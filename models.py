from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    sender_name = db.Column(db.String(100), nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False, index=True)

    origin = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(150), nullable=False)

    # NEW — coordinates for origin and destination
    origin_lat = db.Column(db.Float, nullable=True)
    origin_lng = db.Column(db.Float, nullable=True)
    destination_lat = db.Column(db.Float, nullable=True)
    destination_lng = db.Column(db.Float, nullable=True)

    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    current_location_label = db.Column(db.String(200), nullable=True)

    status = db.Column(db.String(50), default="Pending", nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_filename = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = db.relationship(
        "TrackingEvent",
        backref="shipment",
        cascade="all, delete-orphan",
        order_by="TrackingEvent.timestamp.desc()",
    )

    def __repr__(self):
        return f"<Shipment {self.tracking_id}>"

class TrackingEvent(db.Model):
    __tablename__ = "tracking_events"

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey("shipments.id"), nullable=False)

    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    note = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)