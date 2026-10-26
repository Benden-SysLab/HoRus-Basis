# HoRus-Basis

Capa de servicios Ansible de HoRus. HoRus-Bootstrap crea la infraestructura
VM/LXC en Proxmox; este repositorio configura los sistemas invitados y los
servicios principales.

Referencia completa: [README.md](README.md). Ruso: [README.RU.md](README.RU.md).

## Arquitectura

El despliegue sigue un modelo LEGO. La etapa 01 instala NGINX y HoRus Control
Plane. Cada etapa posterior controla su aplicación, contrato PostgreSQL,
fragmento NGINX `conf.d`, publicación DNS y manifiesto del panel. Las
herramientas SRE y Fluent Bit se incluyen desde la propia función del servicio.

## Etapas

`00_full_install.yml` ejecuta: 01 NGINX, 02 PostgreSQL, 03 Vault, 04 Keycloak,
05 Gitea, 06 Wiki.js, 07 Vikunja, 08 Zot Registry, 09 Jenkins Controller,
10 Jenkins Agent con Ansible y 11 GitGuardian/ggshield. Cada etapa también se
puede ejecutar por separado con `--limit`.

## Secretos y ejecución

Los secretos se guardan únicamente en una base KeePass local:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Las claves SSH privadas y los archivos KeePass nunca se guardan en Git. Instale
las dependencias con
`.venv-wsl/bin/pip install -r requirements-controller.txt`.

## Límites

HoRus-Basis administra SO invitado, paquetes, servicios, logs y publicación.
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) administra
el ciclo de vida Proxmox, red, placement y storage. Los cambios de gateway usan
los scripts apply/commit con backup y rollback temporizado.
