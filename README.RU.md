# HoRus-Basis

Ansible-слой сервисов платформы HoRus. HoRus-Bootstrap создаёт инфраструктуру
VM/LXC в Proxmox, а этот репозиторий настраивает гостевые ОС и последовательно
разворачивает основные сервисы.

English documentation: [README.md](README.md).

Другие языки: [Deutsch](README.DE.md) · [Español](README.ES.md) ·
[Français](README.FR.md) · [日本語](README.JA.md) ·
[Português](README.PT.md) · [Українська](README.UA.md) ·
[中文](README.ZH.md).

## Архитектура

Развёртывание построено как LEGO. Этап 01 устанавливает общий входной NGINX и
HoRus Control Plane. Каждый следующий этап владеет своим приложением,
контрактом с PostgreSQL, фрагментом NGINX `conf.d`, DNS-публикацией и
манифестом панели. Общие SRE-инструменты и Fluent Bit вызываются из роли
устанавливаемого сервиса, а не отдельными ручными установщиками.

```text
HoRus-Bootstrap / Terraform
  -> жизненный цикл VM/LXC, размещение, ресурсы, сеть и хранилища

HoRus-Basis / Ansible
  -> гостевая ОС, пакеты, БД, сервисы, логи и публикация

Основа NGINX
  -> модульные конфиги сервисов + адаптивный HoRus Control Plane
```

## Этапы развёртывания

| Этап | Playbook | Целевой хост | Назначение |
|---:|---|---|---|
| 01 | `01_nginx.yml` | `horus-lb-srv01` | NGINX, центральный портал и публикация через Technitium DNS |
| 02 | `02_psql.yml` | `horus-db-srv03` | PostgreSQL, exporter и сбор логов БД |
| 03 | `03_vault.yml` | `horus-vlt-srv01` | Vault с хранением в PostgreSQL и публикацией через NGINX |
| 04 | `04_access.yml` | `horus-iam-srv01` | Keycloak, единый доступ и личная учётная запись администратора |
| 05 | `05_gitea.yml` | `horus-git-srv01` | Gitea с PostgreSQL и OIDC |
| 06 | `06_wiki.yml` | `horus-wiki-srv01` | Wiki.js с PostgreSQL и OIDC |
| 07 | `07_vikunja.yml` | `horus-vkj-srv01` | Vikunja для задач и планирования, PostgreSQL и OIDC |
| 08 | `08_registry.yml` | `horus-reg-srv01` | OCI Registry Zot с OIDC |
| 09 | `09_jenkins.yml` | `horus-jnk-srv01` | Jenkins controller, плагины, JCasC и OIDC |
| 10 | `10_agent.yml` | `horus-agent-srv01` | Jenkins agent и Ansible control plane для управляемых целей |
| 11 | `11_gitguardian.yml` | `horus-gg-srv01` | Поиск секретов через ggshield |

`playbooks/00_full_install.yml` собирает все этапы в указанном порядке.
Отдельные точки входа остаются для точечного развёртывания и восстановления.

## Общая основа

Сервисные роли устанавливают общие инструменты SRE для эксплуатации и
диагностики. Fluent Bit ставится чистым, после чего получает конфигурацию под
конкретный сервис. PostgreSQL дополнительно отдаёт локальные метрики через
postgres_exporter. Каждая роль проверяет демон, backend и опубликованный адрес.

Портал NGINX делит ссылки на NET, INFRA и SERVICE. Сервисные этапы добавляют
собственный reverse-proxy фрагмент и манифест, поэтому панель расширяется без
переписывания базовой роли.

## Секреты

Пароли, API-токены, OIDC-секреты и сгенерированные учётные данные хранятся в
локальной базе KeePass. Ansible читает их на контроллере через lookup-плагин и
вспомогательные скрипты. Секреты нельзя сохранять в YAML или Git.

Перед запуском укажите путь WSL к базе:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
```

Playbook запрашивает мастер-пароль KeePass и хранит его только в памяти
контроллера на время текущего запуска. Файлы `.kdbx`, `.keyx`, виртуальные
окружения, runtime Ansible и retry-файлы исключены из Git.

Чувствительная топология и данные интеграций отделены от публичного inventory.
Скопируйте `inventory/vault/horus_vault.yml.example` в
`inventory/vault/horus_vault.yml` и заполните локальный файл. Реальный overlay
игнорируется Git и содержит адреса, имена учётных записей, пути к SSH-ключам,
имена записей KeePass, внутренние домены и endpoint-ы сервисов. В Git остаётся
только витрина-схема с заглушками; пароли и токены по-прежнему лежат в KeePass.

## Подготовка контроллера

Поддерживаемая среда — Debian WSL с локальным виртуальным окружением:

```bash
python3 -m venv .venv-wsl
.venv-wsl/bin/pip install -r requirements-controller.txt
```

Inventory и общие несекретные переменные находятся в `inventory/`. Приватные
SSH-ключи хранятся вне репозитория. Перед принятием нового или изменившегося
host key проверяйте fingerprint.

## Запуск этапа

```bash
cd /mnt/d/Projects/Benden-SysLab/HoRus-Basis
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'

.venv-wsl/bin/ansible-playbook \
  playbooks/06_wiki.yml \
  --limit horus-wiki-srv01 \
  -K
```

Полный pipeline запускайте только для полного развёртывания:

```bash
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Для точечного повтора используйте `--limit`. Сервисный этап также может
обновить NGINX, DNS, gateway policy или свою БД PostgreSQL, если эта интеграция
принадлежит сервису.

## Проверка

```bash
.venv-wsl/bin/ansible-playbook --syntax-check playbooks/00_full_install.yml
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml --list-hosts
```

После установки используйте проверки роли и отдельно откройте опубликованный
HoRus URL. Результат Ansible `ok` подтверждает конфигурацию, но не заменяет
проверку endpoint и авторизации.

## Структура репозитория

| Путь | Назначение |
|---|---|
| `inventory/` | группы хостов и общие несекретные переменные |
| `playbooks/` | полный pipeline и точки входа этапов |
| `roles/` | роли сервисов, наблюдаемости и публикации |
| `lookup_plugins/` | lookup KeePass на контроллере |
| `scripts/` | KeePass helpers и gateway policy с защищённым откатом |
| `docs/` | эксплуатационные заметки и handoff-документация |

## Границы ответственности и безопасность

Репозиторий не должен создавать, удалять или изменять размер гостевых систем
Proxmox — их жизненным циклом управляет
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap). Перед
каждым запуском проверяйте inventory и `--limit`. Изменения gateway выполняются
только через подготовленный apply/commit workflow с резервной копией и
отложенным автоматическим откатом.

Репозиторий: [Benden-SysLab/HoRus-Basis](https://github.com/Benden-SysLab/HoRus-Basis).
