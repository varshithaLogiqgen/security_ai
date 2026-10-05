# Secure AI Information Platform — Data Model and Database Design v1

Status: Logical schema for implementation design, not executable migration. PostgreSQL is an option; physical types, indexes, and RLS policies require implementation review.

## Core entities

| Table | Essential fields and relationships | Integrity notes |
|---|---|---|
| organizations | id, name, status | Pilot has one active row |
| users | id, organization_id, identity_provider_id, status, work_email | Unique identity per org; status checked live |
| user_roles | org_id, user_id, role, valid_from/to, assigned_by | Scoped role history; admin self-assignment blocked |
| teams | id, organization_id, name, status | Unique name within org as appropriate |
| team_memberships | org_id, team_id, user_id, start/end, assigned_by | Active interval; retain history |
| team_leads | org_id, team_id, user_id, start/end, assigned_by | Lead need not be unrestricted data owner |
| projects | id, organization_id, name, status, steward_user_id | Steward assigned under approval policy |
| project_memberships | org_id, project_id, user_id, start/end, assigned_by | Active interval |
| work_updates | id, org_id, owner_id, team_id, work_date, status, visibility, body, version | `private` default; one or multiple per day is product decision |
| update_revisions | update_id, version, body, visibility, edited_by, edited_at | Immutable history, restricted like source |
| profiles_work | org_id, user_id, name, work_email, title | Separate from personal fields |
| profiles_personal | org_id, user_id, encrypted fields, updated_at | Owner-only route; not indexed |
| documents | id, org_id, project_id, uploader_id, title, classification, status, current_version_id | Private default; current member required |
| document_versions | id, document_id, version_no, storage_key, hash, mime, bytes, scan_status, created_by/at | Private bucket; immutable version rows |
| document_grants | document_id, grantee_user_id, granted_by, valid_from/to, revoked_at | Active project membership also required |
| document_chunks | id, document_version_id, ordinal, text/embedding reference, indexed_at | No standalone public query; source authorization |
| conversations | id, org_id, owner_id, status | Owner-only |
| messages | id, conversation_id, role, body, created_at | Answer display subject to source access |
| answer_sources | message_id, source_type, source_id, version_id, citation_locator | Recheck on reopen and citation click |
| approval_requests | id, org_id, type, requester, approver, target, reason, status, expiry | Distinct approver; no self-approval |
| audit_events | id, org_id, actor, action, target type/id, decision, reason, policy_version, occurred_at | Append only, privileged read |

## Relationship and constraint rules

Use composite organization-scoped foreign keys or equivalent validated triggers so a team, project, user, update, document, grant, and chat cannot join across organizations. Constrain enums and state transitions. Unique document `(document_id, version_no)`; immutable audit and document-version content; no duplicate concurrent active grant for same document/grantee. Validate membership and grant eligibility transactionally during assignment, but recheck membership on every read. Index memberships by user/team/project and active intervals; updates by organization/team/date/visibility; documents by organization/project/state; chunks by version. Search indexes never become the source of truth for authorization.

## Enforcement

Backend policy service makes the full decision; database row-level security may be a second layer for tenant/ownership boundaries. Use separate low-privilege DB identities for application and indexing jobs. Service-role credentials must not reach the browser. Restrict direct access to private storage and chunk tables. API fields are projected through allowlisted serializers; field privacy cannot be inferred from row access alone. Use transactions or outbox events to propagate index removal and revocation; mark source unavailable before asynchronous cleanup. Backups and derived artifacts follow data retention rules.

## Design checks before migrations

Agree on update-per-day cardinality, supported file formats and limits, whether version history is user visible, exact approval authority, retention periods, and whether any search includes work-profile fields beyond name/email/title/team. These do not change the authorization baseline but affect constraints and storage sizing.
