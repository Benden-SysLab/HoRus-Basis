# nginx

Minimal NGINX baseline for `horus-lb-srv01`.

The role installs NGINX, places a loopback-only health endpoint on port 8080,
validates configuration before replacement, and then invokes the shared SRE
tools and Fluent Bit roles from `tasks/main.yml`. Application upstreams are
intentionally not defined here yet.

The Stage 01 dashboard is grouped into three ordered vertical sections:

- `Infra`: nested `GateWay`, `NET` and `Proxmox` groups for gateway services,
  switches, Wi-Fi access points and the four internal Proxmox web consoles;
- `Observability`: monitoring and telemetry manifests published by the
  HoRus-Observability repository, with optional nested subcategories;
- `Service`: application manifests published by their own installation stages.

Only internal HoRus resources are included. Public NL addresses and unrelated
external services are deliberately excluded from the dashboard.

The browser reads same-origin health snapshots produced on the load balancer by
`horus-portal-health.timer`. This avoids false failures caused by CORS, mixed
HTTP/HTTPS content and private/self-signed certificates. HTTP responses below
500, including authentication challenges, mean that the endpoint is reachable.

