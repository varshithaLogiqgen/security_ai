# Secure AI Information Platform — Product Requirements and MVP Scope v1

Status: Review baseline, 28 September 2026. Source: supplied information matrix and agreed pilot decisions. This project is distinct from the JJ LMS.

## Goal and success criterion

Employees record daily work and share project documents. A signed-in person browses, searches, downloads, or asks the AI only about information they are currently permitted to read. The same decision applies through pages, APIs, direct links, search, citations, and AI retrieval. A pilot succeeds when the acceptance cases in document 08 pass with synthetic users and no cross-organization or cross-project disclosures.

## Pilot boundaries

- One organization in the pilot; `organization_id` is mandatory on every protected entity so isolation remains explicit.
- Four capabilities: daily work updates, project documents, employee profiles, and read-only AI Q&A with source references. Search, administration, and security review support these capabilities.
- Relationships: employee, team lead, organization admin, security/system admin. One user can hold several relationships. Membership and lead assignment are current, time-bounded facts, not permanent privileges.
- Excluded from v1: salary, payroll, performance reviews, medical and HR case records; write actions by AI; external integrations; cross-project document grants; public document links; employee-to-employee work update sharing.

## Functional requirements

1. Users sign in, see their own permitted profile and assignments, and update only self-service fields.
2. An active team member creates a draft daily update for their team. Owner controls `private` or `lead_visible` at publication and can change visibility later. A current lead reads only `lead_visible` updates for teams they lead. Teammates do not inherit access.
3. A current project member uploads a document. Before publication it is uploader-only. Uploader classifies it as `project` or `restricted`. Ordinary documents become available to current project members. For restricted documents uploader grants named current project members; grants expire or are revoked and never override membership.
4. Authorized users browse, search, and download accessible records. Counts, snippets, titles, and links must not disclose inaccessible items.
5. AI answers only from current accessible records/fields and cites accessible sources. It says accessible information is insufficient when there is no supporting content. AI cannot mutate data.
6. Organization admins manage invitations, deactivation, teams, projects, memberships, and lead assignments. Security admins review audit metadata and approved configuration. Neither title alone grants private content.

## Nonfunctional requirements

- Default deny, server-side authorization for every operation; no direct client access to unrestricted storage, search index, model key, or service-role credentials.
- Identity and membership changes take effect for new requests; fail closed during unavailable policy/identity checks.
- Audit security-sensitive changes and access decisions without storing full private content in routine logs.
- Preserve source and version IDs in AI answers, with access checked on reopen and source click.
- Accessible responsive UI; errors do not reveal restricted resource existence.

## Acceptance and release

Ship in slices: identity and policy engine → protected updates → documents and private storage → protected search → read-only AI → revocation and security review. Use synthetic pilot data first. Release requires the authorization test suite in document 08, an owner for operational monitoring, and approval of the open governance decisions listed in document 07.

## Traceability

W1 updates, D1 documents, P1 directory fields, P2 personal fields, A1 structure, C1 conversations, S1 audit records are the complete v1 data categories. Any new category requires catalog, policy, API, UI, and negative-test updates before ingestion.
