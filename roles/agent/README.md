# Jenkins build agent

Installs the Java 21 and build-tool baseline on `horus-agent-srv01`, creates a
dedicated `jenkins` account, authorizes a KeePass-managed SSH key, and registers
the node on the Jenkins controller with a pinned ED25519 host key.

Service role for the HoRus Basis host group. The role owns its complete
installation chain and calls shared roles from \`tasks/main.yml\`.

