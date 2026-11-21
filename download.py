import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

WALLPAPER_FILE = Path("bing-wallpaper.md")
BASE_FOLDER = Path("Bing")

DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
URL_PATTERN = re.compile(r"(https?://[^\s]+?\.(?:jpg|png|jpeg|gif))")


def is_image_corrupted(file_path: Path) -> bool:
    """Return True if image is corrupted or unreadable."""
    if not file_path.is_file():
        return True

    try:
        with Image.open(file_path) as img:
            img.verify()
        return False
    except (OSError, SyntaxError, ValueError):
        return True


def download_single(entry: tuple[str, str], folder: Path) -> str:
    """Download a single wallpaper entry. Returns status string."""
    date_str, url = entry

    # Determine original filename from URL
    if "OHR." in url:
        orig_name = url.split("OHR.")[1]
    else:
        orig_name = url.rsplit("/", 1)[-1]

    file_path = folder / f"{date_str}_{orig_name}"

    try:
        # Repair existing corrupt files in this run; report cleanup errors per file.
        if file_path.exists():
            if not is_image_corrupted(file_path):
                return "skipped"
            file_path.unlink(missing_ok=True)

        # Download the file
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            file_path.write_bytes(response.content)

            # Validate downloaded image
            if is_image_corrupted(file_path):
                file_path.unlink(missing_ok=True)
                return "removed_corrupted"
            return "downloaded"

        print(f"❌ Failed {url} ({response.status_code})")
        return "failed"
    except (requests.RequestException, OSError) as e:
        print(f"⚠️ Error downloading {url}: {e}")
        return "failed"


def extract_date_and_urls(file_path: Path) -> list[tuple[str, str]]:
    """Returns list: [(YYYY-MM-DD, url), ...]."""
    if not file_path.is_file():
        return []

    results = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        date_match = DATE_PATTERN.match(line)
        url_match = URL_PATTERN.search(line)

        if date_match and url_match:
            yyyy, mm, dd = date_match.groups()
            results.append((f"{yyyy}-{mm}-{dd}", url_match.group(1)))

    return results


def main() -> None:
    BASE_FOLDER.mkdir(exist_ok=True)

    wallpaper_entries = extract_date_and_urls(WALLPAPER_FILE)
    print(f"Found {len(wallpaper_entries)} wallpaper entries.")

    counts = {
        "downloaded": 0,
        "skipped": 0,
        "removed_corrupted": 0,
        "failed": 0,
    }

    with Progress(
        TextColumn("[bold blue]Downloading Wallpapers[/]"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("download", total=len(wallpaper_entries))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(download_single, entry, BASE_FOLDER): entry
                for entry in wallpaper_entries
            }

            for future in as_completed(futures):
                status = future.result()
                counts[status] = counts.get(status, 0) + 1
                progress.advance(task)

    print("\n📊 Summary")
    print(f"   ✔ Downloaded:        {counts['downloaded']}")
    print(f"   ⏭️ Skipped:           {counts['skipped']}")
    print(f"   🧹 Removed corrupted: {counts['removed_corrupted']}")
    if counts["failed"] > 0:
        print(f"   ❌ Failed:            {counts['failed']}")
    print(f"   📁 Total processed:   {len(wallpaper_entries)}")
    print("\n✅ All done!")


if __name__ == "__main__":
    main()
