from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


DOCUMENTATION = r"""
name: keepass2
author: HoRus
short_description: Read one field from a KeePass 2 database
description:
  - Opens a KDBX database on the Ansible controller and returns a field from
    one entry. The master password is supplied by a private vars_prompt.
options:
  _terms:
    description: Entry path separated by slashes.
    required: true
  database:
    description: Controller-side path to the KDBX database.
    required: true
  master_password:
    description: KeePass database master password.
    required: true
  field:
    description: Entry field to return.
    choices: [username, password, url, notes, title]
    default: password
"""


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        try:
            from pykeepass import PyKeePass
        except ImportError as exc:
            raise AnsibleError(
                "KeePass lookup requires controller dependency: "
                "pip install -r requirements-controller.txt"
            ) from exc

        database = str(kwargs.get("database", "")).strip()
        master_password = kwargs.get("master_password")
        field = str(kwargs.get("field", "password"))
        select = str(kwargs.get("select", "exact"))

        if not database:
            raise AnsibleError(
                "HORUS_KEEPASS_DATABASE is empty; set it to the controller-side KDBX path"
            )
        if master_password is None:
            raise AnsibleError("KeePass master password was not provided")
        if field not in {"username", "password", "url", "notes", "title"}:
            raise AnsibleError("Unsupported KeePass entry field")
        if select not in {"exact", "latest_valid"}:
            raise AnsibleError("Unsupported KeePass entry selection")

        database_path = Path(database).expanduser()
        if not database_path.is_file():
            raise AnsibleError("KeePass database does not exist at the configured path")

        try:
            keepass = PyKeePass(str(database_path), password=str(master_password))
        except Exception as exc:
            raise AnsibleError(
                "Unable to unlock the KeePass database; verify its path, master password, "
                "and whether it requires an additional key file"
            ) from exc

        results = []
        for term in terms:
            entry_path = [part for part in str(term).split("/") if part]
            if select == "latest_valid":
                group = keepass.root_group
                for group_name in entry_path:
                    group = next(
                        (item for item in group.subgroups if item.name == group_name),
                        None,
                    )
                    if group is None:
                        break
                if group is None:
                    raise AnsibleError(
                        f"KeePass group was not found for token selection: {term}"
                    )

                now = datetime.now(timezone.utc)
                valid_entries = []
                for candidate in group.entries:
                    if not candidate.password:
                        continue
                    expiry = getattr(candidate, "expiry_time", None)
                    expires = getattr(candidate, "expires", True)
                    if expires and (expiry is None or expiry.astimezone(timezone.utc) <= now):
                        continue
                    valid_entries.append(candidate)

                if not valid_entries:
                    raise AnsibleError(
                        f"No non-expired KeePass token entries were found in group: {term}"
                    )
                entry = max(
                    valid_entries,
                    key=lambda item: (
                        getattr(item, "expiry_time", None)
                        or datetime.max.replace(tzinfo=timezone.utc)
                    ),
                )
            elif len(entry_path) == 1:
                matching_entries = keepass.find_entries(
                    title=entry_path[0],
                    first=False,
                )
                entry = matching_entries[0] if len(matching_entries) == 1 else None
            else:
                entry = keepass.find_entries(path=entry_path, first=True)

                # KeePass group layouts can change without changing the entry
                # contract used by Ansible. If the configured path is stale,
                # accept an exact title match only when it is unique globally.
                if entry is None:
                    matching_entries = keepass.find_entries(
                        title=entry_path[-1],
                        first=False,
                    )
                    entry = matching_entries[0] if len(matching_entries) == 1 else None

            if entry is None:
                raise AnsibleError(
                    "Configured KeePass entry was not found, or its title is not unique"
                )

            value = getattr(entry, field, None)
            if value is None or value == "":
                raise AnsibleError("Requested field is empty in the configured KeePass entry")
            results.append(value)

        return results
