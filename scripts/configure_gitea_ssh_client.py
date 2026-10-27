#!/usr/bin/env python3
"""Idempotently manage one exact Host block in an OpenSSH client config."""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import tempfile


BEGIN = "# BEGIN HORUS GITEA MANAGED BLOCK"
END = "# END HORUS GITEA MANAGED BLOCK"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--identity-file", required=True)
    return parser.parse_args()


def remove_managed_block(lines: list[str]) -> list[str]:
    result: list[str] = []
    inside = False
    for line in lines:
        marker = line.strip()
        if marker == BEGIN:
            inside = True
            continue
        if marker == END:
            inside = False
            continue
        if not inside:
            result.append(line)
    if inside:
        raise RuntimeError("unterminated managed Gitea SSH block")
    return result


def remove_exact_host_block(lines: list[str], host: str) -> list[str]:
    result: list[str] = []
    index = 0
    header = re.compile(r"^\s*(Host|Match)\s+(.+?)\s*$", re.IGNORECASE)
    while index < len(lines):
        match = header.match(lines[index])
        if not match or match.group(1).lower() != "host":
            result.append(lines[index])
            index += 1
            continue

        end = index + 1
        while end < len(lines) and not header.match(lines[end]):
            end += 1
        patterns = match.group(2).split()
        if host in patterns and patterns != [host]:
            raise RuntimeError(
                f"refusing to rewrite multi-host block containing {host}: {patterns}"
            )
        if patterns != [host]:
            result.extend(lines[index:end])
        index = end
    return result


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("SSH port must be between 1 and 65535")

    config = pathlib.Path(args.config).expanduser()
    config.parent.mkdir(parents=True, exist_ok=True)
    original = config.read_text(encoding="utf-8") if config.exists() else ""
    lines = original.splitlines()
    lines = remove_managed_block(lines)
    lines = remove_exact_host_block(lines, args.host)

    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        lines.append("")
    lines.extend(
        [
            BEGIN,
            f"Host {args.host}",
            f"    HostName {args.hostname}",
            f"    User {args.user}",
            f"    Port {args.port}",
            f"    IdentityFile {args.identity_file}",
            "    IdentitiesOnly yes",
            END,
        ]
    )
    desired = "\n".join(lines) + "\n"

    if desired == original.replace("\r\n", "\n"):
        print("changed=false")
        return 0

    current_mode = config.stat().st_mode & 0o777 if config.exists() else 0o600
    fd, temporary_name = tempfile.mkstemp(prefix=f".{config.name}.", dir=config.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(desired)
        os.chmod(temporary_name, current_mode)
        os.replace(temporary_name, config)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)

    print("changed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
