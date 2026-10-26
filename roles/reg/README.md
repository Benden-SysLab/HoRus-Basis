# reg

Installs Zot on `horus-reg-srv01`, stores OCI artifacts under `/var/lib/zot`,
uses HoRus Access for browser SSO, grants the configured account registry
administration, and publishes the configured private URL through NGINX and DNS.

Zot is deployed as a single native binary. It does not require Docker, Redis,
MinIO, or a separate database.

