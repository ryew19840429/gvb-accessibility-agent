import requests
import json
import os

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

def get_public_transport_route(origin: str, destination: str):
    """
    Fetches public transport route information from Google Maps Directions API.
    Requires GOOGLE_MAPS_API_KEY environment variable to be set.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "Google Maps API key not found. Please set the GOOGLE_MAPS_API_KEY environment variable."}

    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": "transit",
        "key": api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
