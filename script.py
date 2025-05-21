import requests
import logging
import json
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load constants from constants.json
def load_constants():
    """Load API credentials and segment details from constants.json"""
    try:
        with open("constants.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.error("Error loading constants.json. Ensure the file exists and is correctly formatted.")
        exit(1)

constants = load_constants()

API_KEY = constants["API_KEY"]
SEGMENT_ID = constants["SEGMENT_ID"]
SEGMENT_NAME = constants["SEGMENT_NAME"]
CACHE_FILE = constants["CACHE_FILE"]

def fetch_profiles():
    """Fetch profiles from a Klaviyo Segment and return a dict of {profile_id: email}"""
    base_url = f"https://a.klaviyo.com/api/segments/{SEGMENT_ID}/profiles"
    headers = {
        "Authorization": f"Klaviyo-API-Key {API_KEY}",
        "accept": "application/vnd.api+json",
        "revision": "2025-01-15"
    }
    profiles = {}
    params = {"page[size]": 100}
    url = base_url

    while url:
        if url == base_url:
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            for p in data.get("data", []):
                profile_id = p["id"]
                email = p["attributes"].get("email", "unknown@example.com")
                profiles[profile_id] = email
            url = data.get("links", {}).get("next")
        else:
            logging.error(f"Failed to fetch profiles: {response.status_code} - {response.text}")
            return {}

    return profiles

def push_event_to_klaviyo(profile_id, event_name, is_joining):
    """Send an event to Klaviyo and update the 'Is in Segment' property."""
    url = "https://a.klaviyo.com/api/events"
    headers = {
        "Authorization": f"Klaviyo-API-Key {API_KEY}",
        "Content-Type": "application/vnd.api+json",
        "accept": "application/vnd.api+json",
        "revision": "2025-01-15"
    }

    patch_properties = {
        "append": {"Is in Segment": [SEGMENT_NAME]} if is_joining else {},
        "unappend": {"Is in Segment": [SEGMENT_NAME]} if not is_joining else {}
    }

    payload = {
        "data": {
            "type": "event",
            "attributes": {
                "properties": {
                    "segment_id": SEGMENT_ID,
                    "segment_name": SEGMENT_NAME,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "metric": {
                    "data": {
                        "type": "metric",
                        "attributes": {
                            "name": event_name
                        }
                    }
                },
                "profile": {
                    "data": {
                        "type": "profile",
                        "id": profile_id,
                        "attributes": {
                            "meta": {
                                "patch_properties": patch_properties
                            }
                        }
                    }
                }
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 202:
            logging.info(f"Event '{event_name}' sent for profile ID {profile_id}")
        else:
            logging.error(f"Failed to send event for {profile_id}: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error sending event for {profile_id}: {e}")

def update_cache(fetched_profiles):
    """Update the local cache with new profiles."""
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {"profiles": [], "last_updated": None}

    cached_ids = set(cache.get("profiles", []))
    fetched_ids = set(fetched_profiles.keys())

    new_profile_ids = list(fetched_ids - cached_ids)
    if new_profile_ids:
        logging.info(f"New profiles added: {new_profile_ids}")
        for profile_id in new_profile_ids:
            push_event_to_klaviyo(profile_id, "Joined Segment", is_joining=True)

        cache["profiles"].extend(new_profile_ids)
        cache["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
        logging.info("Local cache updated.")
    else:
        logging.info("No new profiles to add.")

def remove_stale_profiles(fetched_profiles):
    """Remove profiles from the cache that are no longer in the Klaviyo segment."""
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("Cache file not found or invalid. Skipping stale profile removal.")
        return

    cached_ids = set(cache.get("profiles", []))
    fetched_ids = set(fetched_profiles.keys())

    stale_profile_ids = list(cached_ids - fetched_ids)
    if stale_profile_ids:
        logging.info(f"Stale profiles removed: {stale_profile_ids}")
        for profile_id in stale_profile_ids:
            push_event_to_klaviyo(profile_id, "Left Segment", is_joining=False)

        cache["profiles"] = list(cached_ids - set(stale_profile_ids))
        cache["last_updated"] = datetime.now(timezone.utc).isoformat()

        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
        logging.info("Stale profiles removed and cache updated.")
    else:
        logging.info("No stale profiles to remove.")

def main():
    profiles = fetch_profiles()
    if profiles:
        update_cache(profiles)
        remove_stale_profiles(profiles)
    else:
        logging.warning("No profiles fetched. Exiting script.")

if __name__ == "__main__":
    main()
