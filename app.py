import os
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, current_app, g, redirect, render_template, request, url_for

CATEGORIES = ("Work", "Learning", "Inspiration", "Other")
FILTER_OPTIONS = (("all", "All bookmarks"), ("favorites", "Favorites")) + tuple(
    (category, category) for category in CATEGORIES
)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "BOOKMARK_DATABASE",
            str(Path(app.instance_path) / "bookmarks.sqlite3"),
        )
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    initialize_database(app)

    @app.teardown_appcontext
    def close_database(_error=None):
        database = g.pop("database", None)
        if database is not None:
            database.close()

    @app.get("/")
    def home():
        query = request.args.get("query", "")
        category = request.args.get("category", "all")
        edit_id = request.args.get("edit", type=int)
        bookmark = get_bookmark(edit_id) if edit_id is not None else None
        editing = bookmark is not None
        if not editing:
            bookmark = {"title": "", "url": "", "category": "Work", "tag": ""}

        search = query.casefold()
        bookmarks = get_database().execute(
            "SELECT * FROM bookmarks ORDER BY id DESC"
        ).fetchall()
        bookmarks = [
            item
            for item in bookmarks
            if (
                category == "all"
                or (category == "favorites" and item["favorite"])
                or category == item["category"]
            )
            and search
            in " ".join(
                (
                    item["title"],
                    item["url"],
                    item["category"],
                    item["tag"] or "",
                )
            ).casefold()
        ]
        return render_template(
            "index.html",
            bookmarks=bookmarks,
            bookmark=bookmark,
            editing=editing,
            form_open=editing,
            query=query,
            selected_category=category,
            errors=[],
            categories=CATEGORIES,
            filter_options=FILTER_OPTIONS,
        )

    @app.post("/bookmarks")
    def save_bookmark():
        bookmark_id = request.form.get("id", type=int)
        fields = {
            "title": request.form.get("title", "").strip(),
            "url": request.form.get("url", "").strip(),
            "category": request.form.get("category", "").strip(),
            "tag": request.form.get("tag", "").strip(),
        }
        errors = validate_bookmark(fields)
        if errors:
            bookmarks = get_database().execute(
                "SELECT * FROM bookmarks ORDER BY id DESC"
            ).fetchall()
            return (
                render_template(
                    "index.html",
                    bookmarks=bookmarks,
                    bookmark={"id": bookmark_id, **fields},
                    editing=bookmark_id is not None,
                    form_open=True,
                    query="",
                    selected_category="all",
                    errors=errors,
                    categories=CATEGORIES,
                    filter_options=FILTER_OPTIONS,
                ),
                400,
            )

        database = get_database()
        if bookmark_id is None:
            database.execute(
                "INSERT INTO bookmarks (title, url, category, tag) "
                "VALUES (?, ?, ?, ?)",
                (fields["title"], fields["url"], fields["category"], fields["tag"] or None),
            )
        else:
            cursor = database.execute(
                "UPDATE bookmarks SET title = ?, url = ?, category = ?, tag = ? "
                "WHERE id = ?",
                (
                    fields["title"],
                    fields["url"],
                    fields["category"],
                    fields["tag"] or None,
                    bookmark_id,
                ),
            )
            if cursor.rowcount == 0:
                database.rollback()
                return redirect(url_for("home"))
        database.commit()
        return redirect(url_for("home"))

    @app.post("/bookmarks/<int:bookmark_id>/favorite")
    def toggle_favorite(bookmark_id):
        database = get_database()
        database.execute(
            "UPDATE bookmarks SET favorite = 1 - favorite WHERE id = ?",
            (bookmark_id,),
        )
        database.commit()
        return redirect(url_for("home"))

    @app.post("/bookmarks/<int:bookmark_id>/delete")
    def delete_bookmark(bookmark_id):
        database = get_database()
        database.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        database.commit()
        return redirect(url_for("home"))

    return app


def get_database():
    if "database" not in g:
        g.database = sqlite3.connect(current_app.config["DATABASE"])
        g.database.row_factory = sqlite3.Row
    return g.database


def get_bookmark(bookmark_id):
    return get_database().execute(
        "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()


def initialize_database(app):
    with app.app_context():
        database = sqlite3.connect(app.config["DATABASE"])
        try:
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tag TEXT,
                    favorite INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            database.commit()
        finally:
            database.close()


def validate_bookmark(fields):
    errors = []
    if not fields["title"]:
        errors.append("Title is required.")
    elif len(fields["title"]) > 100:
        errors.append("Title must be 100 characters or fewer.")

    url = fields["url"]
    if not url:
        errors.append("Link is required.")
    elif len(url) > 2048:
        errors.append("Link must be 2048 characters or fewer.")
    else:
        try:
            parsed_url = urlsplit(url)
            hostname = parsed_url.hostname
        except ValueError:
            parsed_url = None
            hostname = None

        if (
            parsed_url is None
            or parsed_url.scheme not in ("http", "https")
            or not hostname
            or any(character.isspace() for character in url)
        ):
            errors.append("URL must start with http:// or https:// and include a valid host.")

    if not fields["category"]:
        errors.append("Category is required.")
    elif len(fields["category"]) > 30:
        errors.append("Category must be 30 characters or fewer.")
    elif fields["category"] not in CATEGORIES:
        errors.append("Choose a valid category.")

    if len(fields["tag"]) > 30:
        errors.append("Tag must be 30 characters or fewer.")
    return errors


if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG") == "1")
