#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
keepass_database="${HORUS_KEEPASS_DATABASE:-}"
manage_dns="${HORUS_MANAGE_DNS:-true}"
run_log_dir="${HORUS_RUN_LOG_DIR:-${repo_root}/.horus-runs}"

if [[ -z "${keepass_database}" ]]; then
  printf '%s\n' \
    'HORUS_KEEPASS_DATABASE is empty.' \
    'Export the WSL path to the KeePass database before running this script.' >&2
  exit 2
fi

if [[ ! -f "${keepass_database}" ]]; then
  printf 'KeePass database does not exist: %s\n' "${keepass_database}" >&2
  exit 2
fi

cd "${repo_root}"

mkdir -p "${run_log_dir}"
chmod 700 "${run_log_dir}"
run_log="${run_log_dir}/full-install-$(date -u +%Y%m%dT%H%M%SZ).log"
export ANSIBLE_LOG_PATH="${run_log}"
printf 'Ansible run log: %s\n' "${run_log}"

set +e
.venv-wsl/bin/ansible-playbook \
  playbooks/00_full_install.yml \
  -e "horus_manage_dns=${manage_dns}" \
  "$@"
run_rc=$?
set -e

python3 scripts/report_changed_tasks.py "${run_log}" || true
exit "${run_rc}"
