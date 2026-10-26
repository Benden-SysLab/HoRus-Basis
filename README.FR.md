# HoRus-Basis

Couche de services Ansible de HoRus. HoRus-Bootstrap crée l'infrastructure
VM/LXC Proxmox ; ce dépôt configure les systèmes invités et les services cœur.

Référence complète : [README.md](README.md). Russe :
[README.RU.md](README.RU.md).

## Architecture

Le déploiement suit un modèle LEGO. L'étape 01 installe NGINX et HoRus Control
Plane. Chaque étape suivante possède son application, son contrat PostgreSQL,
son fragment NGINX `conf.d`, sa publication DNS et son manifeste de portail.
Les outils SRE communs et Fluent Bit sont appelés par le rôle du service.

## Étapes

`00_full_install.yml` exécute : 01 NGINX, 02 PostgreSQL, 03 Vault, 04 Keycloak,
05 Gitea, 06 Wiki.js, 07 Vikunja, 08 Zot Registry, 09 Jenkins Controller,
10 Jenkins Agent avec Ansible et 11 GitGuardian/ggshield. Chaque étape peut être
exécutée séparément avec `--limit`.

## Secrets et exécution

Les secrets restent uniquement dans une base KeePass locale :

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Les clés SSH privées et fichiers KeePass ne doivent jamais entrer dans Git.
Installez les dépendances via
`.venv-wsl/bin/pip install -r requirements-controller.txt`.

## Frontières

HoRus-Basis gère l'OS invité, les paquets, services, logs et publications.
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) gère le
cycle de vie Proxmox, le réseau, le placement et le stockage. Les changements
gateway utilisent le workflow apply/commit avec sauvegarde et rollback temporisé.
