#!/usr/bin/env bash
set -euo pipefail

config=/etc/nftables.conf
: "${HORUS_GITEA_LB_ADDRESS:?HORUS_GITEA_LB_ADDRESS is required}"
: "${HORUS_GITEA_ADDRESS:?HORUS_GITEA_ADDRESS is required}"
: "${HORUS_GITEA_HTTP_PORT:?HORUS_GITEA_HTTP_PORT is required}"
: "${HORUS_GITEA_SSH_PORT:?HORUS_GITEA_SSH_PORT is required}"

rule="        ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_HTTP_PORT} ct state new accept comment \"HoRus LB to Gitea API\""
rule_ssh="        ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_SSH_PORT} ct state new accept comment \"HoRus LB to Gitea SSH\""
rule_oidc="        ip saddr ${HORUS_GITEA_ADDRESS} ip daddr ${HORUS_GITEA_LB_ADDRESS} tcp dport 443 ct state new accept comment \"HoRus Gitea to Access OIDC\""
anchor='        ip saddr $NET_TRUSTED ip daddr $NET_INFRA accept \'
rollback_unit=horus-gitea-fw-rollback
rollback_delay=30m
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="/var/backups/nftables.conf.before-gitea-${timestamp}"
candidate="$(mktemp /tmp/nftables-gitea.XXXXXX.conf)"
rollback_script=/run/horus-gitea-fw-rollback.sh

cleanup() {
  rm -f "$candidate"
}
trap cleanup EXIT

if grep -Fq "$rule" "$config" && grep -Fq "$rule_ssh" "$config" && grep -Fq "$rule_oidc" "$config"; then
  echo 'RULES_ALREADY_PRESENT'
  nft list chain inet horus_filter forward | grep -F "${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_HTTP_PORT}"
  nft list chain inet horus_filter forward | grep -F "${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_SSH_PORT}"
  nft list chain inet horus_filter forward | grep -F "${HORUS_GITEA_ADDRESS} ip daddr ${HORUS_GITEA_LB_ADDRESS} tcp dport 443"
  exit 0
fi

anchor_count="$(grep -Fc "$anchor" "$config")"
if [ "$anchor_count" -ne 1 ]; then
  echo "REFUSING: expected one insertion anchor, found $anchor_count" >&2
  exit 1
fi

install -o root -g root -m 0600 "$config" "$backup"
add_rule=1
add_rule_ssh=1
add_rule_oidc=1
grep -Fq "$rule" "$config" && add_rule=0
grep -Fq "$rule_ssh" "$config" && add_rule_ssh=0
grep -Fq "$rule_oidc" "$config" && add_rule_oidc=0
awk -v anchor="$anchor" -v rule="$rule" -v rule_ssh="$rule_ssh" -v rule_oidc="$rule_oidc" \
    -v add_rule="$add_rule" -v add_rule_ssh="$add_rule_ssh" -v add_rule_oidc="$add_rule_oidc" '
  index($0, anchor) == 1 {
    if (add_rule == 1) print rule
    if (add_rule_ssh == 1) print rule_ssh
    if (add_rule_oidc == 1) print rule_oidc
  }
  { print }
' "$config" > "$candidate"

if [ "$(grep -Fc "$rule" "$candidate")" -ne 1 ] || \
   [ "$(grep -Fc "$rule_ssh" "$candidate")" -ne 1 ] || \
   [ "$(grep -Fc "$rule_oidc" "$candidate")" -ne 1 ]; then
  echo 'REFUSING: candidate does not contain exactly one copy of all Gitea rules' >&2
  exit 1
fi

nft -c -f "$candidate"
install -o root -g root -m 0644 "$candidate" "$config"

cat > "$rollback_script" <<EOF
#!/usr/bin/env bash
set -eu
install -o root -g root -m 0644 '$backup' '$config'
/usr/sbin/nft -f '$config'
logger -t horus-gitea-fw 'Automatic rollback restored $backup'
EOF
chmod 0700 "$rollback_script"

systemctl stop "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
systemctl reset-failed "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
systemd-run \
  --unit="$rollback_unit" \
  --on-active="$rollback_delay" \
  "$rollback_script"

if ! nft -f "$config"; then
  install -o root -g root -m 0644 "$backup" "$config"
  nft -f "$config"
  systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
  echo 'APPLY_FAILED_AND_ROLLED_BACK' >&2
  exit 1
fi

live_count="$(nft list chain inet horus_filter forward | grep -Fc "ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_HTTP_PORT}")"
ssh_live_count="$(nft list chain inet horus_filter forward | grep -Fc "ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_SSH_PORT}")"
oidc_live_count="$(nft list chain inet horus_filter forward | grep -Fc "ip saddr ${HORUS_GITEA_ADDRESS} ip daddr ${HORUS_GITEA_LB_ADDRESS} tcp dport 443")"
if [ "$live_count" -ne 1 ] || [ "$ssh_live_count" -ne 1 ] || [ "$oidc_live_count" -ne 1 ]; then
  "$rollback_script"
  systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
  echo "VERIFY_FAILED_AND_ROLLED_BACK: HTTP=$live_count SSH=$ssh_live_count OIDC=$oidc_live_count" >&2
  exit 1
fi

echo "APPLY_OK backup=$backup"
echo "ROLLBACK_ARMED unit=${rollback_unit}.timer duration=${rollback_delay}"
nft -a list chain inet horus_filter forward \
  | grep -F "ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_HTTP_PORT}"
nft -a list chain inet horus_filter forward \
  | grep -F "ip saddr ${HORUS_GITEA_LB_ADDRESS} ip daddr ${HORUS_GITEA_ADDRESS} tcp dport ${HORUS_GITEA_SSH_PORT}"
nft -a list chain inet horus_filter forward \
  | grep -F "ip saddr ${HORUS_GITEA_ADDRESS} ip daddr ${HORUS_GITEA_LB_ADDRESS} tcp dport 443"
