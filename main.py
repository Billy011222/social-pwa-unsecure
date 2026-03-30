import os
import secrets
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)


app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))


def is_safe_url(target):
    if not target:
        return False

    parsed = urlparse(target)

    return (
        parsed.scheme == "" and
        parsed.netloc == "" and
        target.startswith("/") and
        not target.startswith("//")
    )


@app.route("/", methods=["GET", "POST"])
@app.route("/index.html", methods=["GET", "POST"])
def home():


    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url")

        if is_safe_url(url):
            return redirect(url)

        return redirect("/")

    if request.method == "GET":
        msg = request.args.get("msg", "")
        return render_template("index.html", msg=msg)


    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "admin":
        session["username"] = username
        return redirect("/feed.html")

    return render_template("index.html", msg="Invalid credentials")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



@app.route("/signup.html", methods=["GET", "POST"])
def signup():


    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url")

        if is_safe_url(url):
            return redirect(url)

        return redirect("/signup.html")

    if request.method == "POST":
        return redirect("/")

    return render_template("signup.html", msg="")


@app.route("/feed.html", methods=["GET", "POST"])
def feed():

    if "username" not in session:
        return redirect("/")


    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url")

        if is_safe_url(url):
            return redirect(url)

        return redirect("/feed.html")

    return render_template("feed.html", username=session["username"], posts=[])


@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect("/")


    if request.args.get("url"):
        url = request.args.get("url")

        if is_safe_url(url):
            return redirect(url)

        return redirect("/profile")

    return render_template("profile.html", username=session["username"])


@app.route("/messages", methods=["GET", "POST"])
def messages():

    if "username" not in session:
        return redirect("/")

    return render_template("messages.html", username=session["username"], messages=[])


if __name__ == "__main__":
    app.run(debug=False)
