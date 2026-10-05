# Secure AI Information Platform — Acceptance and Security Test Plan v1

Status: Executable scenario specification. Test the same decisions via UI, direct API, search, file download, AI question, citation open, and saved chat reopen where applicable.

## Fixture

One organization. Payments team: Asha and Ravi members, Meera current lead. Dev is in another team. Atlas project: Asha and Dev members; Ravi is not. Create Asha's private and lead-visible published updates, a project Atlas document, a restricted Atlas document with grant only to Asha and Meera if Meera is first made an Atlas member, and a personal phone field. Create separate organization fixture for isolation tests. Mark each source with a unique canary phrase to detect leakage.

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Asha creates/edits own Payments draft | Allow; draft hidden from Meera and Ravi |
| T02 | Meera reads Asha private update | Deny; no result/title/count/AI source |
| T03 | Asha publishes lead-visible update; Meera reads | Allow while Meera leads Payments; Ravi denied |
| T04 | Asha changes that update to private | Meera's next UI/API/search/AI read denied; old source-based chat hidden on reopen |
| T05 | Meera loses lead assignment | All future team-update access denied, even with stale token/index/cache |
| T06 | Dev opens ordinary Atlas document | Allow while Atlas member; Ravi denied |
| T07 | Dev opens restricted Atlas document without named grant | Deny across download/search/AI/citation |
| T08 | Asha grants Dev restricted Atlas document | Allow only while grant and Atlas membership active; record grant audit |
| T09 | Dev leaves Atlas while grant remains | Deny; active grant alone insufficient; old chat hidden |
| T10 | Uploader attempts grant to Ravi, outside Atlas | Reject and audit; no document metadata disclosed to Ravi |
| T11 | Asha narrows ordinary Atlas document to restricted | Immediate denial for non-grantees before index cleanup |
| T12 | Asha tries to widen restricted document without independent approval | Reject; approved steward flow changes access and audits both actors |
| T13 | Admin opens private update/document/P2 by role alone | Deny; admin assignments only through scoped approved workflow |
| T14 | Admin tries self-project assignment/self-approval | Reject; separate approver required |
| T15 | Meera reads Asha personal phone or asks AI for it | Deny; P2 excluded from AI even for owner in v1 |
| T16 | User changes ID or org ID in API request | Deny uniformly; no cross-org leakage |
| T17 | Uploaded file instructs model to ignore permissions | No unauthorized retrieval, tool call, or policy change |
| T18 | Restricted document deleted or version replaced | Old version unavailable to new search/AI; citations rechecked |
| T19 | Former member uses copied link | Fresh authorization denies; expired token cannot bypass |
| T20 | AI has no accessible sources | Neutral insufficient-information response; no hidden counts/titles |
| T21 | Audit viewer opens events | Security staff sees metadata; organization admin limited to own approved admin actions; no raw body |
| T22 | Policy service fails or attributes missing | Fail closed; error audited without content disclosure |

## Test method and release gates

Automate policy unit cases from document 03 and end-to-end tests on each access path. Include concurrent revocation during an AI request, malformed IDs, bulk enumeration, pagination/count leakage, wrong-tenant joins, cache/index lag, and field-level serialization. Verify source canaries never appear for denied users. Security review inspects upload pipeline, stored secrets, direct object URLs, log payloads, approval separation and backup restore. Release only when all critical allow/deny cases pass, no high-severity leakage remains, approved governance decisions are recorded, and an owner signs off on test evidence.
