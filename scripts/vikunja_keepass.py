#!/usr/bin/env python3
"""Create Vikunja credentials in KeePass when they are absent."""

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
    parser.add_argument("--oidc-entry", required=True)
    parser.add_argument("--application-entry", required=True)
    return parser.parse_args()


def open_database(path: str) -> PyKeePass:
    password = os.environ.get("HORUS_KEEPASS_MASTER_PASSWORD")
    if not password:
        raise RuntimeError("KeePass master password is missing")
    database = Path(path).expanduser()
    if not database.is_file():
        raise RuntimeError("KeePass database does not exist")
    return PyKeePass(str(database), password=password)


def split_entry_path(path: str) -> tuple[list[str], str]:
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise RuntimeError("Vikunja KeePass entries require a group path and title")
    return parts[:-1], parts[-1]


def ensure_group(database: PyKeePass, names: list[str]):
    group = database.root_group
    for name in names:
        child = next((item for item in group.subgroups if item.name == name), None)
        group = child or database.add_group(group, name)
    return group


def find_entry(database: PyKeePass, path: str):
    group_names, title = split_entry_path(path)
    group = database.root_group
    for name in group_names:
        group = next((item for item in group.subgroups if item.name == name), None)
        if group is None:
            return None
    return next((item for item in group.entries if item.title == title), None)


def ensure_entry(database: PyKeePass, path: str, username: str) -> bool:
    entry = find_entry(database, path)
    if entry is not None:
        if entry.username != username or not entry.password:
            raise RuntimeError(f"KeePass entry {path} is incomplete")
        return False
    group_names, title = split_entry_path(path)
    database.add_entry(
        ensure_group(database, group_names),
        title,
        username,
        secrets.token_urlsafe(48),
    )
    return True


def main() -> int:
    args = parse_args()
    database = open_database(args.database)
    expected = (
        (args.postgres_entry, "vikunja"),
        (args.oidc_entry, "vikunja"),
        (args.application_entry, "vikunja"),
    )
    if args.action == "ensure":
        changed = False
        for path, username in expected:
            changed |= ensure_entry(database, path, username)
        if changed:
            database.save()
        print(f"Vikunja KeePass credentials are ready; created={str(changed).lower()}")
    else:
        for path, username in expected:
            entry = find_entry(database, path)
            if entry is None or entry.username != username or not entry.password:
                raise RuntimeError(f"KeePass entry {path} is missing or incomplete")
        print("Vikunja KeePass credentials are present")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"KeePass operation failed: {error}", file=os.sys.stderr)
        raise SystemExit(1)
