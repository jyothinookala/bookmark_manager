# Python Bookmark Manager

A small bookmark manager built with Python, Flask, and SQLite.

## Features

- Add, edit, and delete bookmarks
- Search bookmarks and filter by category
- Mark and view favorite bookmarks
- Add an optional tag to each bookmark

## Run locally

Requires Python 3.9 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The SQLite database is created automatically in the `instance` folder. Set `BOOKMARK_DATABASE` to use another database file.

## Run tests

```powershell
python -m unittest discover -s tests -v
```
