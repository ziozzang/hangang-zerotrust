# Native Human 증거 → typed 권한 → 최종 집행 설계

상태: **검토용 설계이며 Human wire/제품 활성화 구현이 아닙니다.**
[English normative contract](../reviews/2026-10-16-human-native-wire-design.md).
기존 [provider 전체 목표](2026-10-15-provider-completion.md)를 유지합니다.
H0만으로 자체 계정·복구·모든 provider MFA·stream 회수가 끝났다고 하지 않습니다.
이전 감사의 Any/All production caller 부재는 당시 기록입니다. 현재 Service에는
고정 credential slot·명시 identity relationship·원래 예산을 보존하는 실제
composition이 있지만 AAL0이며 Human MFA가 아닙니다.

## 기준 소스와 실제 재사용 경계

Cargo·cluster·운영 변경 없이 다음 clean 소스를 읽었습니다.

| 기준 | 확인한 구현과 남은 경계 |
|---|---|
| ZT `735333800b114ca66685cb6eff29d28802e1253a` | 이 격리 설계의 기반. 기존 증거와 전체 목표를 대체하지 않습니다. |
| Hop `87d19a02ee162120eba55a341f9ceb1e02bd9aa5` | private H0 검토 소스. full1111/ignored43·strict Clippy/fmt, 실제 owned OIDC·LDAP LDAPS/StartTLS·TOTP·Engine/current, 실제 CLI material restart 검사 통과. 공개 Human RPC나 운영 채택 증거가 아닙니다. |
| Hop `verify/human.rs:171,191,287,379,387`, `verify/engine.rs:174,349` | 원래 Admission과 실제 Store 기반 Engine, 정확한 HandleView·Refresh 뒤 예상 identity, 최종 Allow만 Checked 생성. 현재 scope에는 최종 body/header digest가 없습니다. |
| Hop `session/service.rs:1463,1647,2003,2271`, `store/sqlite/{primary_owner,human_owner,material_owner}.rs` | adapter 검증 전 primary owner 캡처, 실제 create/reauth transaction provenance, TOTP 뒤 원래 primary generation 유지, joined current 검사. 기존 SessionSeal/issue_session은 새 observed source가 아닙니다. |
| Hop `provider/registry.rs:182,223,356,394,442` | 같은 DB rows/config/material로 컴파일한 실제 Registry와 게시 CAS. 오래된 준비본/ABA 덮어쓰기 거부. human_material_key_env는 source incarnation 전용입니다. |
| Hop `crates/hopae-grpc/proto/gateway.proto`, `http/grpc_gateway.rs:1715-1746` | 실제 Service/Workload RPC. Workload attempt는 tonic decode **뒤** 시작합니다. Human predecode 경계를 이미 만족한다고 하지 않습니다. |
| Hop SDK `request_binding.rs:23`, `workload_observed_client.rs:186,308,382,445,576,602` | v1은 service/audience/method/target/entity hash를 묶지만 header는 묶지 않습니다. 고정 peer/pin, opaque observation, independent observe·소모형 refresh·최종 check의 기법만 재사용합니다. |
| Pum `435f138927fa78a1256e8a29a442eba399b971b6` | `pumgye-core/src/lib.rs:31,159,571,598`의 같은 policy/View·typed Workload map, `workload_observed_permit.rs:37`의 실제 source/Guard/route/plan. Human map/source는 별도 구현이 필요합니다. |
| Root `0b15bfb7f7d199b6b653cd5de567ccc667df7055` | `projection_entity.rs:42,157`, `projection_binding.rs:14,40`, `proxy.rs:3388-3455,3500-3562`: rewrite/backend 구성 뒤 immutable complete body와 route owner·최종 transport/write gate. 현재 v1은 header를 묶지 않습니다. |

파일 경로는 각 component의 src 기준입니다. 실제 구현 때 exact dependency를 다시
고정하고 자기 소스/바이너리로 검증해야 합니다. public source·released runtime·운영
활성화는 서로 다른 근거입니다.

## 1. 실제 최종 요청의 소유권

Root는 route rewrite, Lua/body 변환, backend base-path와 header 변환을 모두 끝낸
실제 요청에서 private `HumanPrepared`를 만듭니다. 기존 bounded body semaphore와
원래 route lease를 유지합니다. 완성되지 않은 stream·trailer·지원하지 않는 upgrade는
거부하며 빈 body를 꾸며 hash하지 않습니다. 기존 최대16MiB 범위 안에서 Human도
명시적 bounded limit을 선택합니다. 발급 뒤 요청 변경이나 독립 dispatch용 복제를
허용하지 않습니다. 최종 projected credential 설치만 지정된 별도 단계에서 수행합니다.

기존 Service/Workload v1 바이트는 그대로 두고 request binding **v2**를 추가합니다.

- domain `hangang-zerotrust:credential-projection:request:v2\0`;
- length-frame service, audience, route ID/revision, 실제 destination-owner SHA256,
  uppercase method, 최종 origin-form target;
- 실제 entity 길이(u64 big endian)와 전체 전송 바이트 SHA256;
- 고정 header-policy revision과 lowercase 이름순 slot 전체의 이름·presence1바이트·
  실제 값. absent와 present-empty를 구분하며 trim·URL/query 정규화·JSON 순서에
  의존하지 않습니다.

바이트 encoding/vector의 normative 기준은 별도로 조율 중인 **H1 canonical codec
specification**이며 이 chain 설계가 경쟁 encoding을 할당하지 않습니다. 합의한 형태는
text LP32, 숫자 fixed BEu64, destination fixed32, entity 길이 BEu64+hash32,
header-policy revision BEu64, slot count BEu16, slot마다 LP32 이름+presence byte와
present인 경우만 LP32 값입니다. 이름은 lowercase RFC tchar1..128바이트이며 고정
credential reserved names를 validator 인자로 받습니다. 값의 TAB 포함 CTL과 DEL은
거부하고 obs-text 바이트는 보존합니다. 한도는16 slots/총8192/개별1024바이트 및
완성 entity16MiB입니다. 실제 구현 전 H1 spec과 독립 cross-language vector로 세부
framing을 확정하며 raw hash/length builder는 Human authority API가 아닙니다.

기존 v1의 identifier/method/target 검사를 재사용합니다. destination은 client URL이
아니며 실제 Root route reference와 Pum current route owner가 일치해야 합니다.
초기 Human은 method 변경 변환을 거부합니다. public app 경로와 최종 rewrite 경로는
고정 route/scope→Pum resource/action/plan 관계로 연결합니다. Hop이 Root Lua를 다시
실행하거나 악의적인 PEP가 실제 전송한 바이트를 원격 hash만으로 관측했다고 하지 않습니다.

Header는 서버 고정 최대16개·값 합계8192바이트·개별1024바이트입니다. 중복·control·
알 수 없는 slot은 거부합니다. Authorization, Cookie, caller/projected credential,
identity/AAL header, Forwarded/X-Forwarded-*, Host, framing/hop-by-hop은 항상 제외합니다.
Content-Type/Encoding·명시 app intent는 변환 후 값을 묶을 수 있습니다. framing은
entity 길이로 검사합니다. 제외한 보안 필드는 별도 owner/caller/route 검사와 upstream
제거/덮어쓰기 대상이지 client identity 승격 통로가 아닙니다. header policy 변경은
이전 prepared request/client/route owner를 회수합니다.

Human SDK 초기 API는 완성된 `Request<Bytes>`와 trusted native context를 받는
`prepare`이며 public `prepare_issue_digest` shortcut은 제공하지 않습니다. DTO/hash/
request builder는 identity 증거가 아닙니다. 신뢰하는 PEP가 실제 최종 요청을 제공하고
source는 실제 native session을 별도로 검증합니다. Root는 동일 immutable body로
최종 dispatch 직전에 v2/header/destination을 다시 비교합니다.

기존 native parser로 원래 public URL/method, app host/port/route, 실제 edge client
IP/UA와 host-bound handle을 전달합니다. 원래 URL과 최종 upstream target을 구분하며
서버가 게시한 관계로 묶습니다. Root가 spoofed source header를 제거하고 실제 edge에서
context를 재구성하며 caller credential은 서버 설정에서만 주입합니다.

## 2. Additive proto/API 제안

정확한 선언·field number는 영문 문서의 proto block이 normative입니다. 기존
hangang.hopae.v1 field/RPC를 바꾸지 않으며 다음을 추가합니다. 번호와 contract4는
아직 production 할당이 아닙니다.

| 추가 타입/서비스 | 필드 및 의미 |
|---|---|
| HumanBoundHeader | name1 / present2 / value3 |
| HumanFinalRequest | binding_contract1=2 / method2 / target3 / entity_sha2564 / entity_length5 / route_id6 / route_revision7 / destination_sha2568 / header_policy_revision9 / headers10 |
| HumanReceiptRequest | verification1 / service2 / audience3 / final_request4. subject/AAL/generation/receipt/caller request_sha256 입력 없음. |
| HumanReceiptReply | request_id1 / 기존 AuthenticationReceiptContext2 / receipt3 |
| HumanReceiptObservedReply | receipt1 / observation2 |
| HumanReceiptObservationRequest | request_id1 / context2 / receipt3 / request_sha2564 |
| HumanReceiptTimeReply | request_id1 / owner_now_ms2 / remaining_ms3 / receipt_sha2564 / clock_domain5 / source_revision6 / application_generation7 / key_registry_revision8 / cache_ttl_ms9=0 |
| HumanAuthenticationReceipts | IssueObserved(HumanReceiptRequest), ObserveTime(HumanReceiptObservationRequest) |
| HumanObservedCredentialProjection | Project(기존 ProjectionRequest)→기존 ObservedProjectionReply. permission_contract4만 허용. |
| Pum HumanObservedProjectionPermits | 기존 AuthenticatedResourceRequest로 Issue, 기존 PermitValidationRequest로 Observe; 기존 observed permit/report 반환. |

Human issue는 bounded descriptor와 서버 header policy로 v2를 재계산합니다. entity
hash는 authenticated PEP의 요청 attestation이지 source identity capability가 아닙니다.
추가 프로토콜·SDK 후보는 기존 128KiB frame 상한과 Verify/header 제한을 유지합니다. 유효한 기존 인증 헤더를 축소하지 않습니다. 원천 record의 개수·바이트 한도는 설정 가능해야 하며 고정 admission64는 wire 계약이 아닙니다.
누락·중복·잘못된 길이/0 hash·correlation·contract·scope mismatch는 Engine/sign 전에
거부합니다. cookie/header/body/proof/default Debug는 release에서도 명시적으로 redaction합니다.

기존 receipt envelope/purpose를 사용하되 signed kind는 **1 Human**, 실제 handle AAL1
또는 native TOTP provenance가 있는 AAL2만 허용합니다. generic parser가1..3을 받아도
현재 source의 AAL0/3은 거부합니다. identity.revision은 실제 user authz version,
credential_generation은 TOTP 뒤 실제 session generation입니다. Service/Workload처럼
profile revision과 같다고 가정하지 않습니다. user/session별 revision을 서로 다른
subject 사이 global floor로 적용하지 않습니다. global floor는 실제 source/app/key
owner에만 적용하며 user A revision100 뒤 user B revision1도 검사합니다.

이전 s_48 Human derivation은 [H2a subject/lifecycle 계약](2026-10-16-human-subject-lifecycle.md)으로
**대체됩니다**. human1:+full lowercase SHA256이며 고정 source issuer·실제 durable Store
realm·exact current native user ID를 묶습니다. caller email/realm/session/provider label은
이를 선택하지 않습니다. Service/Workload s_48 및 legacy strict session receipt는 불변입니다.
계정 연결은 실제 owning native identity 정책이며 revision/AAL/proof epoch는 별개입니다.

Epoch 제안은
`hobs1:<32lowernonzero-process-nonce>:<authority>:s:<source-scope-revision>:a:<app-generation>`
입니다. authority40·전체128·revision1..9007199254740991·leading zero 금지와 strict
re-encode를 적용하는 별도 parser이며 다른 class/legacy epoch를 거부합니다.
clock_domain은 정확히 nonce입니다. Human source_revision은 실제 Human scope 게시
owner로, 초기에는 durable config generation과 exact prepared app Arc에서 나옵니다.
Service authentication_gateway profile이나 user/session revision이 아닙니다. Human
runtime을 만들기 위해 Service profile을 억지 활성화하면 안 됩니다.

Project contract4의 permission_query는 실제 bounded Pum protobuf 바이트입니다.
기존1/2/3은 불변입니다. RPC마다 새 ID와 내부 permit ID를 독립 검사합니다.
chain_sha256은 그 원본 바이트 SHA256이며 재직렬화 JSON이 아닙니다. 출력 profile
metadata는 hobs1 scope revision과 대조합니다. 이번 단계는 Human UTC endpoint를
추가하지 않습니다.

## 3. DTO 대신 실제 source capability와 원래 시간

Human 전용 ingress layer가 tonic body decode·caller 검사·parse·queue **전에** 원래
private BOOTTIME Admission을 잡고 server-owned Rust extension으로 보존해야 합니다.
버퍼링 전 bounded admission을 획득합니다. RPC path 선택만으로 class를 부여하지 않으며
mTLS peer/caller-key도 검사합니다. clock 실패는 추가 Human만 거부하고 ordinary 및
non-Linux 경로를 망가뜨리지 않습니다. extension 누락은 거부하며 exchange/gateway/
Engine에서 새 anchor를 만들지 않습니다. predecode pause/suspend RED/GREEN이 필요합니다.

비공개 삽입 API:

1. Pipeline::exchange_human(VerifyRequest, IngressAdmission, OwnedHumanScope)가
   기존 parser/caller와 Capture extension을 재사용합니다.
2. 실제 final Allow H0 Checked를 소비하는 bind_final(OwnedFinalBinding)만 BoundHuman을
   만듭니다. 원래 scope/handle digest를 유지하며 raw cookie는 보존하지 않습니다.
   record용 private retained-scope current entry를 추가합니다.
3. issuer는 BoundHuman만 받습니다. Identity/SessionSeal/헤더/boolean/서명+숫자 시간으로
   만들지 않습니다. 실제 provider/material/config/session/user/handle/factor/app와
   signer registry를 sign 전 및 모든 callback/await/allocation 뒤에 검사합니다.
4. 정확한 signed receipt hash→원래 BoundHuman/context/digest/admission/current signer와
   process domain record가 필요합니다. record miss/retirement/capacity는 거부하며
   wallclock 복원·새 발급 fallback·live eviction은 없습니다.

Record 제안: count 최대4096·default1024 및 variable native facts/header capacity까지
포함하는 별도32MiB retained-allocation budget, bounded sharded lookup/prune입니다.
보존 전 count/bytes를 예약하고 초과는 거부하며 만료/회수 때 정확히 한 번 반환합니다.
숫자 record ID/size budget은 source capability를 만들지 않습니다. 처리량은 실측 gate입니다.

원래 기한은 tick quantization까지 포함해 **1초 미만**이며 원래 H0 session/handle/
factor freshness보다 길 수 없습니다. 서명 expiry도 같은 source domain의 그 기한
안입니다. ObserveTime은 인증된 **current/revocation endpoint**입니다. signature/context/
hash와 issuing record를 대조한 후 실제 joined current 검사합니다. 기존 logout/admin/
user/factor/provider transaction이 원래 owner를 회수하며 Pum/Root가 이를 변경하지 않습니다.
observe/refresh로 login/reauth·touch 연장·새 record 대체·retired 복구를 하지 않습니다.
모든 작업 뒤 실제 remaining Duration의 floor를 반환하며 TTL0은 revocation lease가 아닙니다.

명시 source/receiver ppm, RPC 전 exchange anchor, 보수적 transit/rounding 차감,
BOOTTIME generation을 사용합니다. 서로 다른 절대 expiry min·receiver UTC cleanup·
임의 grace·원격 EQUAL fallback·공개 숫자 deadline으로 capability를 만들지 않습니다.
clock failure/reversal/suspend는 원래 경계를 회수/거부합니다. EQUAL은 같은 실제 owner/
backend임을 입증한 로컬 연결에서만 가능합니다.

Record는 process-affine입니다. restart/다른 replica/record miss는 같은 key/config여도
옛 proof를 거부합니다. material이 같은 정상 재시작의 유효 native session은 실제
Engine으로 **새 proof**를 만들 수 있으나 옛 proof가 되살아나는 것은 아닙니다.
고정 peer/affinity를 명시하고 임의 LB replica가 record를 재구성하면 안 됩니다.

SDK 제안 human_observed_client는 고정 mTLS peer/pin·hobs1·scope/app/route/header
contract·source/app/key floors·명시 rates를 갖습니다. new_human/prepare/issue/
prepare_observation+independent observe/소모형 refresh/check/retention API를 제공합니다.
Observation은 exact prepared request/client owner/signature/hash/context/source-clock
exchange와 원래 record-backed report에 묶인 private fields입니다. public DTO 또는
SignatureEvidence+임의 runtime bounds로 만들 수 없습니다. refresh는 admission을
줄이고 upper retention만 늘리며 clock callback 뒤 최종 owner/floor를 검사합니다.

## 4. 같은 Pum policy와 Hop paired transaction

같은 owning CAS/compiler/View에 optional human_users를 추가하고 전체 assignment
bounds에 포함하며 빈 map은 기존 serialization에서 생략합니다. Principal::Human 및
native Human evaluator만 해당 map을 읽습니다. users/workload_users fallback은 없으며
같은 subject의 세 map을 독립 관리합니다. guest는 권한을 주지 않고 unknown/missing/
failed publication은 거부합니다. Kubernetes v1/v2에서 Human grant를 자동 생성하지 않습니다.

Human roles AND network/Guard AND resource permission AND classification AND 최대
minimum-AAL이 모두 필요합니다. AAL은 checked native proof에서만 오며 role 요청·group·
network·Service/Workload branch 합/최댓값으로 오르지 않습니다. Pum 실제 policy/View와
Hop SDK/Guard/route/plan owner를 sign/emit 전까지 검사합니다. assignment/role/class/
source 철회가 retained candidate에 반영돼야 하며 exporter write를 hotpath에 넣지 않습니다.

Human OwnerSlot은 서버 고정입니다. Pum 자기 pobs1 BOOTTIME source에서 full signed
proof_remaining_ms는 replay upper retention, 더 짧은 remaining_ms는 admission입니다.
실제 DB/Kubernetes immutable publication을 사용하며 policy 복사본이나 request-selected
peer는 금지합니다.

Hop은 Workload record cast가 아니라 private Human fence를 shared paired core에
연결합니다. async H0 check를 SQLite writer/ledger lock 아래 await하면 안 됩니다.
같은 bounded durable comparison을 opaque expected facts와 사전 native time을 받는
private connection-scoped checker로 추출하고 실제 **같은 Store** paired transaction에
사용합니다. 원격 Pum 관측 앞뒤 current 검사, transaction 안 실제 Human rows/material/
factor·keys·route/plan/app/caller/config·원래 BOOTTIME 검사, secret 작업 뒤 순수 current/
time 재검사가 필요합니다. writer 안 await/network/env/CA/user-clock callback은 없습니다.
기존 prepared local vault에서만 secret을 atomic admission 안에 해석하며 임의 resolver나
새 network lookup을 추가하지 않습니다. 별도 business DB/attached foreign schema나
새 replay store로 분리하지 않습니다.

두 nonce는 기존 canonical ledger에서 **같은 transaction으로** 소모합니다. class/mode/
endpoint/contract prefix로 다시 사용할 수 없습니다. 각 full signed upper lifetime은
stable receiver BOOTTIME generation에서 독립 보존하며 source record의 짧은 생명과
구분합니다. unknown generation tombstone은 보수적으로 유지하고 capacity 초과를
거부합니다. UTC/grace cleanup은 없습니다. commit 전 실패/cancel은 부분 consume/secret
출력이 없고 commit 뒤 cancel/응답 유실은 둘 다 소모되어 재출력할 수 없습니다.

Human output은 필요한 async current read를 commit 뒤 reply 전에도 수행합니다.
마지막 callback/allocation 뒤에는 native BOOTTIME와 순수 publication 검사만 합니다.
실패 시 nonce가 이미 소모됐어도 secret을 폐기/zeroize합니다. output은 자기 clock
nonce, exact chain/request/RPC hash와 최종 실제 Duration floor를 갖고 다른 source
절대 expiry min을 쓰지 않습니다. 이는 point-in-time 검사이지 원격 원자 회수가 아닙니다.

## 5. Root·브라우저·관리 범위

서버 설정의 명시 Human class에 실제 source/client/permit/output/final gate를 연결합니다.
request header나 enum만 추가하는 구현이 아닙니다. 기존 Service/Workload/default는
불변이며 거부/장애 뒤 다른 class fallback이 없습니다. class·service scope·backend
credential은 별도 개념입니다. 모든 pin/kind/epoch/AAL/request/chain/ID/revision/TTL0와
owner를 검사합니다.

준비 뒤 unbound 변환은 없습니다. 최초 upstream byte 직전에 digest/header/destination,
원래 remaining age, route/auth/network/permission/output transport를 검사하며 delayed
connect·pool 재사용·HTTP/2 새 stream에도 적용합니다. 실제 write까지 guard를 유지합니다.
거부 backend0, 성공 backend1에 고정 projected credential만 전달합니다. caller key·원래
credential·proof/envelope·spoofed identity 및 사용한 Hop cookie 이름(default
__Host-hopae / __Host-hopae_bind / __Host-hopae_portal)은 제거합니다. 관계없는 app
cookie는 명시 safe policy로만 보존합니다. 로그/browser에 secret/header/body를 출력하지 않습니다.

interactive login/TOTP는 기존 native portal/Verify 계약을 사용합니다. redirect·handoff·
step-up은 issuable final Allow가 아닙니다. navigation의 기존 인증된 native 응답을
전달하고 이후 실제 새 요청에서 issue합니다. Human RPC가 login URL을 꾸미거나 TOTP
뒤 non-idempotent 요청을 자동 재생하지 않습니다. API는 안전한 login/step-up 거부를 받습니다.

Pum admin에는 같은 CAS의 독립 Human assignment kind/map, 동일 subject row 분리,
draft/role/logout/generation/mobile fence를 적용합니다. 실제 지원하는 SSO 버튼·LDAP
password/TOTP만 표시하며 API composition을 MFA로, Google unsupported forced reauth를
가능한 것으로 표시하지 않습니다. minimumAAL UI는 정책 요청이지 factor 완료 증거가 아닙니다.

## 6. 명시 활성화·스키마·키 lifecycle

영문 6절 JSON은 **아직 실제 loader가 받지 않는 제안 fragment**입니다. 구현 전까지
기존 unknown-key 검사는 거부해야 합니다. receipt_issuer.human_receipts에 authority와
service/audience/app_id/realm/route_ids/binding_contract2/header_policy{revision,names},
maximum_records1024/maximum_retained_bytes33554432를 선언합니다. Human scope/profile
revision은 실제 owning publication에서 나오며 client가 선택하지 않습니다. fragment의 임시 realm label은 Human namespace를 선택하지 않습니다. H2a가 이를 실제
immutable Store realm으로 대체하며 subject는 고정 issuer_ref+실제 current user ID를
사용하고 provider provenance는
별도로 검사합니다. 실제 signing/transport 설정은 기존대로 필요하며 material key를
receipt_issuer.seed_env 대신 쓰면 안 됩니다.

Human-only issuer가 dummy Service profile/scope 없이 준비되도록 source별 validator/
readiness를 함께 수정해야 합니다. 어느 source도 없는 empty issuer는 여전히 거부합니다.
Service RPC가 Human scope 선언을 받아들이면 안 되며 absent 설정의 serialization/
default는 보존합니다.

Pum 제안 flag는 기존 observed-authentication production feature 아래
--human-observed-permits / --human-authentication-live reference-file입니다. trust·permit
signer·Guard/network·route·plan을 필수로 하고 verify-off fallback은 없습니다. 고정 live
파일은 기존 issuer_ref/address/server_name/ca/certificate/key/token_env 및
observed_clock_rates{source_ppm,receiver_ppm} 형태를 재사용하되 Human OwnerSlot만
만들며 hobs1 scope/app/key floor를 고정합니다. 엄격 key allowlist와 기존 CLI 호환성을
검사합니다. human_users selector는 실제 Hop user owner에서 opaque subject를 얻어야
하며 email/client assertion을 쓰지 않습니다. 그 selector 전에는 provenance가 명확한
opaque 값 직접 입력만 허용하고 기존 users 자동 변환은 하지 않습니다.

Root는 routes[].native_resource.observed.authentication_class="human"을 명시하고
기존 issuer/목적별 permit pin, identity_authority, minimum profile/app/key floors,
source_error_ppm/receiver_error_ppm을 요구합니다. 새 서버 고정 native_resource.human_binding의
contract2/header policy revision/names가 Hop scope·실제 route publication과 일치해야 합니다.
기존 maximum_body_bytes/body_timeout_ms/final-header 제한과 고정 mTLS peer/resource/plan을
유지합니다. 의존성/manifest 불일치·미지원 class·rates 누락은 거부하며 Human 미설정은
기존 default를 유지합니다. ppm은 운영자가 입증하는 bound이며 fixture 통과에서 보편
상수를 만들지 않습니다.

H0 schema9/material owner가 선행 조건이고 proof record는 ephemeral, 기존 paired
ledger는 durable입니다. 새 persisted metadata가 실제 필요하면 별도 migration의
inventory/guard/backup을 검증하되 legacy proof를 backfill하지 않습니다. material key,
receipt signing epoch/trust, caller/mTLS, TOTP keyring/enrollment는 별도 lifecycle이며
각 removal/restore/ABA/failed publication을 검사합니다. source/SDK/proto/typed consumers는
Human disabled 상태로 준비한 뒤 owned route를 검증하고 기존 승인 범위의 별도 검증된 publication/adoption 단계를
수행합니다. 기존 signed artifact를 덮어쓰거나 source merge로 운영 Human을 주장하지 않습니다.

## 7. 순서와 RED/GREEN gate

| 단계 | 다음 단계 전 실제 검증 |
|---|---|
| H1 계약/prepare | SDK/Root/Hop v2 고정 vector: 실제 빈/비어있지 않은 body·동일길이 변조·변환 후 bytes·absent/empty/duplicate header·target/basepath/destination/method 변조. 옛 v1 header 변조 RED, 새 v2 GREEN. 기존 v1 vector 불변. predecode pause/suspend 원래 age 소모. |
| H2 source/SDK | 실제 OIDC nonce/PKCE/signature 및 LDAP LDAPS/StartTLS→실제 TOTP→Engine→issue→독립 observe→refresh/check. legacy/external-only AAL2·AAL3·다른 class 거부. caller/IP/UA/host/route/handle·key/app/material/provider/config/primary/factor/user 회수의 await/sign/emit race, deadline/cancel/clock, record miss/restart/replica/capacity. |
| H3 Pum typed | 같은 subject의 세 map 독립 add/delete, guest/unknown/role/class/resource/action/network/Guard 거부. AAL1은2 불가, 실제 TOTP2는 가능, 현재3은 불가. policy/source/route/plan 철회. 실제 CAS stale·응답 유실·readback/restore, force overwrite 금지. |
| H4 paired | 실제 SQLite/vault 동시 pair 한 승자, 다른 contract/class 재사용 불가, 단일 nonce 충돌, secret/commit 전후 실패, cancel/응답 유실/restart/unknown-generation/capacity/key removal, 출력 allocation 뒤 회수, transit/floor. detached signer/숫자 bounds로 Human source 생성 RED. |
| H5 exact chain/UI | 독립 공개 SDK+실제 Hop/Pum/Guard/Root/count backend: OIDC/LDAP/TOTP positive1, class/AAL/guest/classification/request/header/destination/revoke/replay/cancel/delayed-connect negative0. 실제 native SSO/login/TOTP/logout, admin CAS/draft/locale/mobile, 기존 Service Any/All·native/default Workload 회귀. transport 오류를 기대 정책 deny로 세지 않음. |
| H6 artifact/adoption | exact dependency, full/default/feature/strictClippy, production static/hash, 독립 review, local4service 뒤 명시 K3s independent-host/SDK/browser. 기존 승인 범위의 별도 검증된 publication/adoption 단계와 source/artifact receipts. binary 설치만으로 Human route 활성화/검증 주장 금지. |

Async immutable memory snapshot/follower membership과 처리량은 후속 correctness+
performance gate이며 TTL cache로 current SQL을 대체하지 않습니다. provider별 외부
factor provenance, multi-issuer 관계, Human/Service/Workload actor composition, 자체
계정·credential 교체/복구, 계정/directory 회수, Google capability 한계, long-lived stream
재인가를 전체 목표에 유지합니다. Any/All은 원래 branch budget/snapshot/circuit을
보존하고 supplied-invalid/ambiguous identity를 거부해야 하며 검증된 native factor
계약 없이 assurance 합/최댓값 승격은 없습니다.

Parent는 H1 pure codec에 한해 additive v2/header limit을 수용했으며 Human route/RPC
활성화는 허용하지 않았습니다. 독립 cross-language vector가 먼저입니다. 이후 구현 전
hobs1 source revision·contract4 할당, public→final route/
destination 관계, predecode tonic·same-Store checker, subject realm lifecycle·record
capacity를 검토합니다. source-affine topology와 full signed replay retention을 다시
확인합니다. material key·receipt signing key·caller/transport key·TOTP encryption key는
별도 lifecycle입니다. cold restore는 source runtime 재시작과 authoritative replay 증거
보존이 필요합니다. 임의 DB rollback/live VM clone/독립 ledger는 external fencing 없이
지원되지 않으며 즉시 원격 계정 회수나 cross-host failover를 암묵 주장하지 않습니다.

[원천 scope 보완](2026-10-16-human-source-scope-binding.md): Human 시간 보고의 인증된 scope 지문이 필수이며 구현 검증은 진행 중입니다.
