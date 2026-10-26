#!/usr/bin/env python3
"""Create and keep the Jenkins agent SSH key pair in KeePass."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import tempfile
from pathlib import Path

from pykeepass import PyKeePass


def create_account_password_hash() -> str:
    """Create an unknown, valid shadow hash so OpenSSH does not reject a locked account."""
    result = subprocess.run(
        ["openssl", "passwd", "-6", "-stdin"],
        input=secrets.token_urlsafe(48),
        text=True,
        capture_output=True,
        check=True,
    )
    password_hash = result.stdout.strip()
    if not password_hash.startswith("$6$"):
        raise RuntimeError("OpenSSL did not produce a SHA-512 password hash")
    return password_hash


def create_jenkins_ssh_key_pair() -> dict[str, str]:
    """Generate the dedicated Ed25519 key used by the Jenkins SSH launcher."""
    with tempfile.TemporaryDirectory() as directory:
        key_path = Path(directory) / "jenkins_agent_ed25519"
        subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                "horus-jenkins-agent",
                "-f",
                str(key_path),
            ],
            check=True,
        )
        return {
            "private_key": key_path.read_text(encoding="utf-8"),
            "public_key": key_path.with_suffix(".pub").read_text(encoding="utf-8").strip(),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("ensure",))
    parser.add_argument("--database", required=True)
    parser.add_argument("--entry", required=True)
    args = parser.parse_args()

    master = os.environ.get("HORUS_KEEPASS_MASTER_PASSWORD")
    if not master:
        raise RuntimeError("KeePass master password is missing")
    database_path = Path(args.database).expanduser()
    if not database_path.is_file():
        raise RuntimeError("KeePass database does not exist")

    database = PyKeePass(str(database_path), password=master)
    parts = [part for part in args.entry.split("/") if part]
    if len(parts) < 2:
        raise RuntimeError("KeePass entry requires a group path and title")
    group = database.root_group
    for name in parts[:-1]:
        child = next((item for item in group.subgroups if item.name == name), None)
        group = child or database.add_group(group, name)
    entry = next((item for item in group.entries if item.title == parts[-1]), None)

    if entry is not None:
        try:
            payload = json.loads(entry.notes or "")
        except json.JSONDecodeError as error:
            raise RuntimeError("Jenkins agent KeePass notes are not valid JSON") from error
        if entry.username != "jenkins" or not payload.get("private_key") or not payload.get("public_key"):
            raise RuntimeError("Jenkins agent KeePass entry is incomplete")
        changed = False
        if not payload["public_key"].startswith("ssh-ed25519 "):
            payload.update(create_jenkins_ssh_key_pair())
            changed = True
        if not payload.get("account_password_hash"):
            payload["account_password_hash"] = create_account_password_hash()
            changed = True
        if changed:
            entry.notes = json.dumps(payload)
            database.save()
        print(f"Jenkins agent SSH credentials are ready; created={'true' if changed else 'false'}")
        return 0

    payload = create_jenkins_ssh_key_pair()
    payload["account_password_hash"] = create_account_password_hash()
    database.add_entry(group, parts[-1], "jenkins", "managed-in-notes", notes=json.dumps(payload))
    database.save()
    print("Jenkins agent SSH credentials are ready; created=true")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"KeePass operation failed: {error}", file=os.sys.stderr)
        raise SystemExit(1)
