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


def dashboard_source() -> str:
    return DASHBOARD_TEMPLATE.read_text(encoding="utf-8")


def dashboard_categories(source: str) -> list[str]:
    match = re.search(r"const categories = \[(?P<categories>[^]]+)]", source)
    assert match, "Dashboard category allowlist is missing"
    return re.findall(r"'([^']+)'", match.group("categories"))


def test_dashboard_preserves_categories_and_adds_observability() -> None:
    assert dashboard_categories(dashboard_source()) == [
        "NET",
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
