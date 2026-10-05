# Secure AI Information Platform — Authorization Specification v1

Status: Review baseline. Policy owner: organization-designated information owner and security owner. Default deny applies to every branch.

## Decision contract

`authorize(subject, action, resource, context) -> {allow, permitted_fields, reason_code, policy_version}`. Subject is an authenticated active user with current organization, roles, memberships, and lead assignments obtained server-side. Resource attributes are loaded server-side, never trusted from client IDs or document text. Evaluate active session, organization equality, resource state, action, field sensitivity, and relationship together. On missing attributes or policy failure, deny. An admin role is never a content-access wildcard.

| Rule | Action and exact allowance | Deny examples |
|---|---|---|
| W1-C | Create update | Active user currently belongs to target team in same organization; create as own draft | Other team, inactive user |
| W1-R | Read/search/AI update | Owner; or current lead of the update's team when published and `lead_visible` | Teammate, former lead, private update |
| W1-E | Edit/visibility change | Owner while active, same organization; published edits create revision/audit | Lead edits another's update |
| W1-D | Delete | Owner deletes draft; published owner requests soft deletion, with approved retention workflow | Silent hard deletion |
| D1-U | Upload | Active member of target project; new document is uploader-only unpublished | Other project |
| D1-R | Read/search/download/AI | Published project document and current member; restricted document and current member with active named grant; uploader still requires current membership after publication | Expired grant, removed member, admin by title |
| D1-G | Grant/revoke restricted access | Uploader with current project membership chooses named current members of same project/organization; audited | Self-selected outsider or cross-project target |
| D1-C | Classify/publish | Uploader sets project or restricted at first publication. Uploader narrows access; widening published access requires distinct authorized project steward approval | Self-approved widening |
| D1-V | Replace/version | Uploader with current membership submits replacement to private staging; validation and publication preserve classification/grants unless explicitly reapproved | Other member overwrites |
| D1-X | Delete | Uploader requests deletion; authorized retention steward reviews; no new read after approved tombstone | Uploader silently erases published record |
| P1 | Directory read/search/AI | Active same-organization user sees approved work fields; owner edits designated self-service fields; organization admin edits managed fields | Self-assign role/team |
| P2 | Personal read/edit | Active owner only via profile; excluded from search/AI in v1 | Lead or admin reads personal phone |
| A1 | Administer structure | Organization admin manages scoped users, teams, projects, memberships and leads; separate security admin controls security configuration | Admin grants own content access |
| C1 | Chat read/delete | Conversation owner; each reopened answer/citation rechecks every source. Hide affected answer until regenerated from currently accessible sources | Former member views old answer |
| S1 | Audit read | Authorized security staff sees security events; organization admin sees metadata of own approved administrative actions | Full source content in log |

## Administrative separation and approvals

An organization admin may change memberships but cannot add themselves to a project, make themselves lead, or approve their own privilege elevation. A second authorized organization admin plus security reviewer approves admin-initiated self-affecting changes. If the pilot has too few approvers, designate an independent security owner before enabling that workflow. Emergency access is out of v1; no hidden override. Project steward is a named assignment created by a non-benefiting organization admin. Steward approves broadening a published restricted document; the uploader cannot approve their own request. Record requester, approver, reason, scope, expiry, and outcome.

## Revocation and time

Membership/lead/grant removal is effective for new operations as soon as the authoritative transaction commits. Never authorize solely from stale JWT roles, cache labels, or index metadata. Existing in-flight model calls cannot be recalled; before returning an answer, revalidate cited sources and discard affected output. Saved answers are source-linked and hidden on reopen if any supporting source is inaccessible; the user may regenerate. Download endpoints validate current access before each response. Avoid long-lived bearer file links; invalidate or let very short-lived links expire on revocation. Exact expiry and session revocation SLO require operational approval.

## Policy mechanics

- The same policy decision is used by list/detail APIs, counts, thumbnails, extracted text, search snippets, AI context, citation metadata, and downloads.
- Search may prefilter candidates for scale, but reauthorize every candidate and field against current source state before disclosure or model context.
- Uploaded content is untrusted data. It cannot set user attributes, grant access, issue tool calls, or alter these rules.
- Denial responses for unknown and unauthorized IDs use indistinguishable public behavior; internal audit retains precise reason codes.
- Audit significant allowed/denied access, approval, privilege, classification, grant and revocation changes; avoid raw sensitive bodies.

## Policy examples

Meera reads Asha's published Payments update only while Meera currently leads Payments **and** the update is `lead_visible`. Asha may change it to `private`, immediately denying Meera's next read. Dev reads an Atlas ordinary document only while currently in Atlas. For a restricted Atlas document, Dev additionally needs an active named grant from its uploader. Neither a Security Admin nor Organization Admin bypasses these predicates.

## Required sign-off

Organization information owner approves who may see work updates and project files; security owner approves enforcement/revocation; privacy or HR owner approves profile fields. Decisions on deletion retention, log/chat retention, approval staffing and link lifetime are tracked in document 07 and must be resolved before real employee data enters the pilot.
