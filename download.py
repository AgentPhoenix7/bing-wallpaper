import requests
import re
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

# Path to the wallpaper list file
wallpaper_file_path = 'bing-wallpaper.md'

# Output folder — all images in ONE place
base_folder = os.path.join(os.getcwd(), "Bing")
os.makedirs(base_folder, exist_ok=True)

# Statistics
skipped_count = 0
downloaded_count = 0
removed_corrupted_count = 0


def is_image_corrupted(file_path):
    """Return True if image is corrupted or unreadable."""
    if not os.path.exists(file_path):
        return True

    try:
        with Image.open(file_path) as img:
            img.verify()
        return False
    except Exception:
        return True


def download_single(entry):
    global skipped_count, downloaded_count, removed_corrupted_count

    i, (date_str, url) = entry  # date_str = YYYY-MM-DD

    # Determine original filename from URL
    if "OHR." in url:
        orig_name = url.split("OHR.")[1]
    else:
        orig_name = url.split("/")[-1]

    # New filename: "2025-12-01_OHR.xyz.jpg"
    file_name = f"{date_str}_{orig_name}"

    file_path = os.path.join(base_folder, file_name)

    # Skip if exists and valid
    if os.path.exists(file_path):
        if is_image_corrupted(file_path):
            os.remove(file_path)
            removed_corrupted_count += 1
        else:
            skipped_count += 1
            return

    # Download the file
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Validate
            if is_image_corrupted(file_path):
                os.remove(file_path)
                removed_corrupted_count += 1
            else:
                downloaded_count += 1
        else:
            print(f"❌ Failed {url} ({response.status_code})")

    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")


def extract_date_and_urls(file_path):
    """Returns list: (YYYY-MM-DD, url)."""
    results = []
    date_pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')
    url_pattern = re.compile(r'(https?://[^\s]+?\.(?:jpg|png|jpeg|gif))')

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            date_match = date_pattern.match(line)
            url_match = url_pattern.search(line)

            if date_match and url_match:
                yyyy, mm, dd = date_match.groups()
                url = url_match.group(1)
                date_str = f"{yyyy}-{mm}-{dd}"
                results.append((date_str, url))

    return results


# Extract pairs
wallpaper_entries = extract_date_and_urls(wallpaper_file_path)
print(f"Found {len(wallpaper_entries)} wallpaper entries.")

indexed_entries = [(i, entry) for i, entry in enumerate(wallpaper_entries)]

# Threaded downloader with progress bar
with Progress(
    TextColumn("[bold blue]Downloading Wallpapers[/]"),
    BarColumn(),
    TextColumn("{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    TimeRemainingColumn(),
) as progress:

    task = progress.add_task("download", total=len(indexed_entries))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_single, e): e for e in indexed_entries}

        for _ in as_completed(futures):
            progress.advance(task)

# Summary
print("\n📊 Summary")
print(f"   ✔ Downloaded:        {downloaded_count}")
print(f"   ⏭️ Skipped:           {skipped_count}")
print(f"   🧹 Removed corrupted: {removed_corrupted_count}")
print(f"   📁 Total processed:   {len(indexed_entries)}")
print("\n✅ All done!")
