# vikunja

Installs Vikunja on `horus-vkj-srv01`, prepares its dedicated PostgreSQL
database, configures HoRus Keycloak OIDC, publishes the configured private URL through
the central NGINX and Technitium DNS, and stores uploaded files locally under
`/var/lib/vikunja/files`.

Redis and S3/MinIO are deliberately not required for this small installation.
