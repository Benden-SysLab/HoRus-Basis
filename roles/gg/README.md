# GitGuardian ggshield

Installs pinned GitGuardian `ggshield` into an isolated Python virtual
environment on `horus-gg-srv01` and exposes the authenticated wrapper as
`/usr/local/bin/horus-ggshield`.

The selected non-expired API token is read from KeePass by the stage playbook
and stored only in `/etc/horus/ggshield.env` with mode `0640`, readable only
by root and the dedicated `gitguardian` group. The role does
not print or log the token.

GitGuardian SaaS remains the detection API and web interface. This role does
not pretend to deploy the licensed self-hosted GitGuardian platform. The
wrapper is intended for Jenkins jobs and controlled operator scans, for
example:

```bash
sudo -u gitguardian horus-ggshield secret scan repo /srv/horus/gitguardian/scans/repository
```

