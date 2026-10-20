import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

API_KEY = os.environ["PLACE_API_KEY"]
UNIVERSE_ID = os.environ["UNIVERSE_ID"]
BASE_URL = "https://apis.roblox.com/datastores/v1/universes"


def list_datastores():
    url = f"{BASE_URL}/{UNIVERSE_ID}/standard-datastores"
    headers = {"x-api-key": API_KEY}
    datastores = []
    cursor = None

    while True:
        params = {}
        if cursor:
            params["cursor"] = cursor  # TODO
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        datastores.extend(data["datastores"])  # TODO: add this page's items
        cursor = data.get("nextPageCursor")
        if not cursor:
            break

    return datastores


if __name__ == "__main__":
    for ds in list_datastores():
        print(ds["name"])