import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_TEMPLATE = (
    REPOSITORY_ROOT / "roles/nginx/templates/portal/dashboard.html.j2"
)
OBSERVABILITY_ICON = (
    REPOSITORY_ROOT / "roles/nginx/files/portal/icons/observability.svg"
)
NGINX_DEFAULTS = REPOSITORY_ROOT / "roles/nginx/defaults/main.yml"
HEALTH_CHECK_TEMPLATE = (
    REPOSITORY_ROOT / "roles/nginx/templates/portal/health_check.py.j2"
)
NGINX_STAGE = REPOSITORY_ROOT / "playbooks/stages/01_nginx.yml"
PORTAL_GATEWAY_APPLY = (
    REPOSITORY_ROOT / "scripts/apply_portal_health_gateway_access.sh"
)


def dashboard_source() -> str:
    return DASHBOARD_TEMPLATE.read_text(encoding="utf-8")


def dashboard_categories(source: str) -> list[str]:
    match = re.search(r"const categories = \[(?P<categories>[^]]+)]", source)
    assert match, "Dashboard category allowlist is missing"
    return re.findall(r"'([^']+)'", match.group("categories"))


def test_dashboard_preserves_categories_and_adds_observability() -> None:
    assert dashboard_categories(dashboard_source()) == [
        "Infra",
        "Observability",
        "Service",
    ]


def test_grafana_manifest_matches_portal_contract() -> None:
    manifest = json.loads(
        """{
          "name": "Grafana",
          "description": "Dashboards and visualization",
          "url": "https://grafana.horus.admin/",
          "icon": "/icons/observability.svg",
          "category": "Observability",
          "subcategory": "Monitoring"
        }"""
    )

    source = dashboard_source()
    categories = dashboard_categories(source)
    grouped: dict[str, list[dict[str, str]]] = {}
    grouped.setdefault(manifest.get("category", "Service"), []).append(manifest)

    assert manifest["category"] in categories
    assert grouped["Observability"][0]["subcategory"] == "Monitoring"
    assert manifest["url"].startswith("https://")
    assert manifest["icon"].startswith("/icons/")
    assert "service.icon || serviceIcons[service.name]" in source
    assert "service.subcategory" in source
    assert "'Grafana': '/icons/observability.svg'" in source

    icon_root = ET.parse(OBSERVABILITY_ICON).getroot()
    assert icon_root.tag == "{http://www.w3.org/2000/svg}svg"
    assert "observability.svg" in NGINX_DEFAULTS.read_text(encoding="utf-8")


def test_grafana_has_observability_icon_fallback() -> None:
    assert "'Grafana': '/icons/observability.svg'" in dashboard_source()


def test_compact_glass_dashboard_and_availability_contract() -> None:
    source = dashboard_source()

    assert "#services { flex:1; min-height:0; display:flex; flex-direction:column" in source
    assert 'backdrop-filter:blur(18px) saturate(130%)' in source
    assert 'class="availability"' in source
    assert "refreshAvailability(services)" in source
    assert "/portal-health/${encodeURIComponent(service.id)}.json" in source
    assert "health.available === true" in source
    assert 'data-category="${escapeHtml(category)}"' in source
    assert 'Доступно: ${results.filter(Boolean).length} / ${services.length}' in source


def test_infrastructure_subgroups_and_health_contract() -> None:
    source = dashboard_source()

    assert "const categories = ['Infra', 'Observability', 'Service']" in source
    assert "service.subcategory" in source
    assert "data-service-id" in source
    assert "is-checking" in source
    assert "window.setInterval(() => refreshAvailability(services), 30000)" in source
    assert "grid-template-columns:repeat(var(--item-count),minmax(0,1fr))" in source
    assert "--item-count:${Math.max(1, services.length)}" in source
    assert ".tiles::before" not in source
    assert "container-type:inline-size" in source
    assert "font-size:clamp(15px,5cqi,22px)" in source

    defaults = NGINX_DEFAULTS.read_text(encoding="utf-8")
    assert "nginx_portal_health_dir:" in defaults
    assert "keenetic.svg" in defaults


def test_health_checker_supports_appliance_web_interfaces() -> None:
    source = HEALTH_CHECK_TEMPLATE.read_text(encoding="utf-8")

    assert 'method="GET"' in source
    assert 'result["available"] = True' in source
    assert 'except HTTPError as error:' in source
    assert 'result["status"] = error.code' in source
    assert 'method="HEAD"' not in source


def test_portal_health_gateway_policy_is_narrow_and_rollback_protected() -> None:
    stage = NGINX_STAGE.read_text(encoding="utf-8")
    policy = PORTAL_GATEWAY_APPLY.read_text(encoding="utf-8")

    assert "apply_portal_health_gateway_access.sh" in stage
    assert "commit_portal_health_gateway_access.sh" in stage
    assert "Refresh portal health after gateway policy verification" in stage
    assert "--on-active=30m" in policy
    assert '/usr/bin/bash "$rollback_script"' in policy
    assert "nft -c -f" in policy
    assert "grep -Fq 'HoRus portal health" not in policy
    assert "10.10.1.14 tcp dport { 2017, 5380, 9090 }" in policy
    assert "10.255.0.2, 10.255.0.3, 10.255.0.4" in policy
    assert "10.255.0.5, 10.255.0.6" in policy
    assert "tcp dport 80" in policy
    assert "10.255.0.7, 10.255.0.8, 10.255.0.9, 10.255.0.10" in policy
    assert "tcp dport 8006" in policy
