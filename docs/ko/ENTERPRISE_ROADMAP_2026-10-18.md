# 엔터프라이즈 게이트웨이·제로트러스트 전체 로드맵 — 2026-10-18

[English](../ENTERPRISE_ROADMAP_2026-10-18.md)

사용자 지시로 2026-10-17 일시정지를 해제합니다. 목표는 nginx·Apache·Caddy·Traefik·Kong·Envoy를
기능·성능·운영 경험에서 능가하는 것입니다. 아래는 목표와 확인한 격차이며 달성·출시·성능 우위
주장이 아닙니다. 설계 승인은 배포 승인이 아닙니다. 과거 인계의 시험 수는 현재 후보의 재검증을
대신하지 않습니다.

## 현황과 결정

| 구성 요소 | 확인한 상태 | 엔지니어링 결정·게이트 |
| --- | --- | --- |
| Hangang 콘솔 | #17 통합 PR 열림; #19 수정은 cherry-pick됨; #12–#16은 대체 계보 | 현재 head의 Rust·브라우저 시험과 EN/KO 스크린샷 검증 후 한 번 병합. 계보·패치 동등성 확인 후 대체 PR 종료. #19 중복 병합 금지 |
| Hangang 보호 | #21 → #23 → #27 → #29 스택 | 의존 순서대로 현재 후보 검증 후 병합. rebase 시 이전 검토 무효 |
| Gateway API | feat/gateway-api `8136b9a`; 인계 당시 49개 중 2개 실패 | WIP. 매칭·호스트명, fake API·상태·RBAC 및 conformance 하위집합 문서 완료 후 PR. 인증 통과 주장 금지 |
| Hopae RC | integrate/identity-platform-rc `37f5c8e`; PG 위험 메모리 실패 | P0: 시간 단위 계약 수정, 모든 저장소 게이트·manifest·시나리오 정리 후 통합 RC PR. HA 출시 주장 금지 |
| Pumgye | #6 → #8/#9; #8은 미병합 Hopae 참조 | RC 후 고정 커밋 갱신, 현재 후보 검증. shadow와 실제 전환 구분 |
| World 차트 | #1 열림; 오프라인·과거 일회용 클러스터 근거 | 현재 오프라인 게이트 수행. 미출시 의존 이미지로 실제 설치·릴리스 보류 |
| 운영자 보증 | #2 열림; Ed25519 브랜치 구현 | EN/KO 미결 모순·상태 표현 수정, 독립 검토 후 문서 병합. 하드웨어·실제 게이트웨이 검증 남음 |
| Sumunjang | bundle 8개 ref 검증, 27개 커밋 비밀 검사, 원격 8개 브랜치 게시 | 이번 사용자 재개 지시로 게시. bundle 유지. 감사 → API 공백 → 존 → TLS → 메트릭 → ASN → LLM 문서 → 근거 점수 순으로 검토. 게시는 병합·릴리스가 아님 |
| ADR | World 0019–0022 이번에 아키텍처 채택; Hopae 기존 0017–0023 제안 상태 | 소유 경계·상한·실패 시 거부하는 설계 방향 채택. 설계 승인과 구현 인수 게이트는 별도 기록하며 미완성 기능을 완료로 바꾸지 않음 |
| LLM 검사 | 설계만 존재 | L0 결정론적 재생·스키마 검증 진행. L1 공급자 호출·비공개 할당량·보존 정책 활성화는 별도 운영 계획 전까지 보류. 요청 경로 호출·LLM 허용/차단 권한 금지 |


이번 변경으로 World ADR 0019–0022의 아키텍처를 채택하며 미결 질문과 단계별 구현·릴리스
게이트를 유지합니다. Hopae는 0017 포털 호스트 RP·일회성 절차, 0018 AAL3 선택적 표시,
0019 Hopae 소유 서명 그룹, 0020 SQLite/PG 단일 계약, 0021 고정 Ed25519 운영자 단언,
0023 상한 있는 네트워크 근거 단계 상승을 기존 보안 게이트와 함께 아키텍처로 채택하도록
권고합니다. 원문 상태 정리는 RC 검토(#23)에 포함하며 일괄 병합하지 않습니다.
인계의 0017–0023 범위와 달리 **확인한 Hopae RC에 ADR-0022 파일이 없습니다**.
해당 번호 승인을 주장하기 전에 번호를 정리합니다. LLM L0은 오프라인 결정론적 재생·스키마
작업이고 L1은 비공개 예산·근거 보존/삭제 정책 전까지 끕니다. 제안된 30일 근거 보존 기간을
운영 기본값으로 승인하거나 활성화하지 않습니다.

## 경쟁 기능 격차표

공식 문서를 2026-10-18 확인했습니다. 모듈·플러그인·상용 에디션은 기본 코어 지원과
다릅니다. `?`는 이번 검토에서 미확인이며 미지원 판정이 아닙니다. `External`은 다른
구성 요소가 필요하다는 뜻입니다. Hangang 기준은 main 문서이며 branch는 미병합입니다.
이번 작업에서 경쟁 바이너리 성능 측정은 하지 않았습니다. 아래 기술 표의 용어·출처는
영문 기준과 동일하게 유지합니다.

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


## 제로트러스트 전체 인수 기준

| 요소 | 있는 근거 | 남은 인수 근거·소유자 |
| --- | --- | --- |
| 신원 | Hopae 공급자·세션 기반, RC의 패스키·그룹·워크로드 신원 | PG 위험 복제, 수명주기·연합 상호운용. 신원은 Hopae 소유 |
| 디바이스 posture | DEVICES 설계 | 인증된 등록·근거, 발급자/대상/신선도, 분실 장치 회수. 장치 바인딩은 Hopae 소유 |
| 지속 검증 | 요청별 authority, 브랜치의 revision/permit fence | 장시간 HTTP/gRPC/WS 종료, 단절·오래된 스냅샷. Hangang 집행과 각 authority |
| 마이크로세그멘테이션 | Sumunjang 존 브랜치, Pumgye 서비스 정책 | 포트·방향·selector 계약, CNI·동서 트래픽 검증. 네트워크는 Sumunjang 소유 |
| 감사 | 구성 요소별 저널, 판정 exporter 브랜치 | 위변조·누락·순서 변경 근거, 영구 콘솔 감사와 보존. exporter 정책 변경 금지 |

전체 솔루션 인수에는 다섯 요소와 릴리스·롤백 근거가 모두 필요합니다. 로그인 성공,
URI SAN, 차트 렌더링, 개별 전송 벤치만으로 완료를 선언하지 않습니다.

## 우선순위·작업별 이슈

P0: 신원/Gateway 정확성 차단 해소, 검토 단위 검증, 벤치·공급망·릴리스 게이트.
P1: 테넌트 격리 데이터 평면, posture·지속 검증, 연합·메시 경계·운영성.
P2: 결정론적 근거 품질 이후 자문형 LLM 분석. 각 이슈는 하나의 검토 가능한 산출물과
명시적 인수 기준입니다. 연합 이슈는 설계 산출물이며 구현별 후속 이슈를 별도로 만듭니다.
아래 이슈 제목·명령은 저장소의 원문을 유지합니다.

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



[Hangang #41](https://github.com/ziozzang/hangang/issues/41)은 첫 Rust 레인입니다. 기존 테스트와 프로덕션 접두부를 보존하는 추가 전용 레이트리밋 회귀 시험이며 fmt/clippy/전체 테스트와 정확성 전용 벤치 면제 사유를 명시합니다.

성능 인수: 같은 하드웨어/CPU·버전/digest·TLS·라우트 수·본문 분포·정책 의미를 사용하고,
순수 프록시와 4개 구성 요소의 전체 인가 체인을 별도 보고합니다. 워밍업 후 최소 5회 측정,
원시 결과 보존. 처리량·p50/p95/p99·오류율·CPU·RSS와 과부하·재적용·회수·authority 장애를
측정합니다. 회귀 예산 제안: p99 또는 처리량 5% 초과 악화 시 조사. 인가 정확성을 희생하지
않습니다. 더 빠르다는 주장은 같은 부하의 경쟁 제품 재현 자료가 있어야 합니다.

## 상시 개발 루프·운영 경계

러너는 검토된 manifest, 이슈별 격리 브랜치와 제한된 모델 권한을 사용합니다. 허용 경로,
EN/KO 문서, 로컬 링크·공백·비밀값 검사를 거쳐 다른 모델 검토와 별도 적대 감사를 받습니다.
검토는 정확한 head/base/diff에 묶이고 main 변경 시 rebase와 모든 게이트를 재실행합니다.
작업자는 셸·push·배포·알림·서비스 제어·비공개 자료 접근 권한이 없습니다. 러너만 PR을
게시·병합합니다. 잘못된 JSON·할당량 부족·권한 거부·미완료 CI·오래된 승인은 병합 근거가
아닙니다. 엔지니어링 실패 3회면 해당 작업을 보류합니다.

초기에는 문서와 프로덕션 바이트 변경을 금지한 Rust 테스트 레인을 구성합니다. Rust는
등록된 fmt/clippy/전체 테스트, 성능 작업은 실제 벤치가 필요합니다. 코드 자동 병합에는
성공한 원격 CI와 최신 base를 요구하는 strict branch protection도 필요하며 없으면 검토된
PR을 보존해 개발 리드가 처리합니다. 문서 검사를 Rust 검증으로 대체하지 않습니다.
성능 수치를 만들거나 모델이 작업 범위를 자동 확장하지 않습니다. 등록된 작업 완료 시
타이머는 대기하고 리드가 다음 검토 단위를 추가합니다.

운영 게이트웨이는 별도 릴리스 절차를 통과해야 합니다: 서명된 불변 산출물·SBOM/provenance →
새 오프호스트 백업 검증 → staging 전체 체인 검증 → 소량 canary → 오류/p99/회수 비교 →
승격 또는 기존 불변 산출물로 롤백. 중단 기준 제안은 인증 우회 1건, 회수 SLO 위반,
5xx 기준선 대비 0.1%p 초과, p99 10% 초과 악화이며 최소 15분 기준선을 사용합니다.
활성화 전 실제 기준선으로 임계값을 검증합니다. DB 롤백은 하위 호환성 또는 별도 복원 승인이
필요합니다. 이번 재개에는 운영·클러스터 변경이 없습니다.
