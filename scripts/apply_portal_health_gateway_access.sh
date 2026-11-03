#!/usr/bin/env bash
set -euo pipefail

config=/etc/nftables.conf
input_rule='        ip saddr 10.10.1.14 tcp dport { 2017, 5380, 9090 } ct state new accept comment "HoRus portal health to gateway web"'
net_rule='        ip saddr 10.10.1.14 ip daddr { 10.255.0.2, 10.255.0.3, 10.255.0.4, 10.255.0.5, 10.255.0.6 } tcp dport 80 ct state new accept comment "HoRus portal health to network devices"'
proxmox_rule='        ip saddr 10.10.1.14 ip daddr { 10.255.0.7, 10.255.0.8, 10.255.0.9, 10.255.0.10 } tcp dport 8006 ct state new accept comment "HoRus portal health to Proxmox"'
input_anchor='        ip saddr @admin_hosts tcp dport { 2017, 5380, 9090 } accept \'
forward_anchor='        ip saddr $NET_TRUSTED ip daddr $NET_INFRA accept \'
rollback_unit=horus-portal-health-fw-rollback
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="/var/backups/nftables.conf.before-portal-health-${timestamp}"
candidate="$(mktemp /tmp/nftables-portal-health.XXXXXX.conf)"
rollback_script=/run/horus-portal-health-fw-rollback.sh

cleanup() { rm -f "$candidate"; }
trap cleanup EXIT

if grep -Fq "$input_rule" "$config" \
  && grep -Fq "$net_rule" "$config" \
  && grep -Fq "$proxmox_rule" "$config"; then
  nft list chain inet horus_filter input \
    | grep -F 'HoRus portal health to gateway web' >/dev/null || nft -f "$config"
  nft list chain inet horus_filter forward \
    | grep -F 'HoRus portal health to network devices' >/dev/null
  nft list chain inet horus_filter forward \
    | grep -F 'HoRus portal health to Proxmox' >/dev/null
  echo 'POLICY_ALREADY_PRESENT'
  exit 0
fi

if [ "$(grep -Fc "$input_anchor" "$config")" -ne 1 ]; then
  echo 'REFUSING: expected exactly one portal input insertion anchor' >&2
  exit 1
fi
if [ "$(grep -Fc "$forward_anchor" "$config")" -ne 1 ]; then
  echo 'REFUSING: expected exactly one portal forward insertion anchor' >&2
  exit 1
fi

install -o root -g root -m 0600 "$config" "$backup"
add_input=1
add_net=1
add_proxmox=1
grep -Fq "$input_rule" "$config" && add_input=0
grep -Fq "$net_rule" "$config" && add_net=0
grep -Fq "$proxmox_rule" "$config" && add_proxmox=0

awk -v input_anchor="$input_anchor" -v forward_anchor="$forward_anchor" \
    -v input_rule="$input_rule" -v net_rule="$net_rule" \
    -v proxmox_rule="$proxmox_rule" -v add_input="$add_input" \
    -v add_net="$add_net" -v add_proxmox="$add_proxmox" '
  index($0, input_anchor) == 1 && add_input == 1 { print input_rule }
  index($0, forward_anchor) == 1 {
    if (add_net == 1) print net_rule
    if (add_proxmox == 1) print proxmox_rule
  }
  { print }
' "$config" > "$candidate"

for rule in "$input_rule" "$net_rule" "$proxmox_rule"; do
  if [ "$(grep -Fc "$rule" "$candidate")" -ne 1 ]; then
    echo 'REFUSING: candidate rule count is not exactly one' >&2
    exit 1
  fi
done

nft -c -f "$candidate"
install -o root -g root -m 0644 "$candidate" "$config"

cat > "$rollback_script" <<EOF
#!/usr/bin/env bash
set -eu
install -o root -g root -m 0644 '$backup' '$config'
/usr/sbin/nft -f '$config'
logger -t horus-portal-health-fw 'Automatic rollback restored $backup'
EOF
chmod 0700 "$rollback_script"

systemctl stop "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
systemctl reset-failed "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
systemd-run --unit="$rollback_unit" --on-active=30m /usr/bin/bash "$rollback_script"

if ! nft -f "$config"; then
  /usr/bin/bash "$rollback_script"
  systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
  echo 'APPLY_FAILED_AND_ROLLED_BACK' >&2
  exit 1
fi

if ! nft list chain inet horus_filter input \
    | grep -F 'HoRus portal health to gateway web' >/dev/null \
  || ! nft list chain inet horus_filter forward \
    | grep -F 'HoRus portal health to network devices' >/dev/null \
  || ! nft list chain inet horus_filter forward \
    | grep -F 'HoRus portal health to Proxmox' >/dev/null; then
  /usr/bin/bash "$rollback_script"
  systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
  echo 'VERIFY_FAILED_AND_ROLLED_BACK' >&2
  exit 1
fi

echo "APPLY_OK backup=$backup"
echo "ROLLBACK_ARMED unit=${rollback_unit}.timer duration=30m"
nft -a list chain inet horus_filter input | grep -F 'HoRus portal health'
nft -a list chain inet horus_filter forward | grep -F 'HoRus portal health'
