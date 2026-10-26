#!/usr/bin/env python3
"""Create Jenkins secrets in KeePass when they are absent."""

from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path

from pykeepass import PyKeePass


def split_path(value: str) -> tuple[list[str], str]:
    parts = [part for part in value.split("/") if part]
    if len(parts) < 2:
        raise RuntimeError("KeePass entry requires a group path and title")
    return parts[:-1], parts[-1]


def ensure_entry(database: PyKeePass, path: str, username: str) -> bool:
    groups, title = split_path(path)
    group = database.root_group
    for name in groups:
        child = next((item for item in group.subgroups if item.name == name), None)
        group = child or database.add_group(group, name)
    entry = next((item for item in group.entries if item.title == title), None)
    if entry is None:
        database.add_entry(group, title, username, secrets.token_urlsafe(48))
        return True
    if entry.username != username or not entry.password:
        raise RuntimeError(f"KeePass entry {path} is incomplete or has the wrong username")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("ensure",))
    parser.add_argument("--database", required=True)
    parser.add_argument("--oidc-entry", required=True)
    parser.add_argument("--recovery-entry", required=True)
    args = parser.parse_args()

    password = os.environ.get("HORUS_KEEPASS_MASTER_PASSWORD")
    if not password:
        raise RuntimeError("KeePass master password is missing")
    database_path = Path(args.database).expanduser()
    if not database_path.is_file():
        raise RuntimeError("KeePass database does not exist")

    database = PyKeePass(str(database_path), password=password)
    changed = ensure_entry(database, args.oidc_entry, "jenkins")
    changed |= ensure_entry(database, args.recovery_entry, "jenkins-breakglass")
    if changed:
        database.save()
    print(f"Jenkins KeePass credentials are ready; created={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"KeePass operation failed: {error}", file=os.sys.stderr)
        raise SystemExit(1)
