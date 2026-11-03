# psql_exporter

Installs and configures `prometheus-postgres-exporter` on PostgreSQL hosts.
The exporter listens on the host address at port `9187`, so the Prometheus
instance in HoRus-Observability can scrape `/metrics`.

The Prometheus scrape configuration and firewall policy are maintained by the
observability/gateway layers; see `docs/OBSERVABILITY_CONTRACT.md`.

