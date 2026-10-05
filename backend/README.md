# Secure AI backend

Django/DRF API implementing the React workspace contracts in `frontend/README.md`, with authorization derived from the project documentation and `docs/Backend.docx`.

## Run locally (PowerShell, from repository root)

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe backend/manage.py migrate
backend/.venv/Scripts/python.exe backend/manage.py seed_demo --password "Choose-your-local-password"
backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

In another terminal run the document worker:

```powershell
backend/.venv/Scripts/python.exe backend/manage.py process_documents
```

Set `VITE_DEMO_MODE=false` in `frontend/.env.local`, then restart the frontend:

```powershell
cd frontend
npm run dev -- --port 5174
```

Open http://127.0.0.1:5174 and sign in. Synthetic usernames: `asha`, `ravi`, `meera`, `dev`, `admin`, `reviewer`, `security`, `retention`; all use the password supplied to `seed_demo`. Rerunning seed does not reset existing passwords. SQLite, encrypted uploads and generated development keys live in ignored `backend/var/`. Keep the encryption key with backups; losing it makes encrypted data unreadable.

## Feature layout

| React feature | Backend module |
| --- | --- |
| Session/sign-in | `apps/identity` |
| Dashboard | `apps/dashboard` |
| Projects | `apps/projects` |
| Work updates | `apps/work_updates` |
| Documents | `apps/documents` |
| People/settings | `apps/people` |
| Assistant | `apps/assistant` |
| Search | `apps/search` |
| Notifications | `apps/notifications` |
| Administration/approvals | `apps/administration` |
| Audit | `apps/audit` |

Shared policy is in `apps/policy`; validation, concurrency, pagination, throttling and database integrity guards are in `apps/core`. Routes are ordered in `config/urls.py`, under `/api/v1`, without trailing slashes.

## API behavior

- Session cookies and CSRF protect mutations. `/auth/csrf` initializes the CSRF cookie; `/me` returns fresh capabilities. Session versions invalidate deactivated users immediately.
- Unknown, cross-organization and inaccessible resources return the same 404 response. Admin roles do not confer content access.
- Mutations of versioned content require `If-Match` or a body `version`. Conflicts return 409. Optional `Idempotency-Key` prevents replay of standard transactional mutations; repeated keys return 409 rather than replaying private response bodies.
- Lists return `results` and a signed `next` cursor, bound to the reader and filters. They do not disclose hidden totals.
- Upload TXT, PDF or DOCX multipart files; the worker scans and extracts before publication. A new file version suspends publication. Downloads reauthorize access and decrypt private storage; no public media directory exists.
- Membership changes require independent approval. Self-affecting changes require separate admin and security reviewers. Document widening requires its independent project steward; deletion requires a retention steward and respects legal holds.
- P2 personal fields and file blobs are encrypted. P2 fields never enter search or assistant evidence. Assistant responses are buffered and sources rechecked after generation and when reopening saved conversations.
- Audit, file versions and update revisions are protected against modification/deletion by database triggers. Tenant foreign-key checks also operate at the database layer.

## Identity and invitations

Production sign-in uses Authlib OIDC authorization code flow with PKCE, state and nonce verification. Configure one trusted issuer and register `/api/v1/auth/callback` as the redirect URI on the same origin as the frontend. Privileged users need an accepted MFA `amr` claim.

Administrators create invitations; the API returns a link for the administrator to distribute. No email is sent. Acceptance requires OIDC and a verified email matching the unexpired invitation. It creates a basic account without memberships or administrative roles. Existing accounts cannot be linked by email through invitations; an operator must provision their trusted issuer/subject directly. Local password sign-in is only enabled in debug synthetic mode.

An operator can initialize a new production organization with `manage.py bootstrap_organization --organization NAME --username USERNAME --name NAME --email EMAIL --subject VERIFIED_OIDC_SUBJECT`. Configure the issuer first and obtain the subject from your identity administrator. This command refuses existing organizations and identities. Subsequent privileged role/steward provisioning needs your independently reviewed operator procedure; the public API cannot self-elevate accounts.

## Verification

```powershell
backend/.venv/Scripts/python.exe backend/manage.py check
backend/.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
backend/.venv/Scripts/python.exe backend/manage.py test tests
```

The acceptance suite covers the T01–T22 scenarios through grouped tests: tenant isolation, drafts, live memberships, grant intersections, widening, dual review, owner-only P2, injection-resistant evidence selection, current-version citations, revocation during generation, CSRF, scanner quarantine and audit immutability.

## Deployment limits

Production deployment configuration, operational commands, verification and remaining TBD decisions are documented in [deployment/README.md](../deployment/README.md). The production settings now require explicit SSO/provider approval and retention configuration; development defaults cannot silently become production defaults.

This is a runnable implementation for synthetic evaluation, not a declaration of production readiness. The default scanner only detects a test signature; real deployments must use reachable ClamAV and an isolated document worker. The default assistant extracts authorized excerpts locally; Ollama is optional and disabled without explicit provider approval. Keyword quarantine is a heuristic, not complete sensitive-document classification.

Production settings require PostgreSQL, explicit secrets, HTTPS and non-synthetic mode. Serve the frontend and `/api` behind the same trusted HTTPS origin. Configure OIDC, malware scanning, encryption-key custody, provider/data-processing approval, backup/restore, retention and privileged operator procedures before using employee data. The suite and an encrypted backup/restore drill have now passed against an isolated PostgreSQL 18 cluster; repeat verification on the selected deployment. Tenant-wide transaction locks intentionally prioritize revocation correctness over throughput. File extraction runs in a timed child process; OS/container resource and network isolation remain deployment responsibilities.

Deletion approvals create policy-enforced tombstones. `enforce_retention` supports chat expiration and physical purging of approved, expired file tombstones, with legal holds and an explicit apply option. Retention durations, legal-hold release, audit archival and backup expiry still require the organization's approved operational policy.

