# nginx

Minimal NGINX baseline for `horus-lb-srv01`.

The role installs NGINX, places a loopback-only health endpoint on port 8080,
validates configuration before replacement, and then invokes the shared SRE
tools and Fluent Bit roles from `tasks/main.yml`. Application upstreams are
intentionally not defined here yet.

The Stage 01 dashboard is grouped into three sections with three cards per row:

- `NET`: gateway Web Admin, v2rayA, Technitium DNS and the two managed HoRus
  switches;
- `Infra`: the four internal Proxmox web consoles;
- `Service`: application manifests published by their own installation stages.

Only internal HoRus resources are included. Public NL addresses and unrelated
external services are deliberately excluded from the dashboard.

