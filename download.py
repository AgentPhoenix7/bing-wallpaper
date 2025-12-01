import requests
import re
import os

# Path to the wallpaper list file (IMPORTANT CHANGE)
wallpaper_file_path = 'bing-wallpaper.md'

# Base output folder inside the project
base_folder = os.path.join(os.getcwd(), "Walls")
os.makedirs(base_folder, exist_ok=True)


def download_image(i, url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        # Skip if already exists (optional nice touch)
        if os.path.exists(file_path):
            print(f"⚠️  [{i + 1}]: Already exists, skipping: {file_path}")
            return
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"✅ [{i + 1}]: {file_path}")
    else:
        print(f"❌ [{i + 1}]: Failed to download {url} (status {response.status_code})")


def extract_date_and_urls(file_path):
    """
    Returns a list of tuples: (year, month, url)
    """
    results = []
    date_pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')
    url_pattern = re.compile(r'(https?://[^\s]+?\.(?:jpg|png|jpeg|gif))')

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            date_match = date_pattern.match(line)
            url_match = url_pattern.search(line)

            if date_match and url_match:
                year, month, _ = date_match.groups()
                url = url_match.group(1)
                results.append((year, month, url))

    return results


# Extract date + image URL pairs
wallpaper_entries = extract_date_and_urls(wallpaper_file_path)
print(f"Found {len(wallpaper_entries)} wallpaper entries")

# Download each image into organized folders
for i, (year, month, url) in enumerate(wallpaper_entries):

    # Determine filename
    if "OHR." in url:
        file_name = url.split("OHR.")[1]
    else:
        file_name = url.split("/")[-1]

    # Create year/month folder
    output_folder = os.path.join(base_folder, year, month)
    os.makedirs(output_folder, exist_ok=True)

    # Full file path
    file_path = os.path.join(output_folder, file_name)

    # Download
    download_image(i, url, file_path)
print("All done!")
