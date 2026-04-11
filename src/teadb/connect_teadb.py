import requests
import json
from datetime import datetime, timedelta
from config import Config
from models.review import Review
from models.tea import Tea
from .lookup import find_tea

BASE_URL = Config.TEADB_API_BASE_URL
HEADERS = {
    "Authorization": f"Bearer {Config.TEADB_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://my.teadb.org",
    "Referer": "https://my.teadb.org/add-session",
}

# =========================
# API HELPERS
# =========================
def post(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code not in (200, 201):
        print("URL:", url)
        print("Payload:", json.dumps(payload, indent=2))
        print(f"POST {endpoint} failed:", response.status_code)
        print(response.text)
        return None
    else:
        print(f"POST {endpoint} succeeded:", response.status_code)

    return response.json()


def add_custom_tea(
    name,
    tea_type,
    origin="",
    tea_year=None,
    tea_producer="",
    vendor_name="",
    vendor_id=None,
    producer_id=None,
    dry_run=False
):
    url = f"{BASE_URL}/teas/custom"

    # Need to map types from ratea to teadb types. Hong is black
    # The valid types are "raw puerh", "ripe puerh", "green", "black", "oolong", "white", "yellow", "heicha"
    tea_type = tea_type.lower()
    tea_type_mapping = {
        "hong": "black",
        "sheng": "raw puerh",
        "shou": "ripe puerh",
        "liubao": "heicha",
        "fuzhuan": "heicha",
        "raw liubao": "heicha",
        "ripe liubao": "heicha",
    }
    new_tea_type = tea_type_mapping.get(tea_type)



    producer = tea_producer if tea_producer else vendor_name
    vendor = vendor_name if vendor_name else tea_producer
    # According to teadb, vendor should only be provided if producer is not provided. If we set either producer or vendor to 'community',
    # We want to set producer as 'Unknown' and vendor as '' (empty string). Otherwise, we want to unset vendor if we have a producer.
    if producer == "community" or vendor == "community":
        producer = "Unknown"
        vendor = ""

    if producer and vendor:
        vendor = ""  # Unset vendor if we have a producer, to avoid confusion.

    # We auto-set origin based on original tea type.
    originMapping = {
        "hong": "China",
        "sheng": "Yunnan, China",
        "shou": "Yunnan, China",
        "liubao": "Guangxi, China",
        "fuzhuan": "Hunan, China",
        "raw liubao": "Guangxi, China",
        "ripe liubao": "Guangxi, China",
    }
    if not origin and tea_type in originMapping:
        origin = originMapping[tea_type]
    else:
        origin = origin if origin else "China"  # Default to China if not provided
    
    payload = {
        "name": name,
        "type": new_tea_type,
        "origin": origin,
        "tea_year": str(tea_year) if tea_year else None,
        "tea_producer": producer,
        "vendor_name": vendor,
        "vendor_id": vendor_id,
        "producer_id": producer_id
    }
    if dry_run:
        print("Dry run - would add custom tea with payload:")
        print(json.dumps(payload, indent=2))
        return {"status": "dry_run"}

    response = requests.post(url, headers=HEADERS, json=payload)

    print("Status:", response.status_code)

    if response.status_code not in (200, 201):
        print("Failed:", response.text)
        return None

    data = response.json()
    print("Created tea:", data)

    tea_id = data["tea"]["id"]
    vintage_id = data["tea"]["vintage_id"]

    return data, tea_id, vintage_id


# =========================
# CREATE TEA PURCHASE
# =========================
def create_purchase(review):
    payload = {
        "tea_id": review["tea_id"],
        "vintage_id": review["vintage_id"],
        "quantity_grams": review.get("grams", 5),
        "tea_remaining": review.get("grams", 5),
        "cost_amount": review.get("cost", 0),
        "cost_currency": "USD",
        "purchase_date": review.get(
            "purchase_date",
            datetime.now().strftime("%Y-%m-%d")
        ),
        "is_public": True,
        "is_sample": True
    }

    return post("/tea-purchases", payload)


# =========================
# CREATE SESSION (REVIEW)
# =========================
def create_session(review, dry_run=False):
    session_tea_id = review.get("tea_id")
    session_vintage_id = review.get("vintage_id")

    notes = review.get("notes", "")
    tags = review.get("tags", [])

    payload = {
        "tea_id": session_tea_id,
        "vintage_id": session_vintage_id,
        "rating": review["rating"],

    "brewing_parameters": {
        "method": review.get("method", "Gongfu"),
        "method_other": "",
        "vessel_size": review.get("vessel_ml", 100),
        "grams_used": review.get("grams", 5),
            "water_temp_f": review.get("temp_f", 212),
            "steep_time_seconds": review.get("steep_seconds", 15)
        },

        "flavors": review.get("flavors", []),
        "notes": notes,
        "tags": tags,

        "isPublished": True,
        "session_date": review.get(
            "session_date",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),

        "likes_enabled": True,
        "comments_enabled": True
    }

    if dry_run:
        print("Dry run - would create session with payload:")
        print(json.dumps(payload, indent=2))
        return {"status": "dry_run"}

    result = post("/sessions", payload)
    if result:
        print("Session created successfully:", result)

    return result


# =========================
# IMPORT WORKFLOW
# =========================
def import_review(review, create_purchase_first=False, dry_run=False):
    print(f"\nImporting: tea_name={review['tea_name']}")

    if create_purchase_first:
        purchase = create_purchase(review)
        if purchase:
            print("Purchase created")

    session = create_session(review, dry_run=dry_run)
    if session:
        print("Session created")


# =========================
# BULK IMPORT
# =========================
def import_reviews(reviews, dry_run=False):
    for review in reviews:
        import_review(review, dry_run=dry_run)


# =========================
# Ratea <-> Teadb adapter
# =========================

def ratea_review_to_teadb_payload(tea: Tea, review: Review, add_custom_tea_if_not_found=False, dry_run=False):
    tags = []
    tags = review.get("tags", [])
    if "api" not in [t.lower() for t in tags]:
        tags.append("api")

    # Append type in titlecase to tags if not already present
    type_tag = tea.tea_type.title() if tea.tea_type else "Unknown"
    if type_tag not in [t.title() for t in tags]:
        tags.append(type_tag)

    # Append producer in titlecase to tags if not already present
    producer_tag = tea.vendor.title() if tea.vendor else "Unknown"
    if producer_tag not in [t.title() for t in tags]:
        tags.append(producer_tag)

    # Lookup tea_id and vintage_id using tea name, producer, and year. Error if not found.
    tea_id = None
    vintage_id = None
    result = find_tea(tea.name, tea.vendor, tea.year)
    if result:
        tea_id = result["tea_id"]
        vintage_id = result["vintage_id"]
    else:
        print(f"Tea not found in TeaDB: {tea.name} by {tea.vendor} ({tea.year}). Please check manually if exists. (debug) fallback to w2t 2021 hot brandy tea_id and vintage_id for now, but this will need to be fixed for other teas.")
        # Fallback to known tea IDs
        tea_id = 1770  # For w2t 2021 hot brandy
        vintage_id = 31612

        if add_custom_tea_if_not_found:
            print("Adding custom tea...")
            data, tea_id, vintage_id = add_custom_tea(
                name=tea.name,
                tea_type=tea.tea_type,
                tea_year=tea.year,
                tea_producer=tea.vendor,
                vendor_name=tea.vendor,
                origin="",
                dry_run=dry_run
            )
        else:
            print("Not adding custom tea, proceeding with fallback tea_id and vintage_id. This will need to be fixed for accurate data.")

    # notes add to end
    notes = review.get("notes", "")
    notes += f" (Imported via API) teaid: {tea_id}, vintage_id: {vintage_id}" if notes else f"Imported via API (teaid: {tea_id}, vintage_id: {vintage_id})"

    # Teadb has timezone support, ratea does not. We assume user is in US and thus add 8 hours to convert to UTC for session_date. This is a simplification and may need to be improved by allowing user to specify timezone in Tea model and converting accordingly.
    session_date = review.date + timedelta(hours=8) if isinstance(review.date, datetime) else review.date

    # rating needs to be numeric 0-10, instead of 0-5
    payload = [
        {
            "tea_id": tea_id,
            "vintage_id": vintage_id,
            "tea_name": tea.name,
            "tea_producer": tea.vendor,
            "tea_year": tea.year,
            "rating": review.rating * 2,  # Convert 0-5 scale to 0-10
            "notes": review.notes,
            "grams": review.amount_drunk,
            "vessel_ml": review.vesselSize,
            "temp_f": 212,  # Default to boiling if not specified
            "steep_seconds": 15,  # Default to 15 seconds if not specified
            "method": review.method,
            "tags": tags,
            "flavors": [],
            "session_date": session_date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(session_date, datetime) else session_date,
        }
    ]

    return payload

def upload_ratea_review_to_teadb(tea, review, create_purchase_first=False, dry_run=True, add_custom_tea_if_not_found=False):
    print(f"\nUploading review for tea_name={tea.name} to TeaDB...")

    payload = ratea_review_to_teadb_payload(tea, review, add_custom_tea_if_not_found=add_custom_tea_if_not_found, dry_run=dry_run)

    if create_purchase_first:
        purchase = create_purchase(payload[0])
        if purchase:
            print("Purchase created")

    response = create_session(payload[0], dry_run=dry_run)
    if response:
        userid = response.get("session", {}).get("user_id", "unknown")
        tea_id = response.get("session", {}).get("tea_id", "unknown")
        vintage_id = response.get("session", {}).get("vintage_id", "unknown")
        tea_name = response.get("session", {}).get("tea_name", "unknown")
        print(f"Session created for user: {userid}, tea_id: {tea_id}, vintage_id: {vintage_id}, tea_name: {tea_name}")
    else:
        print("Failed to create session.")

def dummy_funct(tea, review):
    payload = ratea_review_to_teadb_payload(tea, review, add_custom_tea_if_not_found=False)
    print("Dummy function - payload prepared:")
    print(json.dumps(payload, indent=2))


# =========================
# EXAMPLE DATA
# =========================
if __name__ == "__main__":
    tea_name = "swerve"
    tea_year = "2023"
    tea_producer = "w2t"
    reviews = [
        {
        "tea_name": tea_name,
        "tea_year": tea_year,
        "tea_producer": tea_producer,
        "rating": 7,
        "notes": "api test 2",
        "grams": 5,
        "vessel_ml": 100,
        "temp_f": 212,
        "steep_seconds": 15,
        "method": "Gongfu",
        "tags": [],
        "flavors": [],
        "session_date": "2026-01-02 12:00:00", # ex: 2026-04-07 21:48:00
        "notes": "This is a test review created via API."
        }
    ]

    import_reviews(reviews, dry_run=False)