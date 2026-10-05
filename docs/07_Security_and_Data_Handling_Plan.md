# Secure AI Information Platform — Security and Data-Handling Plan v1

Status: Pilot controls and decisions requiring named organizational approval. This is a security design, not a claim of legal compliance.

## Controls required before pilot

- Identity: organization-managed accounts, strong authentication including MFA for admins, secure sessions, prompt deactivation and session revocation; server-side membership lookup.
- Authorization: default deny; policy versioning; separate admin and content rights; independent approval for self-affecting admin changes; least-privilege service identities.
- Data: TLS, encrypted private storage/database/backups, server-only secrets, allowlisted field serializers, isolated upload processing, malware/type/size validation.
- Search/AI: current source checks before context, final response, citation open, and chat reopen; prompt-injection-resistant tool boundary; no external model use until provider and permitted classifications are approved.
- Audit: immutable or tamper-evident records of grants, revocations, classifications, approvals, denied attempts, downloads, AI source IDs, and admin changes. Keep raw personal fields, document bodies, and full prompts out of routine logs.
- Operations: access reviews, vulnerability/dependency updates, backup restore drill, monitoring and alerting on privilege changes and anomalous bulk access, incident escalation and source/index purge workflow.

## Revocation and deletion

Commit authoritative membership/grant change first; deny new operations from live source policy immediately. Invalidate caches and queued work; mark source unavailable to retrieval before asynchronous reindexing. Download access is checked on every new request; use no persistent public links. On reopen, source-linked old AI answers become hidden if permission is lost. Published deletion is reviewed against retention/legal hold, then tombstoned and removed from active search/AI; securely dispose of originals, derived copies, and backups according to approved schedules. A recipient may retain data already seen or externally saved, which technical revocation cannot undo.

## Decisions to approve before real data

| Decision | Recommended pilot setting | Accountable owner |
|---|---|---|
| AI provider and data location | Approved provider/contract or internal deployment; no personal P2 in AI | Security + privacy |
| Chat retention | Set explicit duration and deletion rules; no indefinite default | Privacy + business owner |
| Updates/docs/versions retention | Per-category schedule and legal-hold exception | Records/business owner |
| Audit retention | Defined period, restricted reader list and immutable storage | Security + legal/records |
| Admin and steward approvers | Named independent persons and absence delegation | Organization owner |
| Session/download expiry and revocation SLO | Set measurable limits and test | Security operations |
| File formats/size and scanning | Allowlist and quarantine process | Security operations |
| Incident contacts and response | Named owner, triage, containment and notification process | Organization owner |

No production employee information is loaded until these rows are approved. Run the first pilot with synthetic Asha/Ravi/Meera/Dev accounts and documents.
