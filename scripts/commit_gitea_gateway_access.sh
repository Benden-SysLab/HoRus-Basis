#!/usr/bin/env bash
set -euo pipefail

rollback_unit=horus-gitea-fw-rollback
: "${HORUS_GITEA_LB_ADDRESS:?HORUS_GITEA_LB_ADDRESS is required}"
: "${HORUS_GITEA_ADDRESS:?HORUS_GITEA_ADDRESS is required}"
: "${HORUS_GITEA_HTTP_PORT:?HORUS_GITEA_HTTP_PORT is required}"
: "${HORUS_GITEA_SSH_PORT:?HORUS_GITEA_SSH_PORT is required}"

rule="ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_HTTP_PORT}"
rule_ssh="ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_SSH_PORT}"
rule_oidc="ip saddr ${HORUS_GITEA_ADDRESS} ip daddr ${HORUS_GITEA_LB_ADDRESS} tcp dport 443"

grep -Fq "$rule" /etc/nftables.conf
nft list chain inet horus_filter forward | grep -F "$rule" >/dev/null
grep -Fq "$rule_ssh" /etc/nftables.conf
nft list chain inet horus_filter forward | grep -F "$rule_ssh" >/dev/null
grep -Fq "$rule_oidc" /etc/nftables.conf
nft list chain inet horus_filter forward | grep -F "$rule_oidc" >/dev/null

systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
systemctl reset-failed "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
rm -f /run/horus-gitea-fw-rollback.sh

echo 'COMMIT_OK'
nft -a list chain inet horus_filter forward | grep -F "$rule"
nft -a list chain inet horus_filter forward | grep -F "$rule_ssh"
nft -a list chain inet horus_filter forward | grep -F "$rule_oidc"
