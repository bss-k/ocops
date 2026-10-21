import os
import sys
import requests
import argparse
import json

from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

SAFE_PREFIX = "ocops_"
AUDIT_FILE = "audit.jsonl"
BASE_URL = "https://apis.roblox.com/datastores/v1/universes"
PROFILES = ("test", "prod")
_active = {}

class ApiError(Exception):
    def __init__(self, status, text):
        super().__init__(f"HTTP {status}: {text}")
        self.status = status

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
    if not response.ok:
        raise ApiError(response.status_code, response.text)
    
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

def delete_entry(datastore_name, key):
    return api_request(
        "DELETE",
        "standard-datastores/datastore/entries/entry",
        {"datastoreName": datastore_name, "entryKey": key},
    )

def require_safe(datastore):
    if not datastore.startswith(SAFE_PREFIX):
        sys.exit(f"Refusing to write: DataStore must start with '{SAFE_PREFIX}'.")

def apply_change(action, datastore, key, new, dry_run):
    """Guard, show diff, dry-run, confirm, write, audit. new=None means delete."""
    require_safe(datastore)
    old = get_entry_or_none(datastore, key)
    if old is None and new is None:
        print("Nothing to do: entry does not exist.")
        return
    print(f"{datastore}/{key}\n  old: {old}\n  new: {new}")
    if dry_run:
        print("[dry-run] nothing written")
        return
    confirm_prod(f"{action} {datastore}/{key}")
    if new is None:
        delete_entry(datastore, key)
    else:
        set_entry(datastore, key, new)
    audit(action, datastore, key, old, new)

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
    apply_change("set", args.datastore, args.key, json.loads(args.value), args.dry_run)


def cmd_delete(args):
    apply_change("delete", args.datastore, args.key, None, args.dry_run)


def cmd_restore(args):
    record = last_audit(args.datastore, args.key)
    if record is None:
        sys.exit("No audit record for that entry.")
    apply_change("restore", args.datastore, args.key, ..., args.dry_run)  # TODO: which field holds the value to put back?


def add_write_args(p):
    p.add_argument("datastore")
    p.add_argument("key")
    p.add_argument("--dry-run", action="store_true")
    

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
    add_write_args(p)
    p.add_argument("value", help="JSON, e.g. '{\"coins\": 100}'")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("delete", help="delete one entry")
    add_write_args(p)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("restore", help="undo the last change to an entry")
    add_write_args(p)
    p.set_defaults(func=cmd_restore)

    return parser

def get_entry_or_none(datastore, key):
    try:
        return get_entry(datastore, key)
    except ApiError as e:
        if e.status == 404:
            return None  # new key, nothing to overwrite
        raise            # any other error is a real problem


def audit(action, datastore, key, old, new):
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "profile": _active["name"],
        "action": action,
        "datastore": datastore,
        "key": key,
        "old": old,
        "new": new,
    }
    with open(AUDIT_FILE, "a") as f:  # TODO: what does mode "a" do?
        f.write(json.dumps(record) + "\n")

def last_audit(datastore, key):
    """Most recent audit record for this entry on the active profile, or None."""
    if not os.path.exists(AUDIT_FILE):
        return None
    match = None
    with open(AUDIT_FILE) as f:
        for line in f:
            record = json.loads(line)
            if (record["datastore"], record["key"], record["profile"]) == (
                datastore, key, _active["name"]
            ):
                match = record  # later lines overwrite earlier ones
    return match

def confirm_prod(summary):
    if _active["name"] != "prod":
        return
    answer = input(f"PROD: {summary}\nType 'prod' to continue: ")
    if answer != "prod":  # TODO: compare against the right string
        sys.exit("Aborted.")

def main():
    args = build_parser().parse_args()
    load_profile(args.profile)
    print(f"[profile: {args.profile}]", file=sys.stderr)
    try:
        args.func(args)
    except ApiError as e:
        sys.exit(str(e))

if __name__ == "__main__":
    main()
    
