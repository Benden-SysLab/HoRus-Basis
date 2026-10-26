#!/usr/bin/env bash
set -eu

echo '=== HOST ==='
hostname

echo '=== TABLES ==='
nft list tables

echo '=== FORWARD ==='
nft -a list ruleset \
  | grep -n -E 'hook forward|admin_hosts|internal_nets|10\.10\.70|10\.10\.1' -C 8 \
  || true

echo '=== MANAGED FILES ==='
find /etc/horus/policy /usr/local/lib/horus \
  -maxdepth 3 -type f -print 2>/dev/null \
  | sort \
  || true

echo '=== POLICY REFERENCES ==='
grep -RniE 'admin_hosts|internal_nets|forward|services\.d' \
  /etc/horus/policy \
  /usr/local/lib/horus \
  /usr/local/sbin/horus-policy-apply \
  2>/dev/null \
  || true
