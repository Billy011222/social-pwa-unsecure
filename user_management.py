import os
import re
import sqlite3 as sql
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database_files", "database.db")
LOG_PATH = os.path.join(BASE_DIR, "visitor_log.txt")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _connect():
    con = sql.connect(DB_PATH)
    con.row_factory = sql.Row
    return con


def _valid_username(username: str) -> bool:
    return bool(USERNAME_RE.fullmatch((username or "").strip()))


def _valid_password(password: str) -> bool:
    password = password or ""
    return len(password) >= 8 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)


def _valid_dob(dob: str) -> bool:
    return bool(DATE_RE.fullmatch((dob or "").strip()))


def _clean_text(value: str, max_len: int) -> str:
    return (value or "").strip()[:max_len]


def username_exists(username: str) -> bool:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = cur.fetchone() is not None
    con.close()
    return exists


def get_user_by_username(username: str) -> Optional[sql.Row]:
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "SELECT id, username, dateOfBirth, bio, role FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    con.close()
    return row


def migrate_plaintext_passwords() -> None:
    con = _connect()
    cur = con.cursor()
    rows = cur.execute("SELECT id, password FROM users").fetchall()
    updated = False
    for row in rows:
        password = row["password"]
        if password and not str(password).startswith("scrypt:") and not str(password).startswith("pbkdf2:"):
            cur.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(password), row["id"]),
            )
            updated = True
    if updated:
        con.commit()
    con.close()


def insertUser(username, password, DoB, bio=""):
    username = _clean_text(username, 30)
    bio = _clean_text(bio, 200)
    DoB = _clean_text(DoB, 10)

    if not _valid_username(username):
        raise ValueError("Username must be 3-30 characters and contain only letters, numbers, or underscores.")
    if not _valid_password(password):
        raise ValueError("Password must be at least 8 characters and include both letters and numbers.")
    if not _valid_dob(DoB):
        raise ValueError("Date of birth must use DD/MM/YYYY format.")
    if username_exists(username):
        raise ValueError("That username is already taken.")

    con = _connect()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users (username, password, dateOfBirth, bio) VALUES (?,?,?,?)",
        (username, generate_password_hash(password), DoB, bio),
    )
    con.commit()
    con.close()


def retrieveUsers(username, password):
    username = _clean_text(username, 30)
    password = password or ""

    if not _valid_username(username):
        return False

    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    user_row = cur.fetchone()
    con.close()

    if user_row is None:
        return False

    stored_password = user_row["password"]
    if stored_password.startswith("scrypt:") or stored_password.startswith("pbkdf2:"):
        return check_password_hash(stored_password, password)

    return stored_password == password


def insertPost(author, content):
    author = _clean_text(author, 30)
    content = _clean_text(content, 500)

    if not _valid_username(author):
        raise ValueError("Invalid author.")
    if not content:
        raise ValueError("Post content cannot be empty.")

    con = _connect()
    cur = con.cursor()
    cur.execute("INSERT INTO posts (author, content) VALUES (?, ?)", (author, content))
    con.commit()
    con.close()


def getPosts():
    con = _connect()
    cur = con.cursor()
    data = cur.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    con.close()
    return data


def getUserProfile(username):
    username = _clean_text(username, 30)
    if not _valid_username(username):
        return None
    return get_user_by_username(username)


def getMessages(username):
    username = _clean_text(username, 30)
    if not _valid_username(username):
        return []

    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM messages WHERE recipient = ? ORDER BY id DESC", (username,))
    rows = cur.fetchall()
    con.close()
    return rows


def sendMessage(sender, recipient, body):
    sender = _clean_text(sender, 30)
    recipient = _clean_text(recipient, 30)
    body = _clean_text(body, 1000)

    if not _valid_username(sender) or not _valid_username(recipient):
        raise ValueError("Invalid sender or recipient username.")
    if not username_exists(recipient):
        raise ValueError("Recipient does not exist.")
    if not body:
        raise ValueError("Message body cannot be empty.")

    con = _connect()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO messages (sender, recipient, body) VALUES (?, ?, ?)",
        (sender, recipient, body),
    )
    con.commit()
    con.close()


def getVisitorCount():
    try:
        with open(LOG_PATH, "r") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0
