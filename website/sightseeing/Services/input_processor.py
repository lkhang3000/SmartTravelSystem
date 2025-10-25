"""
input_processor.py
-------------------
This module handles user input from the website frontend.
It processes and validates data, then saves it to a JSON file in the backend.
Structure:
    Input Form (Frontend) → API → Input Processor → JSON File (Backend)
"""

import json
import os
from datetime import datetime


# ==============================
# 🧠 Helper: Validation & Processing
# ==============================
def process_user_input(data: dict) -> dict:
    """
    Process and validate the user input data before saving.

    Args:
        data (dict): Raw data received from frontend (via API).

    Returns:
        dict: Cleaned and structured user data.
    """

    # Default fields to prevent missing keys
    user_info = {
        "username": data.get("username", "unknown_user"),
        "gender": data.get("gender", "unspecified"),
        "age": data.get("age", None),
        "language": data.get("language", "Vietnamese"),
    }

    trip_preferences = {
        "tags": data.get("tags", []),
        "location_size_preference": data.get("location_size_preference", []),
        "budget": data.get("budget", 0),
        "group_size": data.get("group_size", 1),
        "domestic_or_international": data.get("domestic_or_international", {}),
        "other_requirements": data.get("other_requirements", ""),
    }

    travel_period = data.get("travel_period", {})
    transportation = data.get("transportation", {})
    geolocation = data.get("geolocation", {})

    processed = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_info": user_info,
        "trip_preferences": trip_preferences,
        "travel_period": travel_period,
        "transportation": transportation,
        "geolocation": geolocation
    }

    return processed


# ==============================
# 💾 Save to JSON file
# ==============================
def save_user_data_to_json(processed_data: dict, file_path: str = "user_data.json"):
    """
    Save processed user data into a JSON file.

    Args:
        processed_data (dict): Validated data returned by process_user_input()
        file_path (str): Path to the JSON file to store all users' data
    """

    # If the file doesn't exist, create an empty structure
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"users": []}, f, ensure_ascii=False, indent=4)

    # Load existing data
    with open(file_path, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)

    # Append the new user entry
    existing_data["users"].append(processed_data)

    # Write back to the JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)


# ==============================
# 🧩 Integration Example (to plug into your API later)
# ==============================
def handle_frontend_input(raw_data: dict):
    """
    Main function to be called by the backend API route.
    Example usage in your API:
        handle_frontend_input(request.json)
    """
    processed = process_user_input(raw_data)
    save_user_data_to_json(processed)
    return {"status": "success", "message": "User data saved successfully."}