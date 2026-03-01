import sqlite3
import re
from datetime import datetime
from collections import Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATABASE = "first-try.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            handle TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    # Insert sample tweets if table is empty
    count = conn.execute("SELECT COUNT(*) FROM tweets").fetchone()[0]
    if count == 0:
        samples = [
            ("Ada Lovelace", "@ada", "Just finished my first algorithm! #coding #history"),
            ("Alan Turing", "@turing", "Can a machine think? #AI #philosophy"),
            ("Grace Hopper", "@hopper", "Found a real bug in the Mark II today #debugging #coding"),
            ("Linus Torvalds", "@linus", "New kernel release! #linux #opensource #coding"),
            ("Margaret Hamilton", "@hamilton", "Apollo code is in production #NASA #coding #space"),
            ("Tim Berners-Lee", "@timbl", "What if we linked all documents together? #web #internet"),
        ]
        conn.executemany(
            "INSERT INTO tweets (username, handle, content) VALUES (?, ?, ?)",
            samples,
        )
    conn.commit()
    conn.close()


def extract_hashtags(text):
    return re.findall(r"#(\w+)", text)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tweets", methods=["GET"])
def get_tweets():
    conn = get_db()
    tweets = conn.execute(
        "SELECT * FROM tweets ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify(
        [
            {
                "id": t["id"],
                "username": t["username"],
                "handle": t["handle"],
                "content": t["content"],
                "created_at": t["created_at"],
            }
            for t in tweets
        ]
    )


@app.route("/api/tweets", methods=["POST"])
def post_tweet():
    data = request.get_json()
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Tweet cannot be empty"}), 400
    if len(content) > 280:
        return jsonify({"error": "Tweet exceeds 280 characters"}), 400

    account = request.cookies.get("account", "You")
    handle = f"@{account}" if account != "You" else "@me"

    conn = get_db()
    conn.execute(
        "INSERT INTO tweets (username, handle, content) VALUES (?, ?, ?)",
        (account, handle, content),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201


@app.route("/api/trending")
def trending():
    conn = get_db()
    tweets = conn.execute("SELECT content FROM tweets").fetchall()
    conn.close()

    hashtag_counter = Counter()
    for tweet in tweets:
        for tag in extract_hashtags(tweet["content"]):
            hashtag_counter[tag.lower()] += 1

    top = hashtag_counter.most_common(10)
    return jsonify([{"tag": tag, "count": count} for tag, count in top])


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5010)
