from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_full_rollout_checks_existing_jenkins_access_before_service_roles() -> None:
    playbook = read("playbooks/00_full_install.yml")

    preflight = "stages/00_runtime_preflight.yml"
    baseline = "stages/00_host_baseline.yml"
    assert preflight in playbook
    assert playbook.index(preflight) < playbook.index(baseline)


def test_runtime_preflight_has_a_standalone_read_only_entrypoint() -> None:
    playbook = read("playbooks/00_runtime_preflight.yml")

    assert "_controller_credentials.yml" in playbook
    assert "stages/00_runtime_preflight.yml" in playbook


def test_agent_rollout_skips_bootstrap_when_runtime_access_is_ready() -> None:
    stage = read("playbooks/stages/10_agent.yml")

    assert "Preflight key-only access from Jenkins agent" in stage
    assert "jenkins_runtime_estate_ready" in stage
    assert "the 34-target bootstrap is skipped" in stage
    assert "Record verified Jenkins Ansible estate" in stage
    assert "when: not (jenkins_runtime_estate_ready | bool)" in stage


def test_jenkins_controller_and_agent_render_the_same_final_casc() -> None:
    controller_stage = read("playbooks/stages/09_jenkins.yml")

    assert "jenkins_agent_enabled: true" in controller_stage
    assert "jenkins_agent_ssh_private_key" in controller_stage
    assert "Read Jenkins agent ED25519 host key" in controller_stage


def test_postgresql_service_rules_use_the_baseline_spacing_contract() -> None:
    rule_files = (
        "roles/access/tasks/database.yml",
        "roles/git/tasks/database.yml",
        "roles/wiki/tasks/database.yml",
        "roles/vikunja/tasks/database.yml",
    )

    for rule_file in rule_files:
        assert "| join('    ')" in read(rule_file)

    assert "database: gitea" in read("roles/psql/defaults/main.yml")


def test_wiki_release_ownership_does_not_oscillate_on_repeat_rollout() -> None:
    install = read("roles/wiki/tasks/install.yml")

    assert (
        '- {path: "{{ wiki_release_dir }}", owner: "{{ wiki_system_user }}", '
        'group: "{{ wiki_system_group }}", mode: "0755"}'
    ) in install
    assert "register: wiki_release_extract" in install
    assert "when: wiki_release_extract.changed" in install


def test_jenkins_host_key_is_not_reinstalled_when_already_trusted() -> None:
    stage = read("playbooks/stages/09_jenkins.yml")

    assert "Read trusted Jenkins host key entries" in stage
    assert "Select scanned Jenkins ED25519 host key" in stage
    assert "jenkins_scanned_key_line.split()[1:3]" in stage
    assert "jenkins_host_key_is_trusted" in stage
    assert "when: not (jenkins_host_key_is_trusted | bool)" in stage
