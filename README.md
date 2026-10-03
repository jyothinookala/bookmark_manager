# Python Bookmark Manager

A small Flask and SQLite version of the Java bookmark manager. It runs as a separate project and does not use or modify the Java application's files.

## Features

- Add, edit, and delete bookmarks
- Organize links with categories and optional tags
- Mark and filter favorites
- Search bookmark titles, URLs, categories, and tags
- Store bookmarks in a local SQLite database

## Requirements

- Python 3.9 or newer
- pip

## Run locally

From the `python-bookmark-manager` folder, install the one application dependency and start Flask:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The SQLite database is created automatically in Flask's `instance` folder. Set `BOOKMARK_DATABASE` to use a different database file.

## Run tests

```powershell
python -m unittest discover -s tests
```
