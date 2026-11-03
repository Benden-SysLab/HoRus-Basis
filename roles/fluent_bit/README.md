# fluent_bit

Shared Fluent Bit installation for every Basis target. The service role selects
log paths by host group and forwards `horus.*` records to the local file sink
and Loki at `observability_loki_host:observability_loki_port`.

The Loki endpoint is a non-secret inventory contract. Authentication, if it is
introduced later, must come from Vault/KeePass rather than this repository.

