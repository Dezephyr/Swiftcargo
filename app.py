from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory
)
from config import Config
from models import db, Shipment, TrackingEvent
from utils.auth import login_required
from utils.tracking import generate_tracking_id
from utils.uploads import save_video, allowed_video
from utils.mailer import send_tracking_email
from utils.geocode import geocode

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# -------------------- Public --------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/track")
def track():
    query = request.args.get("tracking_id", "").strip()
    if not query:
        flash("Please enter a tracking ID or email.", "error")
        return redirect(url_for("index"))

    shipment = Shipment.query.filter(
        (Shipment.tracking_id == query.upper()) |
        (Shipment.recipient_email == query.lower())
    ).first()

    if not shipment:
        return render_template("track_result.html", shipment=None, query=query)

    return render_template("track_result.html", shipment=shipment, query=query)


# -------------------- Admin: Auth --------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == app.config["ADMIN_PASSWORD"]:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Wrong password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out.", "success")
    return redirect(url_for("admin_login"))


# -------------------- Admin: Dashboard --------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    shipments = Shipment.query.order_by(Shipment.created_at.desc()).all()
    return render_template("admin_dashboard.html", shipments=shipments)


# -------------------- Admin: Create Shipment --------------------

@app.route("/admin/create", methods=["GET", "POST"])
@login_required
def admin_create():
    if request.method == "POST":
        sender_name = request.form.get("sender_name", "").strip()
        recipient_name = request.form.get("recipient_name", "").strip()
        recipient_email = request.form.get("recipient_email", "").strip().lower()
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "Pending").strip()

        # Validate required fields
        if not all([sender_name, recipient_name, recipient_email, origin, destination]):
            flash("All fields marked * are required.", "error")
            return redirect(url_for("admin_create"))

        # Handle video upload
        video = request.files.get("video")
        video_filename = None
        if video and video.filename:
            if not allowed_video(video.filename):
                flash("Video must be mp4, mov, webm, avi, or mkv.", "error")
                return redirect(url_for("admin_create"))
            video_filename = save_video(video, app.config["UPLOAD_FOLDER"])

        # Geocode origin + destination
        origin_lat, origin_lng = geocode(origin)
        destination_lat, destination_lng = geocode(destination)

        if origin_lat is None or destination_lat is None:
            flash("Couldn't locate origin or destination on the map. Shipment created without route markers.", "error")

        # Generate a unique tracking ID
        tracking_id = generate_tracking_id()
        while Shipment.query.filter_by(tracking_id=tracking_id).first():
            tracking_id = generate_tracking_id()

        # Create the shipment
        shipment = Shipment(
            tracking_id=tracking_id,
            sender_name=sender_name,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            origin=origin,
            destination=destination,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            description=description,
            status=status,
            video_filename=video_filename,
        )
        db.session.add(shipment)
        db.session.flush()  # assigns shipment.id without committing yet

        # First tracking event
        db.session.add(TrackingEvent(
            shipment_id=shipment.id,
            status=status,
            location=origin,
            note="Shipment created.",
        ))
        db.session.commit()

        # Send tracking email to recipient
        success, msg = send_tracking_email(
            to_email=recipient_email,
            recipient_name=recipient_name,
            sender_name=sender_name,
            tracking_id=tracking_id,
            origin=origin,
            destination=destination,
        )

        if success:
            flash(f"Shipment created. Tracking ID {tracking_id} emailed to {recipient_email}.", "success")
        else:
            flash(f"Shipment created ({tracking_id}) but email failed: {msg}", "error")

        return redirect(url_for("admin_shipment", shipment_id=shipment.id))

    return render_template("admin_create.html")


# -------------------- Admin: View / Update Shipment --------------------

@app.route("/admin/shipment/<int:shipment_id>")
@login_required
def admin_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    return render_template("admin_shipment.html", shipment=shipment)


@app.route("/admin/shipment/<int:shipment_id>/event", methods=["POST"])
@login_required
def admin_add_event(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)

    status = request.form.get("status", "").strip()
    location = request.form.get("location", "").strip()
    note = request.form.get("note", "").strip()
    lat = request.form.get("lat", "").strip()
    lng = request.form.get("lng", "").strip()

    if not status:
        flash("Status is required.", "error")
        return redirect(url_for("admin_shipment", shipment_id=shipment_id))

    shipment.status = status
    if location:
        shipment.current_location_label = location
    if lat and lng:
        try:
            shipment.current_lat = float(lat)
            shipment.current_lng = float(lng)
        except ValueError:
            flash("Latitude and longitude must be numbers.", "error")

    db.session.add(TrackingEvent(
        shipment_id=shipment.id,
        status=status,
        location=location or shipment.current_location_label,
        note=note,
    ))
    db.session.commit()

    flash("Tracking event added.", "success")
    return redirect(url_for("admin_shipment", shipment_id=shipment_id))


@app.route("/admin/shipment/<int:shipment_id>/resend", methods=["POST"])
@login_required
def admin_resend_email(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)

    success, msg = send_tracking_email(
        to_email=shipment.recipient_email,
        recipient_name=shipment.recipient_name,
        sender_name=shipment.sender_name,
        tracking_id=shipment.tracking_id,
        origin=shipment.origin,
        destination=shipment.destination,
    )

    if success:
        flash(f"Tracking email resent to {shipment.recipient_email}.", "success")
    else:
        flash(f"Email failed: {msg}", "error")

    return redirect(url_for("admin_shipment", shipment_id=shipment_id))


@app.route("/admin/shipment/<int:shipment_id>/delete", methods=["POST"])
@login_required
def admin_delete_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    db.session.delete(shipment)
    db.session.commit()
    flash("Shipment deleted.", "success")
    return redirect(url_for("admin_dashboard"))


# -------------------- Uploads --------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# -------------------- Run --------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database ready →", app.config["SQLALCHEMY_DATABASE_URI"])
    app.run(debug=True)