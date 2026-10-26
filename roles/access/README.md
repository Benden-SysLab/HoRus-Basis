# access

Installs Keycloak as the HoRus identity and access-management service on the
`identity` inventory group. The role creates an isolated PostgreSQL role and
database on DB03, installs Keycloak as a systemd service, connects Fluent Bit,
publishes the configured private URL in Technitium, and adds an independent NGINX
reverse-proxy block and portal manifest.

Runtime secrets are read from KeePass and are never stored in repository YAML.
