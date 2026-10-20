import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

API_KEY = os.environ["PLACE_API_KEY"]
UNIVERSE_ID = os.environ["UNIVERSE_ID"]
BASE_URL = "https://apis.roblox.com/datastores/v1/universes"

def api_get(path, params=None):
    """Send an authenticated GET to the Open Cloud API and return the parsed JSON."""
    url = f"{BASE_URL}/{UNIVERSE_ID}/{path}"
    headers = {"x-api-key": API_KEY}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()  # TODO: return the response body as a dictionary

def list_datastores():
    datastores = []
    cursor = None
    while True:
        params = {"cursor": cursor} if cursor else {}
        data = api_get("standard-datastores", params)
        datastores.extend(data["datastores"])
        cursor = data.get("nextPageCursor")
        if not cursor:
            break
    return datastores


if __name__ == "__main__":
    for ds in list_datastores():
        print(ds["name"])