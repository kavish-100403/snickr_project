"""
routes/auth.py – Registration, login, and logout.

Security notes:
  - Passwords are stored as Werkzeug pbkdf2:sha256 hashes.
  - All SQL uses parameterized queries.
  - Jinja2 auto-escapes all template output, preventing XSS.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, dict_cursor

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("workspaces.dashboard"))
    return redirect(url_for("auth.login"))


# ── Login ────────────────────────────────────────────────────────────────────


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("workspaces.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html", username=username)

        conn = get_connection()
        cur = None
        try:
            cur = dict_cursor(conn)
            cur.execute(
                "SELECT user_id, username, email, nickname, password "
                "FROM Users WHERE username = %s",
                (username,),
            )
            user = cur.fetchone()
        finally:
            if cur:
                cur.close()
            conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["nickname"] = user["nickname"]
            flash(f"Welcome back, {user['nickname'] or user['username']}!", "success")
            return redirect(request.args.get("next") or url_for("workspaces.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


# ── Register ─────────────────────────────────────────────────────────────────


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("workspaces.dashboard"))

    form = {}
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        form = {"email": email, "username": username, "nickname": nickname}

        errors = []
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", **form)

        hashed = generate_password_hash(password)
        conn = get_connection()
        cur = None
        try:
            cur = dict_cursor(conn)

            cur.execute("SELECT 1 FROM Users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("An account with that email already exists.", "danger")
                return render_template("auth/register.html", **form)

            cur.execute("SELECT 1 FROM Users WHERE username = %s", (username,))
            if cur.fetchone():
                flash("That username is already taken.", "danger")
                return render_template("auth/register.html", **form)

            cur.execute(
                "INSERT INTO Users (email, username, nickname, password) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING user_id, username, email, nickname",
                (email, username, nickname or None, hashed),
            )
            new_user = cur.fetchone()
            conn.commit()
        except Exception:
            conn.rollback()
            flash("Registration failed. Please try again.", "danger")
            return render_template("auth/register.html", **form)
        finally:
            if cur:
                cur.close()
            conn.close()

        session.clear()
        session["user_id"] = new_user["user_id"]
        session["username"] = new_user["username"]
        session["email"] = new_user["email"]
        session["nickname"] = new_user["nickname"]
        flash("Account created! Welcome to snickr.", "success")
        return redirect(url_for("workspaces.dashboard"))

    return render_template("auth/register.html", **form)


# ── Logout ───────────────────────────────────────────────────────────────────


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
