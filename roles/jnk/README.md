# Jenkins controller

Installs security-fixed Jenkins LTS 2.580.2 on `horus-jnk-srv01`, configures it through JCasC,
uses HoRus Access for OIDC, grants the configured account administration, and
publishes the configured private URL through NGINX and DNS. The controller has zero
executors; build capacity is added by Stage 10 agents.

The controller runs on the supported OpenJDK 25 runtime. The role pins the
Jenkins service to the Java 25 executable and validates the selected runtime.

Service role for the HoRus Basis host group. The role owns its complete
installation chain and calls shared roles from \`tasks/main.yml\`.

