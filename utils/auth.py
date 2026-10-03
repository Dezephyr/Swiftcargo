from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped