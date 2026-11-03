#!/usr/bin/env python3
"""Print changed Ansible tasks from a saved callback log."""

from collections import Counter
from pathlib import Path
import re
import sys


TASK = re.compile(r"TASK \[(?P<name>.+?)]")
CHANGED = re.compile(r"changed: \[(?P<host>[^]]+)]")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: report_changed_tasks.py ANSIBLE_LOG", file=sys.stderr)
        return 2

    current_task = None
    changes: Counter[tuple[str, str]] = Counter()
    for raw_line in Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line
        task_match = TASK.search(line)
        if task_match:
            current_task = task_match.group("name")
            continue
        changed_match = CHANGED.search(line)
        if current_task and changed_match:
            changes[(current_task, changed_match.group("host"))] += 1

    print("\nChanged task report")
    print("===================")
    if not changes:
        print("No changed task lines were recorded.")
        return 0
    for (task, host), count in changes.items():
        suffix = f" x{count}" if count > 1 else ""
        print(f"- {host}: {task}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
