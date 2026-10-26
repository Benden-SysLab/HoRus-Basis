# Jenkins controller

Installs pinned Jenkins LTS on `horus-jnk-srv01`, configures it through JCasC,
uses HoRus Access for OIDC, grants the configured account administration, and
publishes the configured private URL through NGINX and DNS. The controller has zero
executors; build capacity is added by Stage 10 agents.

Service role for the HoRus Basis host group. The role owns its complete
installation chain and calls shared roles from \`tasks/main.yml\`.

