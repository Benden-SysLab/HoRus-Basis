# HoRus-Basis

Camada de serviços Ansible do HoRus. O HoRus-Bootstrap cria a infraestrutura
VM/LXC no Proxmox; este repositório configura os sistemas convidados e os
serviços centrais.

Referência completa: [README.md](README.md). Russo: [README.RU.md](README.RU.md).

## Arquitetura

O deployment segue um modelo LEGO. O estágio 01 instala NGINX e o HoRus Control
Plane. Cada estágio seguinte possui sua aplicação, contrato PostgreSQL,
fragmento NGINX `conf.d`, publicação DNS e manifesto do painel. As ferramentas
SRE comuns e o Fluent Bit são chamados pela própria role do serviço.

## Estágios

`00_full_install.yml` executa: 01 NGINX, 02 PostgreSQL, 03 Vault, 04 Keycloak,
05 Gitea, 06 Wiki.js, 07 Vikunja, 08 Zot Registry, 09 Jenkins Controller,
10 Jenkins Agent com Ansible e 11 GitGuardian/ggshield. Cada estágio também
pode ser executado isoladamente com `--limit`.

## Segredos e execução

Os segredos ficam somente em um banco KeePass local:

```bash
export HORUS_KEEPASS_DATABASE='/mnt/c/path/to/passwords.kdbx'
.venv-wsl/bin/ansible-playbook playbooks/00_full_install.yml -K
```

Chaves SSH privadas e arquivos KeePass nunca devem entrar no Git. Instale as
dependências com `.venv-wsl/bin/pip install -r requirements-controller.txt`.

## Limites

HoRus-Basis gerencia o sistema convidado, pacotes, serviços, logs e publicação.
[HoRus-Bootstrap](https://github.com/Benden-SysLab/HoRus-Bootstrap) gerencia o
ciclo de vida Proxmox, rede, placement e storage. Mudanças no gateway usam os
scripts apply/commit com backup e rollback temporizado.
