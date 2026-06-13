import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config import Config

CONFIDENCE_THRESHOLD = 90

MAPPING_FILE = Config.TEADB_MAPPING_FILE_PATH
from rapidfuzz import process

def fuzzy_find(key, mapping):
    choices = list(mapping["index"].keys())
    match, score, _ = process.extractOne(key, choices)

    if score > CONFIDENCE_THRESHOLD:
        return mapping["index"][match]

    return None

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()


def load_mapping():
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_tea(name, producer="", year="", tea_type=""):
    mapping = load_mapping()

    key = normalize(f"{name} {producer} {year} {tea_type}")

    # Exact match
    if key in mapping["index"]:
        return mapping["index"][key]

    # Fallback: partial match
    fuzzy_result = fuzzy_find(key, mapping)
    if fuzzy_result:
        print(f"Fuzzy matched '{key}' to '{fuzzy_result['name']}'")
        return fuzzy_result
    
    print(f"No match found for '{key}'")
    return None

if __name__ == "__main__":
    # Example usage
    # Intentionally fuzzy search for a tea that doesn't exist to demonstrate fuzzy matching
    tea_info = find_tea("1568", "", "", "black")
    if tea_info:
        print("Found tea:", tea_info)
    else:
        print("Tea not found")