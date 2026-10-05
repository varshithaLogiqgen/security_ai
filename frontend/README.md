# SecureAI frontend

React + TypeScript + Vite workspace built from `PROJECT_CONTEXT.md`, `docs/frontend.docx`, and authoritative specs 03, 04, and 06. The Django project is currently scaffolding with no functioning feature endpoints. This frontend provides a synthetic interaction demo and a separate HTTP adapter; live authentication, authorization, scanning, retrieval, approvals, and persistence still require backend implementation.

## Run

```powershell
cd D:\security_AI\frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open the URL printed by Vite. Demo mode is explicitly enabled by `VITE_DEMO_MODE=true`; it uses fictional records and memory-only changes. Refresh resets the demo. No live AI is called. Uploads are not scanned; only use synthetic files. Admin capabilities are absent from the employee demo, so admin routes correctly show a generic unavailable page. Administration UI is implemented against the proposed API below, not a simulated privilege picker.

For real integration, set `VITE_DEMO_MODE=false` and configure `VITE_API_BASE_URL=/api/v1`. Vite proxies `/api` to `http://127.0.0.1:8000`. Deploy frontend and API on the same origin, with SPA fallback to `index.html`. The default without environment configuration is live mode, which fails closed when `/me` is unavailable. Do not put secrets in Vite environment variables.

## Implemented screens

- Role dashboards for employees, team leads, organization admins and security reviewers, backed by `/dashboard` with exact authorized counts, date/event filters and quick actions. Multiple-role users can switch to their personal workspace. Leads see explicit blockers only on published lead-visible updates. Security configuration is read-only and never contains secrets.
- The dashboard banner names the signed-in account and current view. An admin on Personal workspace can use “Open organization admin dashboard” to return to the organization view. Local direct links: `http://127.0.0.1:5174/?view=admin` for admins and `http://127.0.0.1:5174/?view=employee` for personal work. Unauthorized view choices are rejected by the API.
- Collapsible desktop sidebar, mobile navigation drawer, account sign-in/out and session-expired state.
- Projects and project members/documents; employee directory and work profiles.
- Private drafts, revisions, publish/sharing confirmation, team-lead view from server assignments, deletion requests.
- Document library, staged upload, status display, classification, member grants, widening approval request, replacement version, authorized download and removal request.
- Owner-only personal profile fields fetched only from the personal settings tab.
- Protected search, notifications, read-only chat, saved conversations, citations and access-changed regeneration.
- Capability-gated organization invitations/deactivation, team/project creation, access proposals, independent review, and audit metadata views.
- Loading, empty, error, conflict, and inaccessible states; cursor pagination for main collections; no raw HTML or Markdown execution.

## Proposed backend contract (integration work remains)

All paths are relative to `/api/v1`. Types in `src/types/index.ts` describe response fields; lists return `{ results: T[], next: string | null }` where `next` is an opaque cursor. The API must filter results before returning counts, fields, and cursors. Client capability checks only control navigation; the backend must authorize every read and mutation. No user/organization IDs are sent as proof of identity.

| Endpoint | Method / purpose |
| --- | --- |
| `/me` | GET `Session`, including current teams, led teams and capability hints |
| `/auth/login`, `/auth/logout` | GET SSO redirect; POST end session and invalidate cookie |
| `/profiles`, `/profiles/:id` | GET work profiles; PATCH allowlisted bio for self |
| `/profiles/:id/personal` | Owner-only GET/PATCH `{ phone, address, emergency_contact }` |
| `/projects`, `/projects/:id`, `/projects/:id/documents` | Scoped GET collections/details |
| `/updates`, `/updates/:id` | GET/POST draft; GET/PATCH revision; DELETE draft |
| `/updates/:id/publish`, `/updates/:id/request-deletion` | POST publish or retention request |
| `/teams/:id/updates` | GET only currently authorized lead-visible updates |
| `/documents`, `/documents/:id` | GET list/detail; POST multipart `{ file, title, project_id }` staging |
| `/documents/:id/publish`, `/documents/:id/access` | POST publish / PATCH access `{ classification, grants, version }` |
| `/documents/:id/versions` | POST multipart file with `If-Match`; preserve classification/grants |
| `/documents/:id/download`, `/documents/:id/request-deletion` | GET fresh-authorized bytes / POST retention request |
| `/search` | POST `{ query, cursor }`, returns authorized typed result list |
| `/conversations`, `/conversations/:id` | GET/POST owner-only collection; GET revalidated messages / DELETE |
| `/conversations/:id/messages` | POST `{ question }`, return full conversation after final source validation |
| `/notifications` | GET authorized notification messages, no hidden resource metadata |
| `/admin/users`, `/admin/invitations`, `/admin/users/:id/deactivate` | GET users; POST invitation/deactivation |
| `/admin/teams`, `/admin/projects`, `/admin/access-requests` | GET searchable structure options; POST structure / time-bounded access proposals |
| `/admin/approvals`, `/admin/approvals/:id/review` | GET requests; POST independent review |
| `/security/audit` | GET permitted audit metadata; no source text |

The backend must provide a readable Django CSRF cookie and an HttpOnly session cookie, enforce origin/CSRF validation, and respond with generic 404 for both unknown and inaccessible resources. The fetch adapter includes credentials and CSRF, disables HTTP caching, handles 401 session clearing and 409 conflicts, and sends version preconditions and idempotency keys. Production headers should include `Cache-Control: no-store` on sensitive responses and a deployment-specific CSP.

Collection filters use `q`, `cursor`, and, where applicable, `status`, `classification`, and `project_id`. Admin selectors show server-authorized names and submit their identifiers; an access proposal includes `target_user_id`, `action`, `scope_id`, `operation` (`assign` or `revoke`), `expires_at`, and `reason`. The server must validate these lookups independently and interpret the configured organization timezone for the date/time input.

Document processing/virus scanning, accepted file limits and retention are backend governance decisions. The UI currently proposes PDF/DOCX/TXT with a 10 MB client limit; this is not malware validation. The server must return processing/failed/quarantined states, enforce actual limits and require completed validation before publication. Publishing, approvals, grants, downloads, and version transitions must be transactional on the server. Saved messages with revoked sources must return `state: access_changed` and omit answer/citation content entirely.

## Decisions from conflicting plans

- Follow specs 01–08 over Word proposals: no tasks or update-review queue; updates belong to teams; only private/lead-visible update visibility and project/restricted document classification.
- Full-page AI, buffered responses, owner-only history; SSO handles password reset.
- Light navy design, all modules responsive, synthetic employee Asha; no frontend privilege selector.
- Fonts are bundled locally. The application does not request Google Fonts or other runtime font services.
- No persistent browser cache. TanStack Query uses zero stale/garbage-collection time and fresh reads on focus/mount. Protected query content is hidden while checking access and on errors. Mutations invalidate queries; expiry/logout cancels and clears cached data. This does not replace server revocation checks or a production security review.

## Validate

```powershell
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

Unit tests cover credential/CSRF transport, generic errors, session expiry, revision conflicts, personal-field isolation and saved-answer invalidation. Browser tests cover desktop/mobile layout, updates, uploads, citations, unknown IDs, profile edits and sign-out. These tests exercise synthetic UI behavior; they do not prove backend authorization or satisfy the full T01–T22 release gate. Real employee data remains blocked on backend implementation and the governance approvals in the project context.

Library references: [Vite guide](https://vite.dev/guide/) and [TanStack Query documentation](https://tanstack.com/query/latest/docs/framework/react).
