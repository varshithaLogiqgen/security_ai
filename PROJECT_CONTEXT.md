# PROJECT_CONTEXT.md — Secure AI Information Platform

> Single-source context for anyone (human or AI coding agent) working on this project.
> Compiled 3 October 2026 from 12 project documents (listed in §16). Every section names the documents it comes from.
> **Status:** design/review stage. No code exists yet. All documents are review baselines or drafts, so none of this has been implemented or proven.

---

## 1. What this project is

*Source: 01 Product Requirements*

A secure internal platform where employees:

1. Record **daily work updates**
2. Share **project documents**
3. Look up **employee profiles** (a work directory)
4. Ask a **read-only AI assistant** questions and get answers **with citations**

**The core promise:** a signed-in person can browse, search, download, or ask the AI about **only what they are currently allowed to read**. The same access decision applies everywhere: pages, APIs, direct links, search, citations, downloads, and AI retrieval.

**Pilot success:** every acceptance case in doc 08 passes using synthetic users, with **zero cross-organization or cross-project disclosures**.

This project is separate from the LMS product (JBLUE / "JJ LMS" in doc 01).

---

## 2. Source-of-truth order (read this first)

The Word plans (Frontend, Backend, Database, AI) were written after the eight spec docs, and **they disagree with the specs in several places** (see §14). Until someone formally revises the specs, use this order:

| Priority | Document | Role |
|---|---|---|
| 1 | **03 Authorization Specification** | Final word on who can see or do what |
| 2 | 01, 02, 04, 05, 06, 07, 08 | Product, data, flows, schema, API, security, and tests |
| 3 | Backend, Database, AI, and Frontend plans (.docx) | Implementation proposals: stack, folder layout, phases |

**Rule:** if a Word plan conflicts with docs 01–08, follow 01–08 and log the conflict as a decision (§15).

---

## 3. Non-negotiable rules

*Sources: 01, 03, 06, 07 (repeated in all four Word plans)*

1. **Default deny.** Nothing is allowed unless a policy rule explicitly allows it. Missing attributes or a policy or identity failure means **deny (fail closed)**.
2. **Server-side authorization only.** User ID and organization always come from the verified session, **never from the request body**. Client IDs are lookups, not proof of access.
3. **Live checks.** Never authorize from stale JWT roles, cached labels, or search-index metadata. Recheck current membership, lead assignment, and grants on every request.
4. **Admin is not a content wildcard.** Organization Admin and Security Admin titles grant **no** access to private updates, documents, or personal fields.
5. **No existence leaks.** Inaccessible and unknown IDs get the same generic `404`. Titles, snippets, counts, pagination, autocomplete, and notifications must not reveal hidden items.
6. **The AI is read-only.** It cannot write, administer access, or fetch unfiltered data. The **retrieval service is the security boundary**; the system prompt is not.
7. **Filter before the model.** Only authorized excerpts ever reach the LLM. Never send everything and ask the model to ignore restricted parts.
8. **Uploaded content is untrusted.** Document text cannot grant access, set attributes, trigger tools, or change rules (prompt injection, test T17).
9. **Recheck at every disclosure point:** before AI context, before returning the answer, on citation click, and on chat reopen.
10. **Revocation commits first.** Once the database change commits, new reads are denied, even while index cleanup is still pending.
11. **No public or long-lived file links.** Every download is authorized fresh.
12. **No secrets in the browser.** No model keys, service-role credentials, or direct storage/index access from the frontend.
13. **Separation of duties.** No self-assignment, self-approval, or self-widening of access.
14. **Minimal logging.** Audit logs record IDs and decisions, never raw document bodies, personal fields, or full prompts.

---

## 4. Pilot scope

*Sources: 01, 02, 07*

**In v1**
- One organization, but `organization_id` is mandatory on every protected entity.
- Work updates, project documents, employee profiles (P1/P2), and read-only AI Q&A with citations.
- Supporting features: search, administration, and security/audit review.
- Synthetic pilot users first: Asha, Ravi, Meera, Dev.

**Out of v1**
- Salary, payroll, national IDs, performance reviews, medical data, and HR cases (accidental uploads are **quarantined**, not indexed or sent to the AI)
- AI write actions, autonomous tasks, multi-agent setups, fine-tuning, and voice
- External integrations
- Cross-project or cross-organization document grants
- Public document links
- Sharing work updates between employees
- Emergency or "break-glass" access (there is no hidden override)

**Release gate:** no real employee data until every governance decision in doc 07 is approved (§15).

---

## 5. Users and relationships

*Sources: 01, 03*

| Relationship | What it means |
|---|---|
| Employee | Member of one or more teams or projects |
| Team lead | **Currently** assigned lead of a team (time-bounded) |
| Organization admin | Manages users, teams, projects, memberships, and leads, but does **not** get content access |
| Security / system admin | Reviews audit metadata and security configuration, but does **not** get content access |
| Project steward | Named per project. Approves widening a document from restricted to project |

- One user can hold several relationships at once.
- Memberships, lead assignments, and grants are **time-bounded facts** (start, end, revoked), not permanent privileges.

---

## 6. Data categories

*Source: 02 Information Inventory*

These seven categories are the complete v1 list. Adding a category requires updates to the catalog, policy, API, UI, and negative tests **before** any data is ingested.

| Code | Data | Who can see it |
|---|---|---|
| **W1** | Work update: team, date, body, visibility, status | Draft: owner only. Published: `private` (owner only) or `lead_visible` (owner + current team lead) |
| **D1** | Document: file, title, project, uploader, version, classification, grants, chunks | Unpublished: uploader only. Then `project` (current members) or `restricted` (current members **with** a named grant) |
| **P1** | Work profile: name, work email, job title, directory team | Same-organization directory. Can be searched and cited by the AI |
| **P2** | Personal profile: personal phone, address, emergency contact | **Owner only.** Excluded from search and AI, **even for the owner** |
| **A1** | Structure: teams, projects, memberships, leads, roles | Minimal directory view, plus a management view for admins |
| **C1** | AI conversations: question, answer, source/version references | Owner only, with every source rechecked |
| **S1** | Audit: actor, action, target, decision, reason, policy version | Security staff. Org admins see only their own admin actions |

**Required metadata on every protected record:** immutable ID, `organization_id`, creator, timestamps, lifecycle state, and an audit link. Chunks carry document and version IDs and are **never** readable on their own.

**Retention for every category:** still to be set by the organization (open decision).

---

## 7. Authorization rules

*Source: 03 Authorization Specification. This is the core of the system.*

**Decision contract**
```
authorize(subject, action, resource, context)
  -> { allow, permitted_fields, reason_code, policy_version }
```
One shared policy service decides for: list and detail APIs, counts, thumbnails, extracted text, search snippets, AI context, citation metadata, and downloads.

| Rule | Allowed | Denied example |
|---|---|---|
| W1-C create update | Active user who is currently in the target team (same organization). Creates it as their own draft | Other team; inactive user |
| W1-R read update | Owner, **or** current lead of that team when the update is published **and** `lead_visible` | Teammate; former lead; private update |
| W1-E edit/visibility | Owner while active. Edits after publishing create a revision and an audit entry | A lead editing someone else's update |
| W1-D delete | Owner deletes a draft. Published updates go through a soft-delete request and the retention workflow | Silent hard delete |
| D1-U upload | Active member of the target project. New uploads are unpublished and visible to the uploader only | Other project |
| D1-R read/search/download/AI | `project` documents: current member. `restricted` documents: current member **plus** an active named grant. The uploader also needs current membership | Expired grant; removed member; admin by title alone |
| D1-G grant/revoke | Uploader (still a current member) grants named **current members of the same project**. Audited | Outsider; cross-project |
| D1-C classify/publish | Uploader sets the classification at publish time and can **narrow** it. **Widening** needs approval from a separate steward | Self-approved widening |
| D1-V new version | Uploader (still a member) stages a replacement. Classification and grants are kept | Another member overwriting it |
| D1-X delete | Uploader requests deletion, a retention steward reviews it, then the document is tombstoned | Silent erase |
| P1 | Same-organization active users read approved fields. Owner edits self-service fields. Org admin edits managed fields | Self-assigning a role or team |
| P2 | Owner only, through the profile page | A lead or admin reading a personal phone number |
| A1 | Org admin manages structure. A separate security admin handles security configuration | Admin granting themselves content access |
| C1 | Conversation owner. On reopen, every source is rechecked. If any source is lost, the answer is **hidden** and regeneration is offered | Former member viewing an old answer |
| S1 | Security staff see security events. Org admin sees their own admin-action metadata | Full content in the log |

**Admin separation:** an org admin cannot add themselves to a project, make themselves a lead, or approve their own elevation. Changes that affect the requesting admin need a **second org admin plus a security reviewer**. Approval records include requester, approver, reason, scope, expiry, and outcome.

**Worked example (doc 03):** Meera reads Asha's Payments update only while Meera currently leads Payments **and** the update is `lead_visible`. If Asha switches it to `private`, Meera's next read is denied. Dev reads a project-classified Atlas document only while he is in Atlas. A restricted Atlas document additionally needs Asha's grant to him.

---

## 8. Key flows

*Sources: 02, 04, 06*

**Work update:** member selects their team → private draft → chooses `private` or `lead_visible` → publishes → can change visibility later (takes effect on the next read and next AI request) → editing creates a revision; drafts can be deleted; published updates go through a removal request.

**Document lifecycle:**
```
Upload intent (members only) → type/size/malware validation → private storage (unpublished)
→ text extraction in an isolated worker → link chunks to the version
→ uploader classifies (+ picks grantees if restricted) → publish → index
→ replace / narrow / delete (blocks new reads immediately; index cleanup runs async)
```
- Narrowing `project` to `restricted` suspends publication until grantees are chosen.
- When a new version becomes current, old versions drop out of search and AI.

**AI question:** see §10.

**Membership change:** admin proposes → independent approver (if it affects the admin) → commit and audit → all new reads use the new state → the user sees a generic "no access" page.

---

## 9. Tech stack (proposed, to be confirmed)

*Sources: Backend plan, Database plan, AI plan, Frontend plan*

| Layer | Choice |
|---|---|
| Backend | **Django + Django REST Framework**, built as a modular monolith with versioned APIs (`/api/v1/...`) |
| Database | **PostgreSQL**. UUID primary keys, `timestamptz`, a custom Django user model, and optional row-level security as a second layer |
| Authorization | Shared Django policy service (`apps/authorization`) |
| Authentication | Organization-managed identity provider with MFA for admins (**provider not chosen**) |
| File storage | Private object storage (**provider not chosen**) |
| Background jobs | Worker/task queue for scanning, extraction, and indexing (**mechanism not chosen**) |
| Search | **PostgreSQL full-text search** (GIN index on a tsvector column) first. Vectors only if evaluation justifies them |
| LLM | One configurable provider behind an adapter (hosted API, or local as an alternative). **No external provider until data terms are approved** |
| Frontend | **React + TypeScript + Vite**, Tailwind or CSS modules, TanStack Query, React Hook Form plus schema validation, React Router, Lucide icons, Axios/Fetch through a central API client |
| Testing | pytest / Django tests (backend). Vitest, React Testing Library, and Playwright (frontend and end-to-end) |

### Backend layout (Database plan §7)
```
backend/
├── config/            settings.py, urls.py, asgi.py
├── apps/
│   ├── identity/  organizations/  authorization/  teams/  projects/
│   ├── work_updates/  employee_profiles/  documents/  search/
│   ├── ai_assistant/  audit/
├── manage.py
└── requirements.txt
```
Approval workflows may need their own app (for example `apps/approvals/`). The Database plan doesn't include one.

### Frontend layout (Frontend plan §5)
```
frontend/src/
├── app/          router.tsx, providers.tsx, queryClient.ts
├── components/   layout/ ui/ feedback/ data-display/
├── features/     auth/ dashboard/ projects/ work-updates/ people/ documents/
│                 assistant/ notifications/ administration/
├── services/     api/ auth/
├── hooks/ types/ utils/ styles/
└── main.tsx
```

---

## 10. AI retrieval pipeline

*Sources: 06, AI Component plan*

1. Authenticate and load the user's **current** attributes from the server.
2. Treat the question as a search request only, with no database or tool authority.
3. Find candidate records and chunks within organization and scope filters (prefiltering is allowed for speed).
4. **Reauthorize each source, version, and field** against live policy. Strip masked fields and unauthorized snippets.
5. Build a bounded context with stable source, version, and citation locators. Mark the text as **untrusted evidence**.
6. A read-only model answers from that evidence only. If evidence is insufficient, it returns a **neutral "insufficient information"** response and never hints that restricted items exist. If sources conflict, it names the conflict.
7. Check that citations point only to supplied, authorized sources, then **recheck access right before returning**. Store the answer, source references, and policy version. Log source IDs, not content.
8. On citation click or chat reopen, recheck. If access was lost, **hide the answer** (don't show old source titles) and offer to regenerate.

**Other v1 AI rules**
- **Buffer, don't stream.** Validate the full answer before showing it.
- No cross-user answer cache. Any per-user cache is invalidated on changes to membership, classification, grants, or source versions.
- Rate-limit search and AI to limit enumeration and cost.
- Starting chunk settings (to tune later): 500–800 tokens with 80–120 tokens of overlap. Metadata on each chunk: document ID, version ID, page or section.
- Initial file formats under consideration: PDF, DOCX, and TXT.
- AI components: API layer, authorization adapter, ingestion, chunking and indexing, retrieval engine, prompt builder, LLM adapter (**kept separate so the provider can be swapped**), and citation validator.
- Track these metrics: request count, retrieval and LLM latency, tokens and cost, empty-retrieval rate, citation failures, denials, ingestion failures, and provider errors.

---

## 11. Data model

*Source: 05 is authoritative. The Database plan adds physical details.*

**Tables from 05**
`organizations`, `users`, `user_roles` (time-bounded), `teams`, `team_memberships` (start/end), `team_leads` (start/end), `projects` (with `steward_user_id`), `project_memberships` (start/end), `work_updates` (owner, team, work_date, status, visibility, body, version), `update_revisions`, `profiles_work`, `profiles_personal` (encrypted), `documents`, `document_versions` (immutable; storage_key, hash, mime, bytes, scan_status), `document_grants` (valid_from/to, revoked_at), `document_chunks`, `conversations`, `messages`, `answer_sources` (source_type, source_id, version_id, citation_locator), `approval_requests`, `audit_events` (append-only, includes policy_version).

**Useful additions from the Database plan:** `document_processing_jobs`, `security_events`, an index list (§5 of that plan), UUID and timestamp conventions, and a note that soft deletion is **not** an access-control mechanism.

**Integrity rules**
- Organization-scoped composite foreign keys or validating triggers, so no join can cross organizations.
- `(document_id, version_no)` is unique.
- No duplicate **active** grant for the same document and grantee.
- Enum constraints on state transitions.
- Separate low-privilege database roles for the app and for indexing jobs.
- Search indexes are **never** the authorization source.

---

## 12. API surface

*Sources: 06, Backend plan, AI plan. Route names are illustrative.*

| Route | Purpose |
|---|---|
| `GET /api/v1/me`, `GET/PATCH /api/v1/profiles/{id}` | Profile with field-level P1/P2 policy |
| `/api/v1/updates`, `/api/v1/updates/{id}` | Create, edit, publish, change visibility, delete draft, request deletion |
| `/api/v1/teams/{id}/updates` | Lead view (per-record W1-R check, no leaking counts) |
| `/api/v1/projects`, `/api/v1/projects/{id}/documents` | List and upload |
| `/api/v1/documents/{id}` | Metadata, classify, grant/revoke, new version, request delete |
| `/api/v1/documents/{id}/download` | Streamed file, fresh check on every request |
| `POST /api/v1/search` | Query plus cursor, with per-result live authorization |
| `/api/v1/conversations`, `/api/v1/conversations/{id}/messages` | Ask questions and read answers |
| `/api/v1/admin/*`, `/api/v1/security/audit` | Admin actions and audit log |

- **Error contract:** `401` no session · `404` generic for unknown or inaccessible · `409` version conflict · neutral insufficient-evidence response for the AI.
- **Request rules:** cursor pagination, version preconditions on edits, idempotent uploads and approvals, allowlisted serializers.

---

## 13. Frontend summary

*Sources: 04, Frontend plan*

- **Look and feel:** modern, minimal, light theme. Tokens: primary `#294B83`, accent `#5276B8`, page `#F6F8FB`, surface `#FFFFFF`, text `#1F2937`, muted `#64748B`.
- **Navigation:** Overview, Projects, Work updates, People, Documents, AI Assistant, Notifications, Settings. Admin sections appear only when the user has permission. The sidebar collapses on desktop and becomes a drawer on mobile.
- **Screens (doc 04):** Sign-in, Dashboard, My updates, Team updates, Projects/Documents, Search, AI chat, My profile (P1 and P2 shown separately), Org admin, Security admin.
- **Rules**
  - Route guards improve the experience but are **not** security. The backend decides.
  - Never fetch fields just to hide them.
  - Clear the TanStack Query cache on logout or session expiry.
  - No sensitive data in browser storage, URLs, analytics, or console.
  - Sanitize AI-generated Markdown before rendering.
  - Clear visibility and classification labels, a sharing preview with confirmation, full keyboard and screen-reader support, and no color-only status indicators.
- **Access-lost state:** show a plain explanation when previously visible chat content is now hidden.

---

## 14. Conflicts between the Word plans and the specs

These must be resolved before writing migrations or screens. The default resolution follows §2 (the spec wins).

| # | Topic | Specs (01–08) say | Word plans say | Default |
|---|---|---|---|---|
| 1 | Work-update review | No approval workflow. Only `private` / `lead_visible` | Frontend and DB plans add a review queue, statuses `submitted/approved/needs_changes`, `/reviews`, and `work_update_reviews` | **No review workflow in v1** unless the product owner adds it |
| 2 | What an update belongs to | `team_id` | DB plan uses `project_id` plus `work_update_entries` with durations | **Team-scoped** |
| 3 | Lead model | `team_leads` table with start/end dates | `teams.lead_user_id` (one column, no history) | **Time-bounded `team_leads`** |
| 4 | Membership history | Start/end/revoked intervals, history kept | `status` column with unique `(team_id, user_id)` | Intervals with a **partial unique index on active rows** |
| 5 | Classifications | `project`, `restricted` only | DB and AI plans add `organization`-wide documents | **Two values only** |
| 6 | Grants | valid_from/to, revoked_at, no duplicate active grant | `permission`, `expires_at`, no revoked_at | Spec fields |
| 7 | Role model | Relationship-based. Admin is never a content wildcard | Generic `roles` / `permissions` / `role_permissions` tables. AI plan says "lead/**admin**" can read updates | Relationship-based. **Admins cannot read updates** |
| 8 | P2 fields | Personal phone, address, emergency contact (encrypted) | Phone, **personal_email**, emergency contact. P1 includes "department" | Spec fields. Confirm with privacy/HR owner |
| 9 | Citations table | `answer_sources` covers W1, D1, and P1 sources, with version_id and locator | `message_sources` links only document chunks and stores `quoted_text` | Spec design. Avoid storing quoted text (it leaks after access loss) |
| 10 | Missing tables | `approval_requests`, `update_revisions`, project steward, `policy_version` on audit | Missing from the DB plan | Add them |
| 11 | Chat visibility | Owner only | Frontend route: "owner **or permitted user**" | **Owner only** |
| 12 | Streaming | Buffer and validate before display | Frontend: "streaming or loading" | **Buffer** in v1 |
| 13 | After access loss | Decided: hide the answer and offer regeneration | AI plan lists it as an open question | **Hide and offer regeneration** |
| 14 | Password reset | Organization-managed identity provider | Frontend has forgot-password screens | Let the identity provider handle it |
| 15 | Tasks / "Assigned work" | Not in scope | Dashboard and Projects mention tasks | Out of v1 |
| 16 | API prefix | `/updates`, `/conversations` | Backend uses `/api/v1/...`. AI plan uses `/api/ai/...` | **One prefix: `/api/v1/`** |

---

## 15. Open decisions

*Sources: 05, 07, and the open-decision sections of each Word plan*

**Must be approved before real employee data (doc 07)**
- [ ] AI provider and data location (P2 never goes to the AI)
- [ ] Chat retention (no indefinite default)
- [ ] Retention for updates, documents, and versions, plus legal-hold exceptions
- [ ] Audit retention, reader list, and immutable storage
- [ ] Named independent admin and steward approvers, with cover for absences
- [ ] Session and download-link expiry, plus a revocation time target (SLO)
- [ ] File formats, size limits, scanning, and the quarantine process
- [ ] Incident owner and response process

**Implementation choices**
- [ ] Identity provider · object storage · task queue
- [ ] One update per day or several (unique constraint depends on it)
- [ ] Whether users can see version history
- [ ] Search on P1 fields beyond name, email, title, and team
- [ ] Question and context size limits · usage-logging retention · English-only or multilingual
- [ ] UI: light-only theme? Full-page chat or side panel? Mobile scope? Mockups first?
- [ ] Every conflict in §14

---

## 16. Build order

*Sources: 01 (slices), Backend, Database, AI, and Frontend plans (phases), merged*

| # | Slice | Done when |
|---|---|---|
| 0 | Foundation: Django project, PostgreSQL, custom user model, UUIDs, API versioning, error contract. React shell, design tokens, API client | App runs; placeholder pages render |
| 1 | **Identity + policy engine** (organizations, users, roles, memberships, leads, `authorize()`) | Policy unit tests from doc 03 pass; tenant isolation (T16) and fail-closed (T22) pass |
| 2 | Admin structure: teams, projects, invitations, approvals, separation of duties | T13 and T14 pass |
| 3 | Profiles (P1/P2) + **work updates** | T01–T05 and T15 (UI part) pass |
| 4 | **Documents + private storage**: upload, scan, versions, classification, grants, downloads | T06–T12, T18, and T19 pass |
| 5 | **Protected search** | No leaks through counts, snippets, or pagination |
| 6 | **Read-only AI** + conversations + citations | T15, T17, and T20 pass; revocation during an AI request handled |
| 7 | Revocation hardening, audit views, security review, monitoring | T21 passes; the full doc 08 suite passes; governance approvals recorded |

---

## 17. Test fixture and acceptance cases

*Source: 08 Acceptance and Security Test Plan*

**Fixture**
- One organization, plus a second organization for isolation tests.
- **Payments** team: Asha and Ravi are members; Meera is the current lead. Dev is on another team.
- **Atlas** project: Asha and Dev are members; Ravi is not.
- Data: Asha's private and lead-visible updates; one project-classified Atlas document; one restricted Atlas document (granted to Asha, and to Meera only if she joins Atlas); a personal phone field.
- **A unique canary phrase in every source**, used to detect leaks.

**Cases T01–T22**

| ID | Scenario |
|---|---|
| T01–T05 | Work updates: drafts, private vs lead-visible, visibility change, losing the lead role |
| T06–T12 | Documents: project vs restricted, grants, leaving Atlas, grants to outsiders, narrowing, unapproved widening |
| T13–T14 | Admins can't read content by role, and can't assign or approve themselves |
| T15 | P2 never visible to others or the AI (even for the owner) |
| T16 | Tampered IDs or organization IDs denied uniformly |
| T17 | Prompt injection inside a document |
| T18–T19 | Deleted or replaced versions; copied links |
| T20 | No accessible sources gives a neutral answer |
| T21 | Audit visibility |
| T22 | Fail closed |

Run each case through **every path**: UI, direct API, search, download, AI question, citation open, and saved-chat reopen. Also test:
- concurrent revocation during an AI request
- malformed IDs and bulk enumeration
- pagination and count leaks
- wrong-tenant joins
- cache or index lag
- field serialization

**Release:** all critical cases pass, no high-severity leaks remain, governance decisions are recorded, and an owner signs off.

---

## 18. Source documents

| File | Type |
|---|---|
| 01_Product_Requirements_and_MVP_Scope.md | Spec baseline (28 Sep 2026) |
| 02_Information_Inventory_and_Classification.md | Spec baseline |
| 03_Authorization_Specification.md | Spec baseline (**highest authority**) |
| 04_User_Flows_and_Screen_Requirements.md | Spec baseline |
| 05_Data_Model_and_Database_Design.md | Logical schema |
| 06_API_and_AI_Retrieval_Specification.md | API contract (two identical copies were supplied) |
| 07_Security_and_Data_Handling_Plan.md | Security controls and governance decisions |
| 08_Acceptance_and_Security_Test_Plan.md | Test scenarios T01–T22 |
| Secure_AI_Information_Platform_Backend_Plan.docx | Implementation draft |
| Secure_AI_Information_Platform_Database_Design_Plan.docx | Implementation draft |
| Secure_AI_Information_Platform_AI_Component_Design_Plan.docx | Implementation draft |
| frontend.docx | Implementation draft (includes UI reference images) |
