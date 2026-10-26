# HoRus-Basis

HoRus 的 Ansible 服务层。HoRus-Bootstrap 创建 Proxmox VM/LXC 基础设施；本仓库
负责配置客户机操作系统和核心服务。

完整参考：[README.md](README.md)。俄语：[README.RU.md](README.RU.md)。

## 架构

部署采用 LEGO 模型。Stage 01 安装 NGINX 和 HoRus Control Plane。后续每个
Stage 管理自己的应用、PostgreSQL 契约、NGINX `conf.d` 片段、DNS 发布和仪表板
manifest。通用 SRE 工具和 Fluent Bit 由相应服务 role 调用。

## 阶段

`00_full_install.yml` 依次执行：01 NGINX、02 PostgreSQL、03 Vault、04 Keycloak、
05 Gitea、06 Wiki.js、07 Vikunja、08 Zot Registry、09 Jenkins Controller、
10 包含 Ansible 的 Jenkins Agent，以及 11 GitGuardian/ggshield。每个 Stage 也可
配合 `--limit` 单独运行。

## Secrets 与运行

Secrets 仅存储在本地 KeePass 数据库中：

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

SSH 私钥和 KeePass 文件绝不能提交到 Git。Controller 依赖使用
`.venv-wsl/bin/pip install -r requirements-controller.txt` 安装。

## 管理边界

HoRus-Basis 管理 guest OS、packages、services、logging 和 publication。
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) 管理 Proxmox
lifecycle、network、placement 和 storage。Gateway 变更必须使用带 backup 和
定时 rollback 的 apply/commit scripts。
