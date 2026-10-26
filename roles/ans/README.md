# Ansible on the Jenkins agent

Installs pinned Ansible Core in an isolated virtual environment on
`horus-agent-srv01`, publishes the standard Ansible commands, and prepares the
inventory used by Jenkins jobs. Stage 10 uses a dedicated Ed25519 key for
each trust zone, installs private keys only for the configured automation
account, and appends each public key only to targets in its zone. Key file
names, account names, host membership, and controller paths come from the
private inventory overlay.

The rollout does not replace existing `authorized_keys` and does not grant new
passwordless sudo rights. During the one-time Stage 10 bootstrap, SSH uses
`StrictHostKeyChecking=accept-new`. Previously unseen host keys are therefore
recorded without an interactive prompt, while changed keys remain a hard
failure. Host keys are then read through these bootstrap connections and
published to a dedicated runtime `known_hosts` file with strict checking
enabled.
Stage 10 verifies key-only Ansible ping from the Jenkins agent.

Bootstrap private keys remain outside the repository in the operator's
configured SSH storage. Bootstrap keys are copied into the controller's
private SSH directory with mode `0600`; the runtime keys are
copied directly to the Jenkins agent with mode `0600`. KeePass entries with
the same host names are account passwords, not key material.

