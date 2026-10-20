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
    return response.json()

def paginate(path, items_key, params=None):
    params = dict(params or {})
    items = []
    while True:
        data = api_get(path, params)
        items.extend(data[items_key])
        cursor = data.get("nextPageCursor")
        if not cursor:
            return items
        params["cursor"] = cursor


def list_datastores():
    return paginate("standard-datastores", "datastores")

def list_keys(datastore_name):
    return paginate(
        "standard-datastores/datastore/entries",
        "keys",
        {"datastoreName": datastore_name},
    )


if __name__ == "__main__":
    for ds in list_datastores():
        print(ds["name"])
    print("---")
    for entry in list_keys("Data_4"):
        print(entry["key"])