# Secure AI Information Platform — Information Inventory and Classification v1

Status: Review baseline. Source: uploaded information matrix. Classification is an access input, never an authorization decision by itself.

| Code | Record and sensitive fields | Owner/steward | Default and permitted scope | Retention decision |
|---|---|---|---|---|
| W1 | Work update: team, date, body, visibility, status | Author | Draft private; published private or lead-visible at author's choice | Organization to set |
| D1 | Document: private file, title, project, uploader, version, classification, grants, indexed passages | Uploader; project steward for lifecycle | Unpublished uploader-only; project or restricted after publication | Organization to set |
| P1 | Work profile: name, work email, job title, approved directory team | Employee; organization admin for managed fields | Same-organization directory | Organization to set |
| P2 | Personal profile: personal phone, address, emergency contact | Employee | Owner-only | Organization to set |
| A1 | Teams, projects, memberships, lead assignments, roles and status | Organization admin | Minimum directory view; management view for authorized admins | Organization to set |
| C1 | Question, answer, source/version references | Conversation owner | Owner-only, subject to source recheck | Organization to set |
| S1 | Actor, action, target ID, decision, timestamp, reason, policy/version | Security function | Authorized security staff; limited admin-action metadata to organization admins | Organization to set |

## Required metadata

All protected records have immutable ID, `organization_id`, creator, timestamps, lifecycle state, and audit linkage. W1 has `owner_id`, `team_id`, and visibility. D1 has `project_id`, `uploader_id`, classification, storage key, version, and active grants. Chunks carry source document/version IDs but never become independent broadly readable records. Memberships and grants have start/end/revocation timestamps and actor attribution.

## Classification transitions

- A new upload stays unpublished and uploader-only until classified.
- `project` exposes the approved version to current project members. `restricted` requires both current project membership and a named active grant, except uploader access while uploader remains a current member; on membership loss access stops.
- The uploader may narrow `project` to `restricted` immediately; the system suspends publication until specific grants are chosen and updates search availability. Widening `restricted` to `project` requires an approved project-steward workflow and audit; self-approval is prohibited.
- Cross-organization and cross-project grants are disallowed in v1. A project's administrator may assign membership but obtains no content access through administration alone.
- Personal fields are excluded from general search and AI in v1, including the owner's own personal fields. P1 may be searched and cited subject to field permissions.

## Information lifecycle

Upload → malware/type/size validation → private storage → extraction → classification → publication → indexing → replacement/restriction/deletion. Each index entry retains source ID and version. A superseded or deleted version is unavailable for new search/AI requests. Enforcement always checks live source permissions, including while asynchronous index cleanup is pending. Deleted originals, versions, derived text, backups, and audit records follow separately approved retention and legal-hold rules.

## Explicitly excluded

Salary, payroll, national IDs, performance reviews, medical data, and HR investigations are not collected or indexed in v1. Accidental uploads containing such material are quarantined for authorized review, not indexed or sent to an AI provider.
