#!/usr/bin/env python3
"""Create Access bootstrap credentials in KeePass when they are absent."""

from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path

from pykeepass import PyKeePass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("ensure", "verify"))
    parser.add_argument("--database", required=True)
    parser.add_argument("--postgres-entry", required=True)
    parser.add_argument("--bootstrap-entry", required=True)
    parser.add_argument("--personal-entry", required=True)
    parser.add_argument("--postgres-user", required=True)
    parser.add_argument("--bootstrap-user", required=True)
    parser.add_argument("--personal-user", required=True)
    return parser.parse_args()


def open_database(path: str) -> PyKeePass:
    password = os.environ.get("HORUS_KEEPASS_MASTER_PASSWORD")
    if not password:
        raise RuntimeError("KeePass master password is missing")
    database = Path(path).expanduser()
    if not database.is_file():
        raise RuntimeError("KeePass database does not exist")
    return PyKeePass(str(database), password=password)


def ensure_group(database: PyKeePass, names: list[str]):
    group = database.root_group
    for name in names:
        child = next((item for item in group.subgroups if item.name == name), None)
        group = child or database.add_group(group, name)
    return group


def find_group(database: PyKeePass, names: list[str]):
    group = database.root_group
    for name in names:
        group = next((item for item in group.subgroups if item.name == name), None)
        if group is None:
            return None
    return group


def split_entry_path(path: str) -> tuple[list[str], str]:
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise RuntimeError("Access KeePass entries require a group path and title")
    return parts[:-1], parts[-1]


def require_complete_entry(group, title: str, expected_username: str):
    if group is None:
        raise RuntimeError(f"KeePass group for {title} is missing")
    entry = next((item for item in group.entries if item.title == title), None)
    if entry is None or entry.username != expected_username or not entry.password:
        raise RuntimeError(f"KeePass entry {title} is missing or incomplete")
    return entry


def ensure_entry(database, path: str, username: str) -> bool:
    group_names, title = split_entry_path(path)
    group = ensure_group(database, group_names)
    entry = next((item for item in group.entries if item.title == title), None)
    if entry is None:
        database.add_entry(group, title, username, secrets.token_urlsafe(36))
        return True
    require_complete_entry(group, title, username)
    return False


def verify_entry(database, path: str, username: str) -> None:
    group_names, title = split_entry_path(path)
    require_complete_entry(find_group(database, group_names), title, username)


def main() -> int:
    args = parse_args()
    database = open_database(args.database)
    if args.action == "ensure":
        changed = ensure_entry(database, args.postgres_entry, args.postgres_user)
        changed |= ensure_entry(database, args.bootstrap_entry, args.bootstrap_user)
        changed |= ensure_entry(database, args.personal_entry, args.personal_user)
        if changed:
            database.save()
        print(f"Access KeePass credentials are ready; created={str(changed).lower()}")
    else:
        verify_entry(database, args.postgres_entry, args.postgres_user)
        verify_entry(database, args.bootstrap_entry, args.bootstrap_user)
        verify_entry(database, args.personal_entry, args.personal_user)
        print("Access KeePass credentials are present")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"KeePass operation failed: {error}", file=os.sys.stderr)
        raise SystemExit(1)
