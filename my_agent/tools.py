import requests
import json

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
