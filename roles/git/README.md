# Gitea

Installs Gitea on `horus-git-srv01`, creates its dedicated PostgreSQL database
on `horus-db-srv03`, configures OpenID Connect against the `horus` Keycloak
realm, publishes the configured private URL through NGINX and Technitium, then installs
the shared operator tools and Fluent Bit profile.

Runtime credentials are generated into KeePass under the entry configured in
the private inventory overlay; no secret is stored in repository YAML. The local bootstrap administrator is retained as
an emergency account while normal users sign in through HoRus Access.

