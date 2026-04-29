"""
utils.py – Shared helpers used across route blueprints.
"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator: redirect to login if the user is not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
