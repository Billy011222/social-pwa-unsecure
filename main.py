from flask import Flask, render_template, request, redirect, session
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "supersecretkey"


@app.route("/", methods=["GET", "POST"])
@app.route("/index.html", methods=["GET", "POST"])
def home():

    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url", "")
        url = url.replace("\\", "")

        parsed = urlparse(url)

        if not parsed.netloc and not parsed.scheme and url.startswith("/"):
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


@app.route("/signup.html", methods=["GET", "POST"])
def signup():

    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url", "")
        url = url.replace("\\", "")

        parsed = urlparse(url)

        if not parsed.netloc and not parsed.scheme and url.startswith("/"):
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
        url = request.args.get("url", "")
        url = url.replace("\\", "")

        parsed = urlparse(url)

        if not parsed.netloc and not parsed.scheme and url.startswith("/"):
            return redirect(url)

        return redirect("/feed.html")

    return render_template("feed.html", username=session["username"], posts=[])


@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect("/")

    if request.args.get("url"):
        url = request.args.get("url", "")
        url = url.replace("\\", "")

        parsed = urlparse(url)

        if not parsed.netloc and not parsed.scheme and url.startswith("/"):
            return redirect(url)

        return redirect("/profile")

    return render_template("profile.html", username=session["username"])


@app.route("/messages", methods=["GET", "POST"])
def messages():

    if "username" not in session:
        return redirect("/")

    return render_template("messages.html", username=session["username"], messages=[])


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=False)
