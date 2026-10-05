# Secure AI Information Platform — API and AI Retrieval Specification v1

Status: Contract-level design. JSON response shape, pagination limits, rate limits, and deployment URLs are implementation choices. All routes require a server-validated session except sign-in callbacks.

## Endpoint groups

| Route family | Operations | Authorization point |
|---|---|---|
| `/me`, `/profiles/{id}` | GET/PATCH allowlisted fields | P1/P2 field policy; managed fields immutable to self |
| `/updates`, `/updates/{id}` | list/create/read/edit/publish/change-visibility/delete-draft/request-deletion | W1 rules at list, detail, and mutation |
| `/teams/{id}/updates` | lead list | W1-R per record, no private items or leaking counts |
| `/projects`, `/projects/{id}/documents` | list/upload/metadata | Current membership, D1 state/classification |
| `/documents/{id}` | read metadata/classify/grant/revoke/new-version/request-delete | D1 rules; approval for widening |
| `/documents/{id}/download` | streamed download | Fresh D1-R per request; no durable public URL |
| `/search` | query + cursor | Prefilter and per-result live authorization |
| `/conversations`, `/conversations/{id}/messages` | create/list/read/ask/delete | Owner + live answer-source recheck |
| `/admin/*`, `/security/audit` | scoped assignments, approvals, events | A1/S1 and separation-of-duties checks |

## Request handling contract

Server derives user ID and organization from verified session, never request body. Every object ID resolves within organization. Check requested action and fields after loading trusted attributes and again at final disclosure when membership may have changed. Validate and bound inputs; use cursor pagination. Distinguish invalid input from generic missing/inaccessible resources without revealing hidden metadata. Mutations use version preconditions to avoid lost updates; audit decisions and changes. Define idempotency for uploads and approvals.

## Ingestion

Issue private upload intent only for current project members → validate file type/size and malware scan → store unpublished → extract text in isolated worker → link passages to document version → publish only after classification/grant checks → index. Reject or quarantine unsupported/unsafe files and accidental excluded HR data. Version replacement uses the same pipeline; old versions are not searchable after current-version switch. No public object URLs or model calls from the browser.

## Protected AI retrieval

1. Authenticate and load current server-side attributes.
2. Interpret query solely as a search request, with no direct database or privileged tool authority.
3. Search candidate records and chunks using tenant and likely scope filters.
4. Reauthorize each source, version, and field against live policy. Mask excluded fields and remove unauthorized snippets/metadata before model input.
5. Assemble bounded context with stable source/version/citation locators; treat extracted text as untrusted evidence, not instructions.
6. Ask read-only model to answer from supplied evidence; if insufficient, return that state without claiming a restricted item exists.
7. Validate citations refer only to authorized supplied sources and recheck authorization immediately before returning. Persist source links, answer, and policy version; log source IDs, not entire content.
8. On citation click or history reopen, recheck current source access. Hide stale source-dependent answer if access changed; offer regeneration.

No AI tool may invoke write APIs, administer access, or fetch unfiltered data. A system prompt or output filter is supplementary; the retrieval service is the primary boundary. Avoid caching answers across users; any per-user cache must be invalidated by membership, classification, grant, and source-version changes. Streaming responses require a policy plan: v1 should buffer and validate before displaying sensitive answer text.

## Error contract

Return `401` for no valid session, generic `404` for inaccessible/unknown object IDs, `409` for version conflict, and neutral insufficient-evidence response for AI. Internally audit precise denial reason. Rate-limit search/AI to reduce enumeration and cost abuse.
