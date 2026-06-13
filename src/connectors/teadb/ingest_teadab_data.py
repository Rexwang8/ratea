import json
import re
import os
import sys

import requests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import Config

MAPPING_FILE = Config.TEADB_MAPPING_FILE_PATH
RAW_DATA_FILE = Config.TEADB_RAW_DATA_FILE_PATH
BASE_URL = f"{Config.TEADB_API_BASE_URL}/teas"
TOKEN = Config.TEADB_TOKEN

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://my.teadb.org",
    "Referer": "https://my.teadb.org/add-session",
}


# =========================
# NORMALIZATION
# =========================
def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()


# =========================
# LOAD / SAVE
# =========================
def load_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {"index": {}}
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mapping(mapping):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)


# =========================
# INGEST JSON
# =========================
def ingest_teas(file_path):
    mapping = load_mapping()

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0

    for tea in data.get("teas", []):
        name = tea.get("name", "")
        producer = tea.get("producer", {}).get("name", "")
        year = tea.get("year", "")

        key = normalize(f"{name} {producer} {year}")

        mapping["index"][key] = {
            "tea_id": tea["id"],
            "vintage_id": tea.get("vintage_id"),
            "name": name,
            "producer": producer,
            "year": year,
            "type": tea.get("type", "")
        }

        count += 1

    save_mapping(mapping)
    print(f" Updated mapping with {count} teas")

# =========================
# FETCH FUNCTION
# =========================
def fetch_teas(tea_type):
    if tea_type == "all":
        params = {
            "includeCustom": "true"
        }
    else:
        params = {
            "type": tea_type,
            "includeCustom": "true"
        }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    print("Status:", response.status_code)

    if response.status_code != 200:
        print("Failed:", response.text)
        return None

    return response.json()


# =========================
# SAVE FUNCTION
# =========================
def save_json(data, tea_type):
    # clean filename
    filename = f"{RAW_DATA_FILE}"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {filename}")


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    # First check if we have raw data file and that it is nonempty. If we do, we skip fetching and just ingest from the file. This allows us to fetch once and then iterate on the ingest logic without hitting the API repeatedly.
    if os.path.exists(RAW_DATA_FILE) and os.path.getsize(RAW_DATA_FILE) > 0:
        ingest_teas(RAW_DATA_FILE)
    else:
        # If we don't have a raw data file, fetch from the API and save it for future iterations
        tea_type = ""
        data = fetch_teas(tea_type)
        if data:
            save_json(data, tea_type)
            print("Fetched data from API, now ingesting...")
            ingest_teas(RAW_DATA_FILE)
        else:
            print("No valid raw data file found.")

    print("Done.")