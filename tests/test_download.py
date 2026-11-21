import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

import download


class DownloadRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.entry = ("2026-11-21", "https://bing.com/th?id=OHR.Example_UHD.jpg")
        self.destination = self.folder / "2026-11-21_Example_UHD.jpg"
        content = io.BytesIO()
        Image.new("RGB", (16, 16), "blue").save(content, format="JPEG")
        self.jpeg = content.getvalue()

    def test_corrupt_existing_image_is_replaced_in_one_run(self):
        self.destination.write_bytes(b"interrupted download")
        response = SimpleNamespace(status_code=200, content=self.jpeg)

        with patch.object(download.requests, "get", return_value=response):
            status = download.download_single(self.entry, self.folder)

        self.assertEqual(status, "downloaded")
        self.assertEqual(self.destination.read_bytes(), self.jpeg)
        with Image.open(self.destination) as image:
            image.load()

    def test_failed_replacement_is_counted_as_failed(self):
        self.destination.write_bytes(b"interrupted download")
        response = SimpleNamespace(status_code=503, content=b"unavailable")

        with patch.object(download.requests, "get", return_value=response):
            status = download.download_single(self.entry, self.folder)

        self.assertEqual(status, "failed")
        self.assertFalse(self.destination.exists())

    def test_cleanup_permission_error_is_reported_per_file(self):
        self.destination.write_bytes(b"interrupted download")

        with patch.object(Path, "unlink", side_effect=PermissionError("read-only")):
            status = download.download_single(self.entry, self.folder)

        self.assertEqual(status, "failed")
        self.assertEqual(self.destination.read_bytes(), b"interrupted download")

    def test_directory_collision_does_not_stop_batch_or_remove_directory(self):
        self.destination.mkdir()
        (self.destination / "keep.txt").write_text("preserve this file")
        archive = self.folder / "archive.md"
        archive.write_text(
            f"{self.entry[0]} | [collision]({self.entry[1]})\n"
            "2026-11-21 | [valid](https://example.com/valid.jpg)\n"
        )
        response = SimpleNamespace(status_code=200, content=self.jpeg)
        output = io.StringIO()

        with (
            patch.object(download, "WALLPAPER_FILE", archive),
            patch.object(download, "BASE_FOLDER", self.folder),
            patch.object(download.requests, "get", return_value=response),
            contextlib.redirect_stdout(output),
        ):
            download.main()

        self.assertEqual((self.folder / "2026-11-21_valid.jpg").read_bytes(), self.jpeg)
        self.assertEqual(
            (self.destination / "keep.txt").read_text(), "preserve this file"
        )
        self.assertIn("Downloaded:        1", output.getvalue())
        self.assertIn("Failed:            1", output.getvalue())
        self.assertIn("Total processed:   2", output.getvalue())


if __name__ == "__main__":
    unittest.main()
