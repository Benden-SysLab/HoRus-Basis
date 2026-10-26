# HoRus-Basis

Ansible-Service-Layer für HoRus. HoRus-Bootstrap erstellt die Proxmox-VM/LXC-
Infrastruktur; dieses Repository konfiguriert die Gastbetriebssysteme und die
zentralen Dienste.

Vollständige Referenz: [README.md](README.md). Russisch:
[README.RU.md](README.RU.md).

## Architektur

Das Deployment folgt einem LEGO-Modell. Stage 01 installiert NGINX und das
HoRus Control Plane. Jede weitere Stage besitzt ihre Anwendung, den
PostgreSQL-Vertrag, ein NGINX-`conf.d`-Fragment, DNS-Publikation und ein
Dashboard-Manifest. Gemeinsame SRE-Werkzeuge und Fluent Bit werden aus der
jeweiligen Service-Rolle eingebunden.

## Stages

`00_full_install.yml` führt aus: 01 NGINX, 02 PostgreSQL, 03 Vault, 04 Keycloak,
05 Gitea, 06 Wiki.js, 07 Vikunja, 08 Zot Registry, 09 Jenkins Controller,
10 Jenkins Agent mit Ansible und 11 GitGuardian/ggshield. Jede Stage kann auch
separat und mit `--limit` ausgeführt werden.

## Secrets und Start

Secrets liegen ausschließlich in einer lokalen KeePass-Datenbank:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Private SSH-Schlüssel und KeePass-Dateien gehören nicht in Git. Die
Controller-Abhängigkeiten werden mit
`.venv-wsl/bin/pip install -r requirements-controller.txt` installiert.

## Grenzen

HoRus-Basis verwaltet Gast-OS, Pakete, Dienste, Logging und Publikation.
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) besitzt den
Proxmox-Lifecycle, Netzwerk, Placement und Storage. Gateway-Änderungen verwenden
die bereitgestellten Apply/Commit-Skripte mit Backup und zeitgesteuertem Rollback.
