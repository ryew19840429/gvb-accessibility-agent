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

def get_weather_forecast(latitude: float, longitude: float, timestamp: int):
    """
    Fetches weather forecast from OpenWeatherMap for a specific time.
    Requires OPENWEATHER_API_KEY environment variable to be set.
    latitude: Latitude of the location.
    longitude: Longitude of the location.
    timestamp: Unix timestamp for the desired time.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "OpenWeatherMap API key not found. Please set the OPENWEATHER_API_KEY environment variable."}

    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric",  # Or "imperial" for Fahrenheit
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Find the forecast closest to the requested timestamp
        closest_forecast = None
        min_time_diff = float('inf')

        for forecast_item in data.get("list", []):
            forecast_time = forecast_item["dt"]
            time_diff = abs(forecast_time - timestamp)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast_item
        
        return {"forecast": closest_forecast} if closest_forecast else {"error": "No forecast available for the given time."}

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

    warnings = []

    disruptions = get_gvb_disruptions()
    if isinstance(disruptions, list):
        for disruption in disruptions:
            station_name = disruption.get('stationName', '').lower()
            conveyance_type = disruption.get('conveyanceType', '').lower()
            status = disruption.get('status', '').lower()

            if status == 'out_of_order':
                if origin.lower() in station_name:
                    warnings.append(f"Warning: {conveyance_type.capitalize()} at origin station ({station_name}) is out of order.")
                if destination.lower() in station_name:
                    warnings.append(f"Warning: {conveyance_type.capitalize()} at destination station ({station_name}) is out of order.")
    elif isinstance(disruptions, dict) and "error" in disruptions:
        warnings.append(f"Could not retrieve disruption information: {disruptions['error']}")

    if result and result.get("routes"):
        # Extract destination coordinates and arrival time for weather forecast
        route = result["routes"][0]
        last_leg = route["legs"][-1]
        destination_lat = last_leg["end_location"]["lat"]
        destination_lon = last_leg["end_location"]["lng"]
        arrival_time_unix = last_leg["arrival_time"]["value"]

        weather_forecast = get_weather_forecast(destination_lat, destination_lon, arrival_time_unix)

        if isinstance(weather_forecast, dict) and "error" in weather_forecast:
            warnings.append(f"Could not retrieve weather forecast: {weather_forecast['error']}")
        elif isinstance(weather_forecast, dict) and "forecast" in weather_forecast and weather_forecast["forecast"] is not None:
            closest_forecast = weather_forecast["forecast"]
            
            if closest_forecast.get("pop", 0) > 0.5: # pop is probability of precipitation
                warnings.append(f"Weather warning: High chance of rain ({closest_forecast['pop']*100:.0f}%) at destination around arrival time. Consider bringing a raincoat.")

        if warnings:
            result["warnings"] = warnings
        return result
    elif unix_departure_time is not None:
        # If no routes found for specific time, try again without departure_time (defaults to now)
        now_result = make_request()
        if now_result and now_result.get("routes"):
            # Extract destination coordinates and arrival time for weather forecast
            route = now_result["routes"][0]
            last_leg = route["legs"][-1]
            destination_lat = last_leg["end_location"]["lat"]
            destination_lon = last_leg["end_location"]["lng"]
            arrival_time_unix = last_leg["arrival_time"]["value"]

            weather_forecast = get_weather_forecast(destination_lat, destination_lon, arrival_time_unix)

            if isinstance(weather_forecast, dict) and "error" in weather_forecast:
                warnings.append(f"Could not retrieve weather forecast: {weather_forecast['error']}")
            elif isinstance(weather_forecast, dict) and "forecast" in weather_forecast and weather_forecast["forecast"] is not None:
                closest_forecast = weather_forecast["forecast"]
                
                if closest_forecast.get("pop", 0) > 0.5:
                    warnings.append(f"Weather warning: High chance of rain ({closest_forecast['pop']*100:.0f}%) at destination around arrival time. Consider bringing a raincoat.")

            if warnings:
                now_result["warnings"] = warnings
            return {
                "message": f"No public transport routes found for the exact departure time requested. Here are routes departing around the current time:",
                "routes": now_result["routes"]
            }
        else:
            return {"message": f"No public transport routes found for the specified departure time or for the current time."}
    else:
        return {"message": "No public transport routes found."}
