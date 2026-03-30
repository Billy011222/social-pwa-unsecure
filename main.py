import os
import sys
import sqlite3
import subprocess
import secrets
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    abort,
)
from flask_cors import CORS

import user_management as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database_files", "database.db")
SETUP_SCRIPT = os.path.join(BASE_DIR, "database_files", "setup_db.py")


def _tables_exist():
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        tables = {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        con.close()
        return {"users", "posts", "messages"}.issubset(tables)
    except Exception:
        return False


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "database_files"), exist_ok=True)
    if not os.path.exists(DB_PATH) or not _tables_exist():
        print("[SocialPWA] Setting up database...")
        result = subprocess.run(
            [sys.executable, SETUP_SCRIPT],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print("[SocialPWA] WARNING: setup_db failed:", result.stderr)
    else:
        print("[SocialPWA] Database already exists — skipping setup.")


init_db()

app = Flask(__name__)

# Restrict CORS instead of allowing every origin
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5000", "http://localhost:5000"]}})

# Do not hardcode secrets in production
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # set True if using HTTPS
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0,
)


def generate_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(16)
        session["csrf_token"] = token
    return token


def validate_csrf():
    token = request.form.get("csrf_token", "")
    return token and token == session.get("csrf_token")


def is_safe_internal_url(target: str) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == "" and parsed.netloc == "" and target.startswith("/") and not target.startswith("//")


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("home", msg="Please log in first."))
        return view_func(*args, **kwargs)
    return wrapper


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.context_processor
def inject_security_values():
    return {"csrf_token": generate_csrf_token()}


@app.route("/", methods=["GET", "POST"])
@app.route("/index.html", methods=["GET", "POST"])
def home():
    if request.method == "GET" and request.args.get("url"):
        target = request.args.get("url", "")
        if is_safe_internal_url(target):
            return redirect(target, code=302)
        return redirect(url_for("home", msg="Blocked unsafe redirect."))

    if request.method == "GET":
        msg = request.args.get("msg", "")
        return render_template("index.html", msg=msg)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    is_logged_in = db.retrieveUsers(username, password)

    if is_logged_in:
        session["username"] = username
        posts = db.getPosts()
        return render_template("feed.html", username=username, state=True, posts=posts, msg="")
    return render_template("index.html", msg="Invalid credentials. Please try again.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home", msg="Logged out successfully."))


@app.route("/signup.html", methods=["GET", "POST"])
def signup():
    if request.method == "GET" and request.args.get("url"):
        target = request.args.get("url", "")
        if is_safe_internal_url(target):
            return redirect(target, code=302)
        return redirect(url_for("signup"))

    if request.method == "POST":
        if not validate_csrf():
            abort(403)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        dob = request.form.get("dob", "")
        bio = request.form.get("bio", "")

        try:
            db.insertUser(username, password, dob, bio)
            return redirect(url_for("home", msg="Account created! Please log in."))
        except ValueError as e:
            return render_template("signup.html", msg=str(e)), 400

    return render_template("signup.html", msg="")


@app.route("/feed.html", methods=["GET", "POST"])
@login_required
def feed():
    username = session["username"]

    if request.method == "GET" and request.args.get("url"):
        target = request.args.get("url", "")
        if is_safe_internal_url(target):
            return redirect(target, code=302)
        return redirect(url_for("feed"))

    if request.method == "POST":
        if not validate_csrf():
            abort(403)

        post_content = request.form.get("content", "")
        try:
            db.insertPost(username, post_content)
        except ValueError as e:
            posts = db.getPosts()
            return render_template("feed.html", username=username, state=True, posts=posts, msg=str(e)), 400

    posts = db.getPosts()
    return render_template("feed.html", username=username, state=True, posts=posts, msg="")


@app.route("/profile")
@login_required
def profile():
    if request.args.get("url"):
        target = request.args.get("url", "")
        if is_safe_internal_url(target):
            return redirect(target, code=302)
        return redirect(url_for("profile"))

    username = session["username"]
    profile_data = db.getUserProfile(username)
    return render_template("profile.html", profile=profile_data, username=username)


@app.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    username = session["username"]

    if request.method == "POST":
        if not validate_csrf():
            abort(403)

        recipient = request.form.get("recipient", "").strip()
        body = request.form.get("body", "")
        try:
            db.sendMessage(username, recipient, body)
        except ValueError as e:
            msgs = db.getMessages(username)
            return render_template("messages.html", messages=msgs, username=username, recipient=username, msg=str(e)), 400

    msgs = db.getMessages(username)
    return render_template("messages.html", messages=msgs, username=username, recipient=username, msg="")


@app.route("/success.html")
def success():
    msg = request.args.get("msg", "Your action was completed successfully.")
    return render_template("success.html", msg=msg)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
