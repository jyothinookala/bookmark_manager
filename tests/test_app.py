import tempfile
import unittest
from pathlib import Path

from app import create_app


class BookmarkManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.sqlite3"
        self.app = create_app(
            {"TESTING": True, "DATABASE": str(database)}
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_bookmark(self, title="Flask guide", url="https://flask.palletsprojects.com/"):
        return self.client.post(
            "/bookmarks",
            data={
                "title": title,
                "url": url,
                "category": "Learning",
                "tag": "python",
            },
            follow_redirects=True,
        )

    def test_create_search_filter_favorite_edit_and_delete(self):
        response = self.add_bookmark()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Flask guide", response.data)

        response = self.client.get("/?query=PALLETS&category=Learning")
        self.assertIn(b"Flask guide", response.data)
        response = self.client.get("/?category=Work")
        self.assertIn(b"No bookmarks found", response.data)

        with self.app.app_context():
            from app import get_database

            bookmark_id = get_database().execute(
                "SELECT id FROM bookmarks"
            ).fetchone()["id"]

        self.client.post(f"/bookmarks/{bookmark_id}/favorite")
        response = self.client.get("/?category=favorites")
        self.assertIn(b"Flask guide", response.data)

        response = self.client.post(
            "/bookmarks",
            data={
                "id": bookmark_id,
                "title": "Updated guide",
                "url": "https://example.com/updated",
                "category": "Work",
                "tag": "",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Updated guide", response.data)
        self.assertIn("★".encode(), response.data)

        self.client.post(f"/bookmarks/{bookmark_id}/delete")
        response = self.client.get("/")
        self.assertIn(b"No bookmarks found", response.data)

    def test_rejects_invalid_bookmark_fields(self):
        response = self.client.post(
            "/bookmarks",
            data={
                "title": "Bad link",
                "url": "javascript:alert(1)",
                "category": "Learning",
                "tag": "",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"URL must start with http:// or https://", response.data)
        self.assertNotIn(b"Bad link</a>", response.data)


if __name__ == "__main__":
    unittest.main()
