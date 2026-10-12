# Threat model and invariants

[한국어](ko/THREAT_MODEL.md) · [Index](README.md)

Assume an attacker controls request paths, headers, cookies, bodies and timing;
can replay stale messages, saturate queues and trigger partial failures; and may
compromise a download/analytics endpoint or a less privileged plugin producer.
Operator-installed JavaScript and configured authorities are explicitly trusted
code/services with scoped privileges, not magically sandboxed dependencies.

| Attack / failure | Required invariant |
| --- | --- |
| Forged subject/class/device header | Facts come only from configured verified authorities |
| Protected path alias/case/escape | One canonical namespace, no weaker second lookup |
| Catalog downgrade or stale replay | Reviewed downgrade; epoch/CAS/hash and compatible activation |
| Network allow used as global authorization | Identity/resource/tenant checks remain required |
| Revoked session on pooled connection | Per-request checks/fences; connection auth is not a grant |
| Old async UI reply after logout | Session-generation check, abort/dispose, no stale repaint |
| Remote package/asset tampering | Reviewed install and pinned immutable package bytes |
| Admin service key in browser | Server-held least-privilege backend/delegation credentials |
| Full-route write delegated to Hopae | Only owned operations/fields with server-enforced scope |
| Protocol length/ID/replay confusion | Explicit version, bounds, IDs, freshness and parser parity |
| Analytics failure on request path | No synchronous sink dependency; bounded queues/counters |
| Audit full or incomplete remote mutation | Fail applicable admission before dispatch; record uncertainty |
| High-cardinality or sensitive telemetry | Fixed label budget; privacy allowlist; no raw credentials |
| Provider unavailable | Explicit deny/unavailable contract, no fabricated identity |
| Missing device/object evidence | Unknown does not become healthy/public/owned |

Testing requires actual process fixtures, adversarial codecs, HTTP/native golden
cases, concurrent authority changes, restart and saturation. Do not equate schema
validation, unit tests or screenshots with production end-to-end assurance.
