import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

API_KEY = os.environ["PLACE_API_KEY"]
UNIVERSE_ID = os.environ["UNIVERSE_ID"]
BASE_URL = "https://apis.roblox.com/datastores/v1/universes"


def list_datastores():
    url = f"{BASE_URL}/{UNIVERSE_ID}/standard-datastores"
    headers = {...}  # TODO: put the API key in the right header
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # raises an error on 4xx/5xx
    return response.json()


if __name__ == "__main__":
    print(list_datastores())