# wiki

Installs the stable Wiki.js 2.x release on `horus-wiki-srv01`, prepares its
PostgreSQL database on `horus-db-srv03`, bootstraps the local emergency admin,
creates the Keycloak client, publishes the configured private URL through the central
NGINX and Technitium DNS, and calls the shared operator and Fluent Bit roles.

The Wiki.js Keycloak authentication strategy itself is enabled after the first
deployment because Wiki.js generates the strategy callback identifier. The
Keycloak client accepts callbacks only below the configured Wiki.js URL.

