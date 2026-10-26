#!/usr/bin/env bash
set -eu

echo '=== NFTABLES UNIT ==='
systemctl cat nftables.service 2>/dev/null || true

echo '=== NFTABLES CONFIG ==='
for path in /etc/nftables.conf /etc/nftables.d /etc/horus /usr/local/lib/horus /usr/local/sbin; do
  [ -e "$path" ] && printf '%s\n' "$path"
done

echo '=== HORUS FILTER SOURCE ==='
grep -RIl --exclude='*.before-*' --exclude='*.bak' \
  -E 'table[[:space:]]+inet[[:space:]]+horus_filter|Laptop and Jenkins administrative access|Trusted clients to infrastructure' \
  /etc /usr/local/lib /usr/local/sbin 2>/dev/null \
  | sort \
  | while IFS= read -r file; do
      echo "--- $file ---"
      grep -n -E 'table[[:space:]]+inet[[:space:]]+horus_filter|chain forward|policy drop|Laptop and Jenkins administrative access|Trusted clients to infrastructure' \
        -C 12 "$file" || true
    done

echo '=== RELATED UNITS ==='
systemctl list-unit-files --no-pager \
  | grep -Ei 'horus|nft|firewall' \
  || true
