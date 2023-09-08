from flask import Flask, redirect, render_template, request, session
import sqlite3
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime
from os.path import isfile


app = Flask(__name__)


app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.errorhandler(Exception)
def handle_exc(e):
    if not isinstance(e, HTTPException): e = InternalServerError()
    return render_template("error.html", message=e.name, code=e.code)


def custom_exc(error): return render_template("error.html", message=error, code=400)


default_date = "%Y-%m-%d %H:%M:%S"

@app.template_filter("date_format")
def date_format(date_string, d_format="%B %d, %Y"):
    if d_format == "short": d_format = "%d/%m/%Y"
    return datetime.strptime(date_string, default_date).strftime(d_format)


def init_db(name):
    connection = sqlite3.connect(name)
    with open("schema.sql") as f: connection.executescript(f.read())
    connection.commit()
    connection.close()
    

def query_db(query, args=(), one=False):
    database_name = "ideahub.db"
    if not isfile(database_name): init_db(database_name)
    conn = sqlite3.connect(database_name)
    conn.row_factory = lambda cursor, row: {col[0] : row[idx] for idx, col in enumerate(cursor.description)}
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall() if not one else cur.fetchone()
    conn.commit()
    conn.close()
    return rv


def likes_ideas(ideas):
    for idea in ideas:
        if idea["id"] in [row["idea_id"] for row in query_db("SELECT idea_id FROM likes WHERE user_id = ?;", (session.get("user_id", 0), ))]: idea["liked"] = True
    return ideas


def signin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None: return redirect("/signin")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/favicon.ico")
def favicon():
    return "", 200


@app.route("/")
def index():
    ideas = query_db("SELECT ideas.id AS id, username, user_id, idea_name, idea_body, post_date FROM ideas INNER JOIN users ON users.id = ideas.user_id WHERE posted = 1 ORDER BY post_date DESC;")
    return render_template("index.html", ideas=likes_ideas(ideas), search=False)


@app.route("/search")
def search():
    query = "%" + request.args.get("q") + "%"
    ideas = query_db("SELECT ideas.id AS id, username, user_id, idea_name, idea_body, post_date FROM ideas INNER JOIN users ON users.id = ideas.user_id WHERE posted = 1 AND idea_name LIKE ? ORDER BY post_date DESC;", (query, ))
    return render_template("index.html", ideas=likes_ideas(ideas), search=True)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")
        row = query_db("SELECT * FROM users WHERE username = ?;", (username, ), True)
        if not row: return custom_exc("Username is not registered")
        elif not check_password_hash(row["hash"], password): return custom_exc("Incorrect password")
        session["user_id"] = row["id"]
        return redirect("/")
    return render_template("signin.html", verb="in", alt="up")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        session.clear()
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation: return custom_exc("Password not equal to password confirmation")
        elif query_db("SELECT * FROM users WHERE username = ?;", ("username", )): return custom_exc("Username is already in use")
        query_db("INSERT INTO users (username, email, hash) VALUES (?, ?, ?);", (username.capitalize(), email, generate_password_hash(password)))
        row = query_db("SELECT * FROM users WHERE username = ?;", (username, ), True)
        session["user_id"] = row["id"]
        return redirect("/")
    return render_template("signin.html", verb="up", alt="in")


@app.route("/signout")
def signout():
    session.clear()
    return redirect("/")


@app.route("/like")
@signin_required
def like():
    idea_id = request.args.get("id", type = int)
    query_db("INSERT INTO likes (user_id, idea_id) VALUES (?, ?);", (session["user_id"], idea_id))
    return redirect("/")


@app.route("/unlike")
@signin_required
def unlike():
    idea_id = request.args.get("id", type = int)
    query_db("DELETE FROM likes WHERE user_id = ? AND idea_id = ?;", (session["user_id"], idea_id))
    return redirect("/")


@app.route("/create", methods=["GET", "POST"])
@signin_required
def create():
    if request.method == "POST":
        name = request.form.get("idea-name")
        body = request.form.get("idea-body")
        if not name: return custom_exc("Idea Name")
        query_db("INSERT INTO ideas (user_id, idea_name, idea_body) VALUES (?, ?, ?);", (session["user_id"], name.capitalize(), body.capitalize()))
        return redirect("/ideas")
    else: return render_template("create.html")


@app.route("/ideas")
@signin_required
def ideas():
    ideas = query_db("SELECT * FROM ideas WHERE user_id = ? ORDER BY create_date DESC;", (session["user_id"], ))
    return render_template("ideas.html", ideas=ideas)


@app.route("/delete")
@signin_required
def delete():
    idea_id = request.args.get("id", type = int)
    query_db("DELETE FROM ideas WHERE id = ?;", (idea_id, ))
    return redirect("/ideas")


@app.route("/post")
@signin_required
def post():
    idea_id = request.args.get("id", type = int)
    query_db("UPDATE ideas SET posted = 1, post_date = CURRENT_TIMESTAMP WHERE id = ?;", (idea_id, ))
    return redirect("/ideas")


@app.route("/unpost")
@signin_required
def unpost():
    idea_id = request.args.get("id", type = int)
    query_db("UPDATE ideas SET posted = 0, post_date = NULL WHERE id = ?", (idea_id, ))
    return redirect("/ideas")


@app.route("/users")
def users():
    profs = query_db("SELECT id, username, join_date FROM users WHERE id != ?;", (session.get("user_id", 0), ))
    for prof in profs: prof["no_ideas"] = query_db("SELECT COUNT(id) FROM ideas WHERE user_id = ? AND posted = 1;", (prof["id"], ), one=True)["COUNT(id)"]
    follows = [row["follow_id"] for row in query_db("SELECT follow_id FROM follows WHERE user_id = ?;", (session.get("user_id", 0), ))]
    return render_template("users.html", users=profs, follows=follows)


@app.route("/follow")
@signin_required
def follow():
    follow_id = request.args.get("id", type = int)
    query_db("INSERT INTO follows (user_id, follow_id) VALUES (?, ?);", (session["user_id"], follow_id))
    return redirect("/users")


@app.route("/unfollow")
@signin_required
def unfollow():
    follow_id = request.args.get("id", type = int)
    query_db("DELETE FROM follows WHERE user_id = ? AND follow_id = ?;", (session["user_id"], follow_id))
    return redirect("/users")


@app.route("/profile/<prof_id>")
@signin_required
def profile(prof_id):
    profile = query_db("SELECT id, username, join_date FROM users WHERE id = ?;", (prof_id, ), one=True)
    profile["followers"] = query_db("SELECT user_id AS id, username FROM follows INNER JOIN users ON users.id = follows.user_id WHERE follow_id = ?;", (profile["id"], ))
    profile["following"] = query_db("SELECT follow_id AS id, username FROM follows INNER JOIN users ON users.id = follows.follow_id WHERE user_id = ?;", (profile["id"], ))
    profile["ideas"] = query_db("SELECT id, idea_name, idea_body, post_date FROM ideas WHERE posted = 1 AND user_id = ?;", (profile["id"], ))
    profile["likes"] = [row["idea_id"] for row in query_db("SELECT idea_id FROM likes WHERE user_id = ?;", (session.get("user_id", 0), ))]
    return render_template("profile.html", profile=profile)


@app.route("/notifications")
@signin_required
def notifications():
    notifs = query_db("SELECT users.id AS user_id, users.username, ideas.idea_name, likes.like_date FROM users INNER JOIN likes ON likes.user_id = users.id INNER JOIN ideas ON likes.idea_id = ideas.id WHERE posted = 1 AND ideas.user_id = ?;", (session["user_id"], ))
    notifs += query_db("SELECT users.id AS user_id, users.username, follows.follow_date FROM follows INNER JOIN users ON follows.user_id = users.id WHERE follow_id = ?;", (session["user_id"], ))
    notifs.sort(key=lambda notif: datetime.strptime(next(val for key, val in notif.items() if "date" in key), default_date), reverse=True)
    return render_template("notifications.html", notifs=notifs)
