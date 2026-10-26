# HoRus-Basis

Ansible service layer for the HoRus platform. HoRus-Bootstrap creates the
Proxmox VM/LXC infrastructure; this repository configures the guest operating
systems and deploys the core services in a deterministic stage order.

Russian documentation: [README.RU.md](README.RU.md).

Other languages: [Deutsch](README.DE.md) · [Español](README.ES.md) ·
[Français](README.FR.md) · [日本語](README.JA.md) ·
[Português](README.PT.md) · [Українська](README.UA.md) ·
[中文](README.ZH.md).

## Architecture

The deployment follows a LEGO model. Stage 01 installs the shared NGINX entry
point and HoRus Control Plane. Each later service stage owns its application,
database contract, NGINX `conf.d` fragment, DNS publication and dashboard
manifest. Shared operator tooling and Fluent Bit are included by the service
roles rather than run as unrelated manual installers.

```text
HoRus-Bootstrap / Terraform
  -> VM and LXC lifecycle, placement, compute, network and storage

HoRus-Basis / Ansible
  -> guest OS, packages, databases, services, logging and publication

NGINX foundation
  -> modular service fragments + responsive HoRus Control Plane
```

## Deployment stages

| Stage | Playbook | Target | Purpose |
|---:|---|---|---|
| 01 | `01_nginx.yml` | `horus-lb-srv01` | NGINX, central portal and Technitium DNS publication |
| 02 | `02_psql.yml` | `horus-db-srv03` | PostgreSQL, exporter and database logging |
| 03 | `03_vault.yml` | `horus-vlt-srv01` | Vault with PostgreSQL storage and NGINX publication |
| 04 | `04_access.yml` | `horus-iam-srv01` | Keycloak access management and personal admin account |
| 05 | `05_gitea.yml` | `horus-git-srv01` | Gitea with PostgreSQL and OIDC |
| 06 | `06_wiki.yml` | `horus-wiki-srv01` | Wiki.js with PostgreSQL and OIDC |
| 07 | `07_vikunja.yml` | `horus-vkj-srv01` | Vikunja tasks and planning with PostgreSQL and OIDC |
| 08 | `08_registry.yml` | `horus-reg-srv01` | Zot OCI registry with OIDC |
| 09 | `09_jenkins.yml` | `horus-jnk-srv01` | Jenkins controller, plugins, JCasC and OIDC |
| 10 | `10_agent.yml` | `horus-agent-srv01` | Jenkins agent and Ansible control plane for managed targets |
| 11 | `11_gitguardian.yml` | `horus-gg-srv01` | ggshield-based secrets scanning |

`playbooks/00_full_install.yml` composes all stages in this order. Individual
stage entry points remain available for scoped deployment and recovery.

## Shared baseline

Service roles install the common SRE tools required for operation and
diagnostics. Fluent Bit is installed cleanly and receives a service-specific
configuration. PostgreSQL additionally exposes local metrics through
postgres_exporter. Service roles validate their own daemon, backend and
published endpoint before completion.

The NGINX portal groups links into NET, INFRA and SERVICE sections. Service
stages add their own reverse-proxy fragment and manifest, so the portal grows
without rewriting the foundation role.

## Secrets

Runtime passwords, API tokens, OIDC secrets and generated credentials are kept
in a local KeePass database. They are read on the Ansible controller through
the repository lookup plugin and helper scripts; they must never be committed
to YAML or Git.

Set the database path in WSL before a run:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
```

The playbooks prompt for the KeePass master password and keep it only in
controller memory for the current run. `.kdbx`, `.keyx`, virtual environments,
Ansible runtime data and retry files are ignored by Git.

Sensitive topology and integration metadata are separated from the public
inventory. Copy `inventory/vault/horus_vault.yml.example` to
`inventory/vault/horus_vault.yml` and fill the local file. The real overlay is
ignored by Git and contains addresses, account names, SSH key paths, KeePass
entry names, internal domains and service endpoints. The tracked example is
only a schema with placeholders; passwords and tokens remain in KeePass.

## Controller setup

The supported controller environment is Debian WSL with a repository-local
Python virtual environment:

```bash
python3 -m venv .venv-wsl
.venv-wsl/bin/pip install -r requirements-controller.txt
```

Inventory and common non-secret defaults live under `inventory/`. SSH private
keys remain outside the repository. Verify host fingerprints before accepting
new or changed host keys.

## Running a stage

```bash
cd /mnt/d/Projects/Benden-SysLab/HoRus-Basis
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'

.venv-wsl/bin/ansible-playbook \
  playbooks/06_wiki.yml \
  --limit horus-wiki-srv01 \
  -K
```

Run the complete pipeline only when a full rollout is intended:

```bash
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Use `--limit` for a scoped rerun. A service stage may also update NGINX, DNS,
gateway policy or its PostgreSQL database when those integrations belong to
that service.

## Validation

Before deployment:

```bash
.venv-wsl/bin/ansible-playbook --syntax-check playbooks/00_full_install.yml
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml --list-hosts
```

After deployment, use the checks built into each role and verify the service
through its published HoRus URL. An Ansible `ok` result is configuration
evidence, not a substitute for endpoint and authentication verification.

## Repository structure

| Path | Purpose |
|---|---|
| `inventory/` | host groups and shared non-secret variables |
| `playbooks/` | complete pipeline and stage entry points |
| `roles/` | service, observability and publication roles |
| `lookup_plugins/` | controller-side KeePass lookup |
| `scripts/` | KeePass helpers and rollback-protected gateway policy tools |
| `docs/` | operational notes and handoff documentation |

## Ownership and safety

Do not use this repository to create, destroy or resize Proxmox guests;
infrastructure lifecycle belongs to
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap). Review
inventory targets and `--limit` before every run. Gateway changes must use the
provided apply/commit workflow with backup and timed rollback.

Repository: [Benden-SysLab/HoRus-Basis](https://github.com/Benden-SysLab/HoRus-Basis).
