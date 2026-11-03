# HoRus observability contract

This repository configures the workload-side exporters and log forwarder. The
Prometheus/Loki/OTel services themselves are managed by HoRus-Observability.

## Endpoints

| Source | Endpoint | Consumer | Payload |
|---|---|---|---|
| Basis hosts | `:9100` | Prometheus `10.10.50.41:9090` | node metrics |
| `horus-db-srv03` | `10.10.1.31:9187/metrics` | Prometheus `10.10.50.41:9090` | PostgreSQL metrics |
| Basis hosts | `10.10.50.43:3100/loki/api/v1/push` | Loki | Fluent Bit logs |
| Future application emitters | `10.10.50.44:8889` | OTel/Prometheus | application metrics |

## Required Observability-side configuration

HoRus-Observability must scrape at least:

```yaml
scrape_configs:
  - job_name: horus-node
    static_configs:
      - targets:
          - 10.10.1.14:9100
          - 10.10.1.12:9100
          - 10.10.1.13:9100
          - 10.10.1.26:9100
          - 10.10.1.31:9100
          - 10.10.1.32:9100
          - 10.10.1.33:9100
          - 10.10.1.34:9100
          - 10.10.1.36:9100
          - 10.10.1.37:9100
          - 10.10.50.47:9100
  - job_name: horus-postgresql
    static_configs:
      - targets: [10.10.1.31:9187]
```

The gateway/host firewall must allow Prometheus `10.10.50.41` to reach the
exporter ports and Basis hosts to reach Loki `10.10.50.43:3100`. Firewall
changes are intentionally not hidden in this role.

No passwords or API tokens are used by these paths. If Loki or OTel later
requires authentication, credentials must come from Vault/KeePass and must not
be added to inventory YAML.
