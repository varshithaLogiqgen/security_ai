# Production deployment

Status: the deployable configuration and verification tooling are implemented. Hosting, domain, organization SSO, AI approval/model, retention periods, off-site backup destination and audit archive remain **TBD**. No external account, paid resource, provider approval or public deployment has been created. Production startup rejects incomplete configuration.

## What is provided

- Linux Docker Compose stack: Caddy HTTPS/frontend, Gunicorn API, separate document worker, PostgreSQL 18 and ClamAV. Only ports 80/443 are published. An optional Ollama container runs on the private network.
- Secret-file support, separate migration/runtime database credentials, restricted runtime database grants, non-root/read-only application containers and bounded worker resources.
- OIDC code flow with PKCE/state/nonce and privileged-account MFA. The organization must register its own issuer/client; no identity provider has been selected on its behalf.
- Live readiness checks for database permissions/migrations, discovery/JWKS, ClamAV signatures/clean/EICAR samples and a synthetic AI contract probe.
- Authenticated encrypted database/file archives, backup verification/extraction, a PostgreSQL restore drill, and legal-hold-aware retention commands.
- GitHub Actions configuration for PostgreSQL, real ClamAV, frontend checks and container builds. This workflow has not been executed in a remote repository by this task.

## Decisions required before launch

Fill `deployment/.env` from `.env.example` only after the organization chooses its services and approves the data location/retention policy. Zero retention values intentionally block production startup. `AI_PROVIDER_APPROVED=false` intentionally blocks production startup; setting it to true is a record of actual approval, not a way to obtain approval.

The implemented generative adapter speaks the Ollama chat API. Use an approved self-hosted model with the `local-ai` profile or an approved HTTPS Ollama-compatible service. Other provider APIs need their own adapter and contract tests once selected. No employee information is used in readiness probes.

Choose a Linux host with Docker Compose, persistent encrypted disks, an inbound firewall allowing only 80/443 and your restricted management channel, DNS pointing the public domain to that host, and sufficient RAM (ClamAV about 3 GB container budget; model memory depends on the chosen model). Pin container images by reviewed digest before release. The supplied Compose database uses a private same-host network without TLS; managed/remote PostgreSQL must use `DATABASE_SSLMODE=verify-full` and its CA via `DATABASE_SSLROOTCERT`.

## Prepare secrets and SSO

From the repository root, using the backend virtual environment:

```powershell
backend/.venv/Scripts/python.exe deployment/generate_secrets.py
Copy-Item deployment/.env.example deployment/.env
```

The generator creates ignored secret files without printing or overwriting keys. Fill `deployment/secrets/oidc_secret` from the organization secret manager. `ollama_key` may be empty for the private Ollama container; use a key for an authenticated hosted endpoint. On Linux ensure the API container UID 10001 can read its mounted secret files, PostgreSQL can read its password files, and no other host users can read them. Local Compose secret mounts are file mounts, not an encrypted secret vault. Store recovery copies of the data and backup keys separately in your organization vault.

Register the exact redirect URI `https://YOUR_DOMAIN/api/v1/auth/callback` in the identity provider. Enable authorization code flow, PKCE S256, `openid email profile` scopes and ID-token issuance. Configure `OIDC_MFA_AMR` to match the issuer's documented MFA claims and test a privileged user with and without MFA. Invites require a verified email claim; automatic role assignment from claims is disabled. The readiness command checks discovery, not the complete human login/MFA flow.

## Deploy on the selected Linux host

All commands below run from `deployment/` with completed `.env` and secret files:

```sh
docker compose config --quiet
docker compose build
docker compose up -d db clamav
docker compose --profile ops run --rm migrate
# If a self-hosted Ollama model has been approved:
docker compose --profile local-ai up -d ollama
docker compose exec ollama ollama pull YOUR_APPROVED_MODEL
docker compose up -d api worker
docker compose --profile ops run --rm maintenance python manage.py production_verify
docker compose up -d web
```

No database or scanner port is exposed to the host. ClamAV downloads signatures before becoming healthy. Do not override readiness to publish unscanned files. Its signature download requires outbound access. Caddy provisions HTTPS using the configured domain and contact email. Do not publish the API port directly: it trusts the proxy's HTTPS header.

Bootstrap the first admin with a trusted issuer subject:

```sh
docker compose --profile ops run --rm maintenance python manage.py bootstrap_organization \
  --organization YOUR_ORGANIZATION --username INITIAL_ADMIN --name ADMIN_NAME \
  --email ADMIN_WORK_EMAIL --subject VERIFIED_OIDC_SUBJECT
```

The migration service alone receives the database owner credentials. `configure_runtime_role` grants normal application DML to `secureai_app`, denies modifications to immutable records, and gives it no schema ownership. Rerun this command after migrations introducing tables. The bootstrap database owner is highly privileged and must never be used by the public API. Independent security/retention role assignments remain reviewed operator actions; the UI cannot grant itself privileged roles.

## Backups and recovery

```sh
docker compose --profile ops run --rm maintenance python manage.py backup_workspace
docker compose --profile ops run --rm maintenance python manage.py verify_backup /backups/TIMESTAMP.backup
```

Backups include a custom-format PostgreSQL dump and every referenced, unpurged encrypted file version. The whole archive is separately encrypted with authenticated, ordered frames and an authenticated terminator. Keys are excluded. Application content writes are locked for the archive duration to keep the dump and blobs aligned. Plan the backup window accordingly. Temporary plaintext database dumps exist only inside the container's private `/tmp`; size that tmpfs for the database or use a private encrypted scratch volume for larger installations. A failure leaves `.partial`, never a completed `.backup`.

Copy completed archives to the **chosen off-host encrypted/immutable backup destination**. A Docker volume on the same server is not disaster recovery. Apply the approved `BACKUP_RETENTION_DAYS` in that destination only after a successful restore drill, and suspend expiry for legal holds. No backup destruction is scheduled before that destination and policy are selected. For lower RPO, choose managed PostgreSQL PITR or PostgreSQL WAL archiving; daily logical archives alone are not point-in-time recovery.

To recover, first authenticate/extract into a NEW directory on an isolated recovery host:

```sh
python manage.py verify_backup /backups/TIMESTAMP.backup --extract-to /recovery/NEW_DIRECTORY
# Point libpq PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE to a NEW empty recovery database.
pg_restore --dbname "$PGDATABASE" --no-owner --no-acl --exit-on-error /recovery/NEW_DIRECTORY/database.dump
```

Never restore over the live database. Restore the private files into the new deployment's private volume and retrieve its original DATA_ENCRYPTION_KEY from the vault. Reapply runtime grants, run migrations/readiness, verify counts and decrypt representative file hashes, check tenant/audit triggers, then run retention before opening restored access (an old backup can contain previously expired data). Only switch DNS after the organization approves the recovery verification. The local `backend/tests/postgres_check.py` automates an isolated synthetic dump/encryption/extraction/restore/hash/trigger drill on Windows PostgreSQL.

## Retention and legal holds

```sh
# Report only:
docker compose --profile ops run --rm maintenance python manage.py enforce_retention
# Apply the configured, approved policy:
docker compose --profile ops run --rm maintenance python manage.py enforce_retention --apply
```

Chats expire only when both creation and the latest message are older than `CHAT_RETENTION_DAYS`. A conversation legal hold prevents erasure. Documents are eligible only after independent deletion approval has tombstoned them and the `DELETED_FILE_RETENTION_DAYS` grace period has elapsed. A document legal hold prevents purge. Purging removes encrypted file contents and search chunks, retains immutable version metadata, and records an audit event. Published/current files are never purged merely because they are old. Interrupted file purge is retryable because tombstoned content is already inaccessible.

`AUDIT_RETENTION_DAYS` reports records due for archival. **It does not remove immutable audit records or update revisions.** Their archive destination, retention obligation, hold handling and independently approved physical destruction procedure remain TBD. Do not disable immutable triggers to implement routine cleanup. Legal-hold placement/release is a restricted operator procedure and must be audited/reviewed; it is not exposed as a public employee API.

Optional systemd units in `deployment/systemd/` run nightly backups and retention reporting. They expect the repository at `/opt/secureai`; adjust the path. Enable timers only after secrets, off-site copying, alert routing and policies are configured. Retention remains report-only until an operator intentionally enables `--apply`.

## Release verification

1. Run the PostgreSQL/ClamAV CI suite and build both containers; review image/dependency scans.
2. Run `production_verify` with runtime credentials. It must pass every check.
3. Complete real SSO login/logout, revoked-account and privileged-MFA tests on the chosen issuer.
4. Verify employee/lead/admin/steward accounts, cross-tenant denials, upload-to-publication, source revocation and saved-answer hiding through the deployed UI.
5. Complete off-host backup retrieval and restore drill. Confirm legal holds prevent retention deletion and the alert destination receives a forced failed job.
6. Record domain/TLS, chosen providers, approval references, residency, retention, RPO/RTO, incident contacts and deployment owner in the release record.

These external checks cannot be marked complete while the service choices are TBD. Health-check failure should be routed to the organization's monitoring system; no alerting account has been configured.

## References

Configuration follows [Docker Compose secrets](https://docs.docker.com/reference/compose-file/secrets/), [Caddy reverse proxy headers](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [Django proxy security settings](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header), [PostgreSQL dump/restore guidance](https://www.postgresql.org/docs/18/app-pgdump.html), [ClamAV INSTREAM protocol](https://docs.clamav.net/manual/Usage/ClamdProtocol.html), and the [Ollama chat API](https://docs.ollama.com/api/chat).
