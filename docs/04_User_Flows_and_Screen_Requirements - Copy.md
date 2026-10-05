# Secure AI Information Platform — User Flows and Screen Requirements v1

Status: Review baseline. Every screen renders server-authorized fields and handles `403/404` without revealing inaccessible content.

|Screen|User action|Required states and checks|
|-|-|-|
|Sign-in|Authenticate, end session|Invalid, inactive, expired; session protected; no local privilege selection|
|Dashboard|View own updates, assigned projects, AI entry|Counts and previews from authorized results only|
|My updates|Draft, edit, publish, choose private/lead-visible, request removal|Clear visibility label and confirmation; owner-only edit; published revision history|
|Team updates|Lead views eligible updates|Current-led teams only; no private drafts/updates; filters preserve authorization|
|Projects/documents|Browse, upload, classify, grant, version, download, request deletion|Membership check; unpublished uploader-only; restricted grantee picker limited to current project members; approver flow for widening|
|Search|Query work updates, directory, documents|No restricted titles/snippets/counts; recheck before result and open|
|AI chat|Ask question, read answer/citations, reopen history|Accessible sources only; insufficient-data state; cite source IDs/versions; reopen may show access-changed state|
|My profile|View/edit own allowed fields|Separate P1 and P2; managed role/team/project shown read-only|
|Organization admin|Invite/deactivate, create teams/projects, assign memberships/leads, review approvals|Scoped changes; self-affecting action requires independent approval; no content preview|
|Security admin|View audit metadata and policy events|Least-privilege filters, no raw document bodies; investigate denied activity|

## Core flows

**Update:** Active member selects own team → enters update → saves private draft → chooses `private` or `lead\\\_visible` → publishes. Current lead sees only lead-visible published updates. Owner changes setting later; next reads and AI requests follow the new setting. Owner can edit own published update with revision/audit, delete draft, or request removal of published content.

**Document:** Current member uploads to private staging → system validates file → uploader sets title/classification → if restricted, picks named current project members → publishes → extraction/indexing become available only through authorized retrieval. Uploader replaces with validated version; classification is retained. Restriction or approved deletion immediately blocks new reads even if index cleanup is pending.

**AI:** User submits question → server resolves current identity/relationships → protected search returns candidates → per-source and per-field authorization → model receives approved excerpts only → output cites approved sources → final source recheck → answer displayed. A citation click checks again. On reopening a conversation after access loss, hide source-dependent answers and offer regeneration; do not show former source titles.

**Membership change:** Authorized admin proposes assignment → independent approver handles self-affecting changes → mutation commits and is audited → new reads/search/download/AI use current memberships. User sees generic no-access state for resources no longer visible.

## UX and accessibility acceptance

Responsive layouts; labeled visibility and classification controls; explicit sharing preview and confirmation; keyboard access and screen-reader labels; accessible errors; no hidden admin-only controls as security substitute. Avoid displaying restricted resource existence in notifications and autocomplete. Show a plain explanation when a user has lost access to previously visible chat content.

