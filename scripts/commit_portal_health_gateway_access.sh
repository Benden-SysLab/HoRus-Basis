#!/usr/bin/env bash
set -euo pipefail

rollback_unit=horus-portal-health-fw-rollback
comments=(
  'HoRus portal health to gateway web'
  'HoRus portal health to network devices'
  'HoRus portal health to Proxmox'
)

for comment in "${comments[@]}"; do
  grep -Fq "$comment" /etc/nftables.conf
done
nft list chain inet horus_filter input | grep -F "${comments[0]}" >/dev/null
nft list chain inet horus_filter forward | grep -F "${comments[1]}" >/dev/null
nft list chain inet horus_filter forward | grep -F "${comments[2]}" >/dev/null

systemctl stop "${rollback_unit}.timer" 2>/dev/null || true
systemctl reset-failed "${rollback_unit}.timer" "${rollback_unit}.service" 2>/dev/null || true
rm -f /run/horus-portal-health-fw-rollback.sh

echo 'COMMIT_OK'
nft -a list chain inet horus_filter input | grep -F 'HoRus portal health'
nft -a list chain inet horus_filter forward | grep -F 'HoRus portal health'
