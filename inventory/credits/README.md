# KeePass secret source

HoRus-Basis never stores credentials in repository YAML. The controller reads
passwords, tokens, generated application secrets and initialization material
from an existing KeePass 2 database at runtime.

The private names of KeePass groups and entries belong in the ignored
`inventory/vault/horus_vault.yml` overlay. The tracked
`inventory/vault/horus_vault.yml.example` contains only placeholders.

```bash
python3 -m venv .venv-wsl
.venv-wsl/bin/pip install -r requirements-controller.txt
export HORUS_KEEPASS_DATABASE=/mnt/c/path/to/passwords.kdbx
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

The master password is requested interactively and kept only in controller
memory for the current run. KeePass databases, key files, passwords, tokens
and private SSH keys must never be committed.

Some stages create missing KeePass entries with cryptographically random
values. Existing entries are validated and are not overwritten automatically.
Vault initialization material is written only to KeePass; no plaintext
initialization file is created in the repository.

Stage 10 references local SSH key files through paths defined in the private
overlay. The referenced private keys are not copied into this repository.
