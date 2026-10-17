# Enterprise gateway and full zero-trust roadmap — 2026-10-18

[한국어](ko/ENTERPRISE_ROADMAP_2026-10-18.md)

Owner-directed resumption of the 2026-10-17 pause. Target: exceed nginx, Apache,
Caddy, Traefik, Kong and Envoy in demonstrated feature coverage, performance and
operator experience. This is a target, not an achieved parity or performance claim.
Design acceptance never authorizes deployment. Historic handoff evidence is not
fresh qualification of today's candidate.

## Current review units and decisions

| Component | Current evidence | Engineering decision / gate |
| --- | --- | --- |
| Hangang console | #17 integration open; #19 fixes already cherry-picked; remaining open #12–#16 are superseded lineage | Qualify exact integration head with Rust, browser tests and screenshots; merge unit once, then close superseded PRs with patch/ancestry proof. Do not independently merge #19 twice. |
| Hangang protection | #21 → #23 → #27 → #29 stacked | Merge in dependency order only after current candidate validation; rebase invalidates old reviews. |
| Gateway API | feat/gateway-api `8136b9a`; 2 of 49 unit tests failed at handoff | WIP; finish matching/hostname tests, fake API/status and RBAC, conformance-subset docs before PR. No conformance claim. |
| Hopae RC | integrate/identity-platform-rc `37f5c8e`; PG risk memory test failed | P0: repair time-unit contract, run all backend gates and document manifest/scenarios before opening consolidated RC. No HA release claim. |
| Pumgye | #6 → #8/#9; #8 references unmerged Hopae | Qualify and update immutable Hopae pin after RC; retain policy shadow/cutover distinction. |
| World charts | #1 open; current offline suite 21 tests (19 pass, 2 optional skips); schema-enabled retry timed out at 300 s | Run current offline gates; unreleased dependency images still block install/release. |
| Operator assurance | #2 merged `fafd0b9`; Ed25519 implementation on branches | Correct contradictory remaining-work wording in EN/KO, independent review, then merge documentation. Hardware/live gateway qualification remains open. |
| Sumunjang | eight bundle refs verified; 27 commits secret-scanned; eight remote branches now published | Publication approved by resumed user instruction. Preserve bundle. Review audit → API gaps → zones → TLS → metrics → ASN → LLM docs → evidence score; publication is not merge/release. |
| ADRs | World 0019–0022 accepted as architecture here; Hopae existing 0017–0023 proposed | Accept ownership and bounded/fail-closed architectural direction; do not relabel unfinished implementations complete. Record acceptance separately from runtime gates. |
| LLM inspection | design only | Approve L0 deterministic replay/schema work; defer L1 provider calls, private quota and retention activation to explicit operational plan. No synchronous request-path LLM; no LLM allow/block authority. |


World ADRs 0019–0022 are accepted as architecture in this change, preserving all
open questions and phased implementation/release gates. Hopae recommendations:
0017 portal-host RP and one-time ceremonies, 0018 opt-in AAL3 presentation, 0019
Hopae-owned signed groups, 0020 one SQLite/PG contract, 0021 pinned Ed25519
operator assertions, and 0023 bounded network-evidence step-up are recommended
for architectural acceptance with their existing security gates. Source-status
reconciliation belongs in the Hopae RC review (#23); no unsafe blanket merge.
There is **no ADR-0022 file on the inspected Hopae RC** despite the handoff's
0017–0023 range: resolve numbering before claiming approval of that number.
LLM L0 is deterministic offline fixture/schema work; L1 remains disabled until
private budget and rationale retention/deletion are specified. The proposed
30-day rationale default is not activated or approved as an operational default.

## Feature gap matrix

Sources below are official documentation checked 2026-10-18. A module/plugin or
commercial edition is not equivalent to default core support. “?” means not
qualified by this review, not unsupported. “External” means another component is
needed. Hangang baseline is repository main documentation; “branch” is unmerged.
No competitor binaries were benchmarked in this session.

| Capability | nginx [N] | Apache 2.4 [A] | Caddy [C] | Traefik [T] | Kong [K] | Envoy [E] | Hangang family gap / priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HTTP/3 / QUIC | experimental module | ? | HTTP/3 | HTTP/3 entrypoint | ? | HTTP/3 | Opaque UDP/QUIC relay only; true termination P1 |
| gRPC | grpc module | HTTP/2 proxy; gRPC parity ? | H2 reverse proxy | gRPC routing | gRPC routing | gRPC | Authority gRPC exists; gateway bidi/trailers/deadlines qualification P1 |
| WebSocket | upgrade proxy | proxy upgrade | reverse proxy | proxy | proxy | HTTP upgrades | tunnel exists; sustained backpressure/revocation qualification P1 |
| Dynamic config / API | reload; API edition dependent | config/graceful; manager modules | JSON admin API | providers/API | Admin API | xDS | candidate/CAS exists; fleet ACK/NACK/rollback P1 |
| Plugins | modules/njs | modules | modules | middleware/plugins | plugin ecosystem | filters/Wasm | isolated Lua + broker; versioned lifecycle/capability assurance P1 |
| Rate limiting | limit_req | bandwidth module; request quota ? | extension-dependent | middleware | plugins | local/global filters | qualify local bounds; distributed quotas/fairness P1 |
| WAF | external/module | external/module | extension | external/plugin | plugin/integration | external/filter | deterministic normalization/CRS-compatible qualification P1 |
| mTLS / SPIFFE | TLS client auth; SPIFFE external | TLS client auth; SPIFFE external | TLS client auth | TLS options | mTLS plugin/edition | TLS/SDS | workload mTLS exists; SVID rotation/federation P1 |
| OIDC / SSO | auth_request/OIDC module/edition | external module | forward_auth | ForwardAuth/external | OIDC plugin/edition | ext_authz/JWT | Hopae identity RC WIP; enterprise federation P1 |
| Policy engine | access/auth modules | authz modules | handlers/external | middleware/external | plugins | RBAC/ext_authz | Pumgye v2 branch; deny/group/AAL/revision qualification P0/P1 |
| Observability / OTel | logs/status/OTel module | logs/status; OTel ? | metrics; tracing scope ? | metrics/tracing | OTel plugin | stats/tracing | Prometheus exists; bounded correlated OTLP P1 |
| Cache | proxy_cache | mod_cache | extension | external/plugin | proxy-cache plugin | cache filter | memory/disk exists; authorization/tenant isolation P1 |
| Load balancing | upstream | proxy_balancer | reverse_proxy policies | services | upstreams | clusters | basic LB exists; outliers/retries/fairness evidence P1 |
| Health checks | passive; active edition/module | proxy_hcheck | active/passive | service checks | upstream checks | active/outliers | existing checks; flapping/drain convergence P1 |
| Service mesh | companion/control plane | external | external | companion | Kong Mesh separate | mesh data plane | full mesh unqualified; trust domains/east-west P1 |
| Gateway API / k8s | Gateway Fabric separate | external | external | Gateway provider | KIC separate | Envoy Gateway separate | Ingress exists; Gateway WIP + charts P0 |
| ACME | ACME module/build dependent | mod_md | automatic HTTPS | certificate resolvers | ACME plugin | external control plane | HTTP-01/DNS-01/EAB exists; fleet renewal/CA outage qualification P1 |
| Performance benchmark | workload-dependent | workload-dependent | workload-dependent | workload-dependent | workload-dependent | workload-dependent | no comparable cross-product baseline; harness/protocol P0 |

Sources: [N: nginx module index](https://nginx.org/en/docs/),
[HTTP/3](https://nginx.org/en/docs/http/ngx_http_v3_module.html),
[gRPC](https://nginx.org/en/docs/http/ngx_http_grpc_module.html);
[A: Apache modules](https://httpd.apache.org/docs/2.4/mod/),
[upgrade behavior](https://httpd.apache.org/docs/2.4/mod/mod_proxy_wstunnel.html);
[C: Caddy proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[API](https://caddyserver.com/docs/api), [modules](https://caddyserver.com/docs/modules/);
[T: Traefik entrypoints](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/),
[Gateway API](https://doc.traefik.io/traefik/providers/kubernetes-gateway/);
[K: Kong gateway](https://developer.konghq.com/gateway/),
[plugin catalog and edition filters](https://developer.konghq.com/plugins/);
[E: Envoy architecture](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/arch_overview),
[TLS](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/ssl).

## Zero-trust completeness gates

| Element | Existing evidence | Missing acceptance evidence / owner |
| --- | --- | --- |
| Identity | Hopae provider/session base; passkeys, groups, workload identity on RC | PG risk replication, lifecycle/federation interoperability; Hopae owns identity |
| Device posture | DEVICES design | authenticated enrollment/evidence, issuer/audience/freshness and lost-device revocation; Hopae owns device binding |
| Continuous verification | request-time authorities; revision/permit fences on branches | long-lived HTTP/gRPC/WS termination, partitions and stale snapshots; Hangang enforcement + each authority |
| Microsegmentation | Sumunjang zones branch, Pumgye service policy | port/direction/selector contracts, CNI/east-west qualification; network ownership stays Sumunjang |
| Audit | component-local journals; decision exporter branch | tamper/drop/reorder evidence, durable console audit and retention; exporter cannot mutate policy |

Full-set acceptance requires all five rows and release/rollback evidence. A successful
login, URI SAN, chart render or isolated transport benchmark is not sufficient.

## Priority and measurable delivery

P0: unblock identity/Gateway correctness; qualify review units; establish benchmark
and supply-chain/release gates. P1: tenant-safe data plane, posture/continuous
verification, federation, mesh boundaries and operability. P2: advisory LLM
analysis only after deterministic evidence quality. Each issue below is one
reviewable deliverable with explicit acceptance criteria; federation issue is a
design deliverable and must create separate implementation issues.

| Priority | Issue / deliverable | Acceptance |
| --- | --- | --- |
| P0 | [[P0] HA risk memory uses one clock contract](https://github.com/ziozzang/hopae/issues/23) | fmt; clippy default/postgres/postgres,test-hooks; all-targets test-hooks; hopae-grpc; test-postgres; qualify-postgres; scenario coverage; no new doc failures |
| P0 | [[P0] Finish Gateway API fail-closed controller](https://github.com/ziozzang/hangang/issues/30) | fmt/clippy/full Rust; 49 controller tests; fake API cases; Helm render; no conformance certification claim without upstream suite |
| P0 | [[P0] Qualify console integration before merge](https://github.com/ziozzang/hangang-zerotrust/issues/3) | Rust and Playwright on current candidate; screenshots EN/KO desktop/mobile; i18n parity; independent review and hostile audit |
| P0 | [[P0] Qualify Helm packaging against released artifacts](https://github.com/ziozzang/hangang-zerotrust/issues/4) | helm strict lint all five profiles; render tests and schema validation; no live deployment |
| P0 | [[P0] Integrate authorization platform with stable Hopae pin](https://github.com/ziozzang/pumgye/issues/10) | workspace fmt/clippy/tests; real-process denied-backend=0 and revocation; exact-head review |
| P0 | [[P0] Review published network-security stack](https://github.com/ziozzang/sumunjang/issues/6) | workspace fmt/clippy/tests; signed ASN tamper/expiry; zones deny tests; hot TLS reload; metrics bounded labels |
| P0 | [[P0] Reproducible gateway benchmark protocol](https://github.com/ziozzang/hangang-zerotrust/issues/5) | Bilingual local links and git diff --check; protocol must distinguish bare proxy and full four-component authorization chain |
| P1 | [[P1] Terminate HTTP/3 with bounded QUIC state](https://github.com/ziozzang/hangang/issues/31) | h3 interop; loss/reorder/NAT change; auth replay denial; H2/H3 equal-policy benchmarks |
| P1 | [[P1] Qualify gRPC proxy and WebSocket revocation](https://github.com/ziozzang/hangang/issues/32) | real gRPC streaming and WS tests; backend unreachable after revocation; memory bounds under slow peers |
| P1 | [[P1] Fleet configuration acknowledgements and rollback](https://github.com/ziozzang/hangang/issues/33) | partition/reorder/replay tests; crash recovery; rollout and rollback dry run |
| P1 | [[P1] Versioned plugin lifecycle and compatibility](https://github.com/ziozzang/hangang/issues/34) | malicious plugin isolation; incompatible version rejection; no credential escape |
| P1 | [[P1] Distributed rate limits with explicit failure modes](https://github.com/ziozzang/hangang/issues/35) | multi-replica overshoot bound; outage and hot-key tests; p99 cost measured |
| P1 | [[P1] WAF rules and request normalization assurance](https://github.com/ziozzang/hangang/issues/36) | benign/attack corpus; parser differentials; false positive report; CPU/memory adversarial bounds |
| P1 | [[P1] Device posture evidence lifecycle](https://github.com/ziozzang/hopae/issues/24) | spoofed/stale/replayed evidence deny; lost-device revoke; privacy and key rotation tests |
| P1 | [[P1] Enterprise federation and provisioning design](https://github.com/ziozzang/hopae/issues/25) | protocol threat models, conformance plan, deprovision/revocation flow and separate follow-up issues before implementation |
| P1 | [[P1] Policy engine replay-safe continuous authorization](https://github.com/ziozzang/pumgye/issues/11) | property/differential tests; policy revocation within declared SLO; no allow on unknown enum or expired evidence |
| P1 | [[P1] OTel trace correlation without request-path blocking](https://github.com/ziozzang/hangang/issues/37) | collector outage/drop accounting; cardinality/privacy tests; p99 on/off overhead |
| P1 | [[P1] Cache authorization and tenant isolation](https://github.com/ziozzang/hangang/issues/38) | poisoning/mixed tenant/revocation tests; hit/miss benchmarks and byte caps |
| P1 | [[P1] Load balancing outliers and health convergence](https://github.com/ziozzang/hangang/issues/39) | retry budget/no unsafe replay; flapping backends and slow-start tests; p99 and fairness |
| P1 | [[P1] SPIFFE identity rotation and mesh boundaries](https://github.com/ziozzang/hangang-zerotrust/issues/6) | CA rollover/revocation and impersonation tests; east-west default-deny evidence; resource budget |
| P1 | [[P1] Kubernetes microsegmentation authority](https://github.com/ziozzang/sumunjang/issues/7) | cross-namespace privilege denial; stale/partial snapshot rejection; disposable CNI qualification plan |
| P2 | [[P2] LLM inspection L0 evidence-only evaluation](https://github.com/ziozzang/sumunjang/issues/8) | prompt injection; malformed/unknown fact IDs; timeout/quota; no raw headers/body; no policy writes |
| P1 | [[P1] ACME fleet renewal and abuse bounds](https://github.com/ziozzang/hangang/issues/40) | staging CA tests; challenge cleanup; lease loss and rollover; no live production issuance |
| P0 | [[P0] Release canary rollback and supply-chain gate](https://github.com/ziozzang/hangang-zerotrust/issues/7) | reviewed runbook and local rehearsal; no /docker/hangang mutation; exact immutable digests |
| P1 | [[P1] Tamper-evident audit export and retention](https://github.com/ziozzang/hangang-zerotrust/issues/8) | tamper/reorder/drop detection; storage outage bounds; delete/key-expiry tests |


[Hangang #41](https://github.com/ziozzang/hangang/issues/41) is the first bounded Rust lane: append-only rate-limit regression coverage, unchanged existing tests/production prefix, full fmt/clippy/tests and an explicit correctness-only benchmark waiver.

Performance acceptance: identical hardware/CPU allocation, versions/digests, TLS,
route count, payload distribution and policy semantics; bare proxy and full-chain
runs reported separately. At least five measured runs after warm-up; retain raw
results. Record throughput, p50/p95/p99, error rate, CPU and RSS, including overload,
reload, revocation and authority failure. Proposed regression budget: >5% p99 or
throughput regression triggers investigation; never trade authorization correctness
for speed. “Faster” requires reproducible same-workload competitor artifacts.

## Continuous development and release boundary

The development runner uses a reviewed task manifest, one isolated branch per
issue, bounded model permissions and private routes. It validates allowed paths,
paired docs, local links, whitespace and secrets before independent model review
and a separate hostile audit. Reviews bind to exact head/base/diff. Any base
change requires rebase and all gates again. Runner alone can push/open/merge PRs;
workers cannot run shell, deploy, push, notify, control services or read private material.
Malformed review output, unavailable quota, permission rejection, pending CI or
stale approval never authorizes merge. Three engineering failures hold a task.

Initial lanes: paired documentation and Rust regression coverage with a byte-identical
production prefix. Rust requires registered fmt/clippy/full tests and successful remote
CI plus strict up-to-date branch protection before automatic merge. Performance tasks
require measured benchmarks; correctness-only tests carry an explicit waiver. A docs
check cannot qualify Rust changes. Without strict protection the reviewed Rust PR is
preserved for the lead, without changing repository settings. No fabricated benchmark results or automatic backlog
scope expansion. Timer idles after eligible configured tasks finish.

Operating gateway changes require a distinct reviewed release: immutable signed
artifacts + SBOM/provenance → fresh verified off-host backup → staging full-chain
qualification → small canary → compare errors/p99/revocation → promote or rollback
by immutable prior artifact. Proposed canary stop thresholds: any auth bypass,
revocation SLO breach, >0.1 percentage-point excess 5xx, or >10% p99 regression over
a minimum 15-minute baseline. Validate thresholds against baseline before enabling.
Database rollback requires backward compatibility or explicit restore approval.
No production/cluster mutation is part of this resumption.
