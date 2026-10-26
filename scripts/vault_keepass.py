#!/usr/bin/env python3
"""Store and retrieve Vault initialization material directly in KeePass."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pykeepass import PyKeePass


ROOT_TOKEN_TITLE = "Root Token"
UNSEAL_KEY_PREFIX = "Unseal Key "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("check", "store", "verify", "read"))
    parser.add_argument("--database", required=True)
    parser.add_argument("--group", required=True)
    return parser.parse_args()


def open_database(path: str) -> PyKeePass:
    password = os.environ.get("HORUS_KEEPASS_MASTER_PASSWORD")
    if not password:
        raise RuntimeError("KeePass master password is missing")
    database = Path(path).expanduser()
    if not database.is_file():
        raise RuntimeError("KeePass database does not exist")
    return PyKeePass(str(database), password=password)


def ensure_group(database: PyKeePass, path: str):
    group = database.root_group
    for name in (part for part in path.split("/") if part):
        child = next((item for item in group.subgroups if item.name == name), None)
        group = child or database.add_group(group, name)
    return group


def find_group(database: PyKeePass, path: str):
    group = database.root_group
    for name in (part for part in path.split("/") if part):
        group = next((item for item in group.subgroups if item.name == name), None)
        if group is None:
            raise RuntimeError("Vault initialization group is missing in KeePass")
    return group


def find_entry(group, title: str):
    return next((entry for entry in group.entries if entry.title == title), None)


def check(database: PyKeePass, group_path: str) -> None:
    group = ensure_group(database, group_path)
    if find_entry(group, ROOT_TOKEN_TITLE) or any(
        entry.title.startswith(UNSEAL_KEY_PREFIX) for entry in group.entries
    ):
        raise RuntimeError("Vault initialization entries already exist in KeePass")
    database.save()


def store(database: PyKeePass, group_path: str) -> None:
    payload = json.load(sys.stdin)
    root_token = payload.get("root_token")
    keys = payload.get("unseal_keys_b64")
    if not root_token or not isinstance(keys, list) or not keys:
        raise RuntimeError("Vault initialization response is incomplete")

    group = ensure_group(database, group_path)
    if find_entry(group, ROOT_TOKEN_TITLE) or any(
        entry.title.startswith(UNSEAL_KEY_PREFIX) for entry in group.entries
    ):
        raise RuntimeError("Refusing to overwrite Vault initialization entries")

    database.add_entry(group, ROOT_TOKEN_TITLE, "root", root_token)
    for index, key in enumerate(keys, start=1):
        database.add_entry(group, f"{UNSEAL_KEY_PREFIX}{index}", "unseal", key)
    database.save()


def read(database: PyKeePass, group_path: str) -> None:
    group = find_group(database, group_path)
    root_entry = find_entry(group, ROOT_TOKEN_TITLE)
    key_entries = sorted(
        (entry for entry in group.entries if entry.title.startswith(UNSEAL_KEY_PREFIX)),
        key=lambda entry: int(entry.title.removeprefix(UNSEAL_KEY_PREFIX)),
    )
    if root_entry is None or not root_entry.password or not key_entries:
        raise RuntimeError("Vault initialization material is incomplete in KeePass")
    print(json.dumps({
        "root_token": root_entry.password,
        "unseal_keys_b64": [entry.password for entry in key_entries],
    }))


def verify(database: PyKeePass, group_path: str) -> None:
    group = find_group(database, group_path)
    root_entry = find_entry(group, ROOT_TOKEN_TITLE)
    key_entries = [
        entry for entry in group.entries
        if entry.title.startswith(UNSEAL_KEY_PREFIX)
    ]
    if root_entry is None or not root_entry.password:
        raise RuntimeError("Vault Root Token is missing in KeePass")
    if len(key_entries) != 5 or any(not entry.password for entry in key_entries):
        raise RuntimeError("KeePass must contain exactly five non-empty Vault unseal keys")
    print("Vault initialization material is present in KeePass")


def main() -> int:
    args = parse_args()
    database = open_database(args.database)
    if args.action == "check":
        check(database, args.group)
    elif args.action == "store":
        store(database, args.group)
    elif args.action == "verify":
        verify(database, args.group)
    else:
        read(database, args.group)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"KeePass operation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
