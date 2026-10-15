# Astra review adoption audit — 2026-10-15

Reconciled by Sol against retained original reviews, current source, test logs,
signed release/adoption records and a fresh coordinator browser check. Astra is
stopped. This audit does not start a new Astra review or qualify the whole product.

| Review scope | Current evidence | Remaining boundary |
| --- | --- | --- |
| T1 signature/time evidence; T2 predecode authentication; T3 BOOTTIME/replay foundation | Implemented and qualified for the current Linux Service chain | Future endpoints need explicit adoption; arbitrary VM/clone/rollback guarantees are absent |
| T4 original source age | Implemented; deterministic delay/clock/suspend-model and real withdrawal/restart gates | No full physical-host suspend/VM restore experiment establishes universal platform behavior |
| T5 shared bounded ingress | Adopted in all four components with functional release gates | No full-chain 10k/100k throughput qualification |
| T6 information architecture; T7 visual/accessibility; T8 authority UX | Partial implementation | The remaining ADM acceptance criteria below are not delivered |
| T9 native client/permit/output/replay/final transport | Current Service path passed actual four-service, independent SDK, K3s/browser, non-dispatch and signed/internal adoption gates | Operating routes remain opt-in; Human/Workload, safe pooling, fleet/streaming and throughput remain unfinished |

## Administrator acceptance: 3 complete, 3 partial, 3 incomplete

| Criteria | State | Evidence or remaining work |
| --- | --- | --- |
| ADM-01 draft lifecycle | Complete for the named fix | Drafts survive navigation/in-flight publication; conflicts preserve edits and logout clears them |
| ADM-02 Sumunjang policy CAS | Complete for the versioned editor | Expected revision checked under publication lock; stale writers and source-managed writes refuse |
| ADM-05 footer placement | Complete | Generated plugin views mount before attribution with headings |
| ADM-03 truthful mutation outcome/correlation | Partial | Final revocation can still drop a completed operation reference; native denial is flattened to infrastructure failure |
| ADM-07 authority freshness/source/errors | Partial | Source ownership/read-only controls exist; a failed audit can block policy refresh and stale states are inconsistent |
| ADM-08 identity/console/service recovery | Partial | Explicit account mappings and server authorization exist; role/error/recovery UX is inconsistent |
| ADM-04 host-owned menus/subpage routes | Incomplete | Discovery-order menu, ambiguous labels, durable subpages/history/search remain |
| ADM-06 shared forms/tables/locale/keyboard | Incomplete | Form hierarchy, scoped overflow, locale lifecycle, tab keys and full responsive/theme/accessibility acceptance remain |
| ADM-09 contextual cross-module navigation | Incomplete | Validated service links, destination reauthorization and installed-capability slots remain |

The bounded ADM count is not a whole-product percentage. Original T items overlap
and have no agreed weights; a single completion percentage would mislead.

## Fresh console observation and concrete defect

A fresh anonymous browser loaded the login and all JavaScript without page errors.
A fresh system-administrator browser opened Pumgye, Sumunjang and Hopae with no
module/global errors. This does not establish that the operator's original account
or session is healthy. Their reported symptom remains under investigation.

Visual inspection confirms unfinished Pumgye form/raw-JSON hierarchy. At a 390px
viewport the operating Pumgye page expands to approximately 619px; the same check
keeps the Sumunjang/Hopae pages within 390px. This is a reproduced ADM-06 defect,
not proof that the entire administrator interface is unavailable. A focused layout
fix and responsive regression are next.

## Releases and newly added scope

Hangang 0.3.7, Hopae 0.0.8, Pumgye 0.1.7 and Sumunjang 0.3.6 have signed-public and
internal-adoption evidence in the [release record](2026-10-15-native-observed-adoption.md).
Hopae 0.0.9 composition has static/local and 1,017-test evidence, but its full K3s
qualification remains incomplete; initial browser failures and a later post-catalog
restoration refusal are preserved. It is not released. Workload policy stage C is
merged, protocol stage A is local and source-owner stage B is in development; there
is no qualified Workload/Human source-to-backend chain yet.

The original three Astra administrator reviews are retained. Interrupted navigation,
write-safety and style follow-up drafts were never saved and must not be counted as
finished designs. Old queue paragraphs are historical; this audit and linked exact
release evidence govern the current state. The full private source-by-source audit
is preserved with the review archive and integrity manifest.
