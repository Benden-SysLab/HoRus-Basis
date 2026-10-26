# HoRus-Basis

HoRus の Ansible サービス層です。HoRus-Bootstrap が Proxmox の VM/LXC
インフラを作成し、このリポジトリがゲスト OS と主要サービスを設定します。

完全なリファレンス: [README.md](README.md)。ロシア語:
[README.RU.md](README.RU.md)。

## アーキテクチャ

デプロイは LEGO モデルです。Stage 01 が NGINX と HoRus Control Plane を
構築します。後続の各 Stage は、アプリケーション、PostgreSQL 契約、NGINX
`conf.d`、DNS 公開、ダッシュボード manifest を所有します。共通 SRE ツールと
Fluent Bit は各サービスロールから呼び出されます。

## Stage

`00_full_install.yml` は、01 NGINX、02 PostgreSQL、03 Vault、04 Keycloak、
05 Gitea、06 Wiki.js、07 Vikunja、08 Zot Registry、09 Jenkins Controller、
10 Ansible を含む Jenkins Agent、11 GitGuardian/ggshield の順に実行します。
各 Stage は `--limit` を使って個別に実行できます。

## Secrets と実行

Secrets はローカル KeePass データベースだけに保存します。

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

SSH 秘密鍵と KeePass ファイルを Git に追加しないでください。Controller の
依存関係は `.venv-wsl/bin/pip install -r requirements-controller.txt` で導入します。

## 管理境界

HoRus-Basis は guest OS、packages、services、logging、publication を管理します。
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) は Proxmox
lifecycle、network、placement、storage を管理します。Gateway 変更には backup と
timed rollback を備えた apply/commit scripts を使用します。
