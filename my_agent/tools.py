import requests
import json
import os
import time
from datetime import datetime, timezone

def get_gvb_disruptions():
    """
    Fetches lift and escalator disruption information from the GVB API.
    """
    url = "https://www.gvb.nl/api/gvb-shared-services/travelinformation/api/v1/Disruption/GetConveyanceDisruptions?language=en"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,nl;q=0.8',
        'priority': 'u=1, i',
        'referer': 'https://www.gvb.nl/en/travel-information/conveyances',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        if not response.text:
            return []
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_public_transport_route(origin: str, destination: str, departure_time: str | None = None):
    """
    Fetches public transport route information from Google Maps Directions API.
    Requires GOOGLE_MAPS_API_KEY environment variable to be set.
    departure_time: Optional departure time in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ').
                    If not provided, defaults to current time.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "Google Maps API key not found. Please set the GOOGLE_MAPS_API_KEY environment variable."}

    base_url = "https://maps.googleapis.com/maps/api/directions/json"

    # Convert ISO 8601 string to Unix timestamp if provided
    unix_departure_time = None
    if departure_time:
        try:
            # Handle optional nanoseconds and 'Z' for UTC
            dt_object = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            unix_departure_time = int(dt_object.timestamp())
        except ValueError:
            return {"error": f"Invalid departure_time format. Expected ISO 8601 (e.g., 'YYYY-MM-DDTHH:MM:SSZ'), got {departure_time}"}

    def make_request(time_param=None):
        params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "key": api_key,
        }
        if time_param:
            params["departure_time"] = time_param
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    # First attempt with the specified departure_time
    result = make_request(unix_departure_time)

    if result and result.get("routes"):
        return result
    elif unix_departure_time is not None:
        # If no routes found for specific time, try again without departure_time (defaults to now)
        now_result = make_request()
        if now_result and now_result.get("routes"):
            return {
                "message": f"No public transport routes found for the exact departure time requested. Here are routes departing around the current time:",
                "routes": now_result["routes"]
            }
        else:
            return {"message": f"No public transport routes found for the specified departure time or for the current time."}
    else:
        return {"message": "No public transport routes found."}
