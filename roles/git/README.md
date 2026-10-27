# Gitea

Installs Gitea on `horus-git-srv01`, creates its dedicated PostgreSQL database
on `horus-db-srv03`, configures OpenID Connect against the `horus` Keycloak
realm, publishes the configured private URL through NGINX and Technitium, then installs
the shared operator tools and Fluent Bit profile.

The same stage publishes Git-over-SSH without taking over the load balancer's
management SSH port. NGINX listens on public TCP port `2222` and forwards the
connection to port `22` on `horus-git-srv01`. Gitea advertises that public port
in generated clone links, for example:

```text
ssh://git@git.horus.admin:2222/Benden-SysLab/HoRus-Basis.git
```

The gateway rules required for the HTTP, SSH, and OIDC paths are applied by
Stage 05 with an automatic rollback timer and committed only after all Gitea
health checks pass. Stage 05 also adds the Gitea system account to the existing
managed SSH `AllowUsers` policy, validates the complete SSH daemon configuration
before restarting it, and fails closed when the expected managed policy file is
absent.

On the controller, Stage 05 maintains separate exact-host OpenSSH client blocks
for WSL and Windows. It copies the Windows-held Gitea private key into the WSL
filesystem with mode `0600`, uses the WSL key path there, and keeps the native
Windows key path in the Windows SSH config used by VS Code and Windows Git. All
local paths live only in the ignored private inventory overlay.

Runtime credentials are generated into KeePass under the entry configured in
the private inventory overlay; no secret is stored in repository YAML. The local bootstrap administrator is retained as
an emergency account while normal users sign in through HoRus Access.

