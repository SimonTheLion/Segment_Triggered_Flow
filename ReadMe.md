# Klaviyo Segment Sync Script

## Overview

This script fetches the members of a specific segment from Klaviyo and maintains a local cache file to track changes. When new profiles are added to the segment or removed from it, an event is recorded on the profile's timeline in Klaviyo.

## Features

- Fetches profiles from a specified Klaviyo segment.
- Maintains a local cache of segment members.
- Sends an event to Klaviyo when a profile joins or leaves the segment.
- Stores API credentials and segment details in a separate constants file for security.
- Uses logging to track script execution and errors.

## Requirements

- Python 3.x
- `requests` module (installed within a virtual environment)
- A Klaviyo API Key with the necessary permissions. (profiles\:read, segments\:read, events\:write)

## Setup

### 1. Create a Virtual Environment (Recommended)

To avoid conflicts with system packages, create and activate a virtual environment:

```sh
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

Once inside the virtual environment, install the required dependencies:

```sh
pip install requests
```

### 3. Create a `constants.json` File

For security, API credentials and other constants are stored in `constants.json`. This file should be placed in the same directory as the script with the following content:

```json
{
  "API_KEY": "your_klaviyo_api_key",
  "SEGMENT_ID": "your_segment_id",
  "SEGMENT_NAME": "your_segment_name",
  "CACHE_FILE": "cache.json"
}
```

Replace the placeholders with your actual Klaviyo credentials.

### 4. Running the Script

Execute the script using:

```sh
python script.py
```

## How It Works

1. **Fetching Profiles**

   - The script calls Klaviyo's API to retrieve members of the specified segment.
   - Profiles are fetched in batches of 100 (or as set in the script) until all profiles are retrieved.

2. **Updating the Cache**

   - If new profiles are found that are not in the cache, they are added, and an event is pushed to Klaviyo indicating they "Joined Segment."
   - The cache file is updated with the new profiles and a timestamp.

3. **Removing Stale Profiles**

   - If a profile is found in the cache but no longer in the segment, it is removed, and an event is pushed to Klaviyo indicating they "Left Segment."
   - The cache file is updated accordingly.

4. **Logging**

   - The script logs successful operations and errors to help with debugging.

## Error Handling

- If the `constants.json` file is missing or incorrectly formatted, an error is logged, and the script exits.
- If the API request fails, an error message is logged with the status code and response text.
- If the cache file is missing or corrupted, a new one is created.

## Customization

- Modify the `page[size]` parameter in `fetch_profiles()` to adjust the number of profiles fetched per request.
- Change the event names in `push_event_to_klaviyo()` if you want different event labels in Klaviyo.
- Adjust logging levels in `logging.basicConfig()` for more or less verbosity.

## Troubleshooting

- **Error: "Failed to fetch profiles"**

  - Check that your `API_KEY` and `SEGMENT_ID` are correct.
  - Ensure your API Key has the necessary permissions.

- **Profiles not updating correctly**

  - Verify that `cache.json` exists and is formatted correctly.
  - Run the script with logging enabled to check for errors.

## License

This script is provided as-is with no warranty. Use it at your own risk.