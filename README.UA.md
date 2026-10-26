# HoRus-Basis

Ansible-шар сервісів HoRus. HoRus-Bootstrap створює інфраструктуру VM/LXC у
Proxmox, а цей репозиторій налаштовує гостьові ОС та основні сервіси.

Повна довідка: [README.md](README.md). Російська:
[README.RU.md](README.RU.md).

## Архітектура

Розгортання побудоване за моделлю LEGO. Етап 01 встановлює NGINX і HoRus
Control Plane. Кожен наступний етап володіє своїм застосунком, контрактом
PostgreSQL, фрагментом NGINX `conf.d`, DNS-публікацією та маніфестом панелі.
Спільні SRE-інструменти та Fluent Bit викликаються роллю відповідного сервісу.

## Етапи

`00_full_install.yml` виконує: 01 NGINX, 02 PostgreSQL, 03 Vault, 04 Keycloak,
05 Gitea, 06 Wiki.js, 07 Vikunja, 08 Zot Registry, 09 Jenkins Controller,
10 Jenkins Agent з Ansible та 11 GitGuardian/ggshield. Кожен етап можна
запустити окремо з `--limit`.

## Секрети та запуск

Секрети зберігаються лише в локальній базі KeePass:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Приватні SSH-ключі та файли KeePass не повинні потрапляти в Git. Залежності
встановлюються командою
`.venv-wsl/bin/pip install -r requirements-controller.txt`.

## Межі відповідальності

HoRus-Basis керує гостьовою ОС, пакетами, сервісами, логами та публікацією.
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) керує
життєвим циклом Proxmox, мережею, placement і storage. Зміни gateway виконуються
apply/commit-скриптами з backup та відкладеним rollback.
