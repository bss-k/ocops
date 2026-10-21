import os
import sys
import requests
import argparse
import json
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

SAFE_PREFIX = "ocops_"
BASE_URL = "https://apis.roblox.com/datastores/v1/universes"
PROFILES = ("test", "prod")
_active = {}

def load_profile(name):
    prefix = name.upper()
    _active["name"] = prefix
    _active["api_key"] = os.environ[f"{prefix}_API_KEY"]
    _active["universe_id"] = os.environ[f"{prefix}_UNIVERSE_ID"]

def api_request(method, path, params=None, body=None):
    url = f"{BASE_URL}/{_active['universe_id']}/{path}"
    headers = {"x-api-key": _active['api_key']}
    response = requests.request(
        method, url, headers=headers, params=params, json=body, timeout=30
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise SystemExit(f"{e}\n{response.text}") from e
    
    if not response.content:
        return None
    return response.json()

def api_get(path, params=None):
    """Send an authenticated GET to the Open Cloud API and return the parsed JSON."""
    return api_request("GET", path, params)

def set_entry(datastore, key, value):
    return api_request(
        "POST",
        "standard-datastores/datastore/entries/entry",
        {"datastoreName": datastore, "entryKey": key},
        body=value
    )

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

def get_entry(datastore_name, key):
    return api_get(
        "standard-datastores/datastore/entries/entry",
        {"datastoreName": datastore_name, "entryKey": key}, 
    )


def cmd_datastores(args):
    for ds in list_datastores():
        print(ds["name"])

def cmd_keys(args):
    keys = list_keys(args.datastore)
    for entry in keys[: args.limit]:  # slicing with None returns everything
        print(entry["key"])

def cmd_get(args):
    value = get_entry(args.datastore, args.key) 
    print(json.dumps(value, indent=2))

def cmd_set(args):
    if not args.datastore.startswith(SAFE_PREFIX):
        sys.exit(f"Refusing to write: Datastore must start with '{SAFE_PREFIX}'.")
    value = json.loads(args.value)
    if args.dry_run:
        print(f"[dry-run] would set {args.datastore}/{args.key} = {value}")
        return
    result = set_entry(args.datastore, args.key, value)
    print(json.dumps(result, indent=2))
    
def build_parser():
    parser = argparse.ArgumentParser(prog="ocops", description="Roblox Open Cloud ops CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    parser.add_argument("--profile", choices=PROFILES, default="test")

    p = sub.add_parser("datastores", help="list DataStores")
    p.set_defaults(func=cmd_datastores)

    p = sub.add_parser("keys", help="list keys in a DataStore")
    p.add_argument("datastore")
    p.add_argument("--limit", type=int, help="show only the first N keys")
    p.set_defaults(func=cmd_keys)

    p = sub.add_parser("get", help="read one entry")
    p.add_argument("datastore")
    p.add_argument("key")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("set", help="write one entry")
    p.add_argument("datastore")
    p.add_argument("key")
    p.add_argument("value", help="JSON, e.g. '{\"coins\": 100}'")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_set)

    return parser

def main():
    args = build_parser().parse_args()
    load_profile(args.profile)
    print(f"[profile: {args.profile}]", file=sys.stderr)
    args.func(args)

if __name__ == "__main__":
    main()
