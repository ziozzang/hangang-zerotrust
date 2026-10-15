# 네이티브 요청 경로 계측과 원천 snapshot 후속 단계

상태: 2026-10-16 후속 설계다. 실제 Human 네 코어 기능 검증이 우선이며 이 문서는 route·RPC·운영 설정을 활성화하지 않는다. [English](../reviews/2026-10-16-native-hotpath-snapshot-design.md).

검토 소스는 로컬 Root 후보 `f369c526e4f4cbd6d10659a002039eb0fb8355dc`, 공개 Pum `f6fb7d9a7e92b615d3c2525999b55a66e7a491ac`, 로컬 H4 후보 `fe3a9d8e7d6373c76b4ef99d54a70b13d7ef8ed7`다. 두 로컬 후보를 공개 dependency나 운영 완료로 표현하지 않는다. 정확한 함수·행 위치는 영문 표에 기록했다. 소스만으로 RPS·지연·할당 합계를 추정하지 않는다.

## 실제 남은 요청 경로

- Pum 점결정은 이미 DB가 게시한 동일 불변 CompiledPolicy/View를 ArcSwap으로 읽으며 요청별 SQL이 없다. 이를 별도 cache/정책 엔진으로 바꾸면 안 된다.
- Hop native Verify는 실제 인증 후 canonical Human 정책 좌표 조회에도 SQL을 사용한다. Human capture/current·Issue·Observe는 session/handle/user/provider/config/realm/primary material·AAL2 TOTP 상태를 결합하는 durable current SQL을 반복한다. OIDC/LDAP primary 로그인을 Observe마다 다시 하지는 않지만 DB-free Observe는 아니다.
- Store read는 pooled SQLite reader와 spawn_blocking을 사용하고, write는 내부 mpsc/oneshot·직렬 writer로 이동한다. 이는 프로세스 내부 스케줄링이며 외부 IPC라고 부르면 안 된다. 매 요청 새 DB 연결이라고 단정하지도 않는다.
- Pum observed permit은 실제 Hop·Sum·route·plan 관측 RPC를 호출하고 서명 전후 current fence를 반복한다. Pum 점결정의 in-memory 특성과 전체 RPC 경로 비용은 다르다.
- H4는 local Source current와 실제 Pum Observe, samewriter current를 검사한다. canonical pair ledger는 IMMEDIATE 거래에서 두 nonce·만료 보존 index·count·key registry·native current를 원자적으로 검사/기록/commit한다. reply 준비 후 current SQL도 남는다.
- Root는 단일 body frame의 Bytes를 복사 없이 유지하지만 분할 body는 기하급수적으로 늘어나는 Vec에 합친다. 현재 Human body hash는 초기 H1v2·재확인·SDK actual prepare의 세 번이다. SDK 내부 bind_actual 한 번과 전체 경로 한 번은 다른 주장이다. URI/header seal과 작은 scope fingerprint 계산·protobuf/문자열 할당도 별도다.
- 최종 raw write/TLS flush·route/current fence는 효과 경계이며 성능을 이유로 없애거나 pooled client가 요청 owner보다 오래 보유하게 하면 안 된다.

## M1: 실제 Store 원천 snapshot

첫 작은 단계는 실제 Store/incarnation·issuer·UID에 결합된 불변 canonical 정책 좌표를 사용하여 반복 metadata SQL만 제거하는 것이다. 이 값은 session·MFA·grant가 아니며 current 적격성 SQL을 대체하지 않는다. 그 다음 모든 mutation의 게시/철회 경계가 검증되면 readonly Human Observe를 동일 native source snapshot과 비교하도록 옮긴다. 기존 joined SQL은 테스트 oracle이며 불명확한 상태의 낙관적 fallback은 금지한다. request마다 전체 session map을 복제하지 않는다.

필수 writer 목록은 handle 생성/rotation/logout/termination/expiry, primary 재인증·identity link, user disable·credential/authz/groups, TOTP 등록/삭제·factor downgrade, provider/config/material/realm 변경이다. 누락된 writer는 stale cache 허용 범위가 아니라 보안 결함이다. revision은 단조 증가하고 overflow는 거부한다.

단일 owner 제안 상태는 `eligible(old) → pending/ineligible → durable commit → 검증된 immutable publication(new)`이다. DB commit 전에 grant를 게시하면 rollback 시 허위 grant가 생긴다. commit 뒤에만 snapshot을 바꾸고 그 사이 old owner를 유지하면 철회가 지연된다. pending을 먼저 닫고 commit·검증·게시를 완료해야 한다. 실패한 게시가 이미 철회된 capture를 복구해서는 안 된다. 이전 capture는 원래 generation·Store·clock domain·기한을 유지하며 새 snapshot으로 갈아타지 않는다.

| 구현 가능한 결정적 시험 | 필수 결과 |
|---|---|
| pending 뒤 SQL 전 writer를 멈추고 Observe 경쟁 | 이전 proof 거부, 원래 source age 유지 |
| logout/disable/factor 삭제 commit 뒤 publication 전 정지 | Observe·H4 writer가 오래된 eligible snapshot으로 통과하지 않음 |
| pending 뒤 SQL rollback | 새 grant·generation 비공개, 이전 retired capture 복구 금지 |
| commit 전/commit 후 publish 전/publish 후 ack 전 실제 자식 kill | 재시작 시 검증된 DB를 hydrate한 뒤 readiness, lost ack 명시적 조정 |
| 늦은 오래된 게시·변경 없는 동시 게시·material A→B→A | prepared generation CAS·정확한 Store/Arc·late latch로 stale/ABA 거부 |
| callback/SQL/writer 대기 중 원래 기한·suspend jump·시계 오류/반전 | 원래 anchor/domain 유지, 실패 latch; 정상 reverse completion은 허위 rollback으로 처리하지 않음 |
| 실제 OIDC/LDAP/AAL1·TOTP2와 SQL oracle 비교 | 동일 사용자별 provenance·scope·적격성; 전역 user revision floor 금지 |
| 외부 Store/realm·record miss·generic session | 동일 label/config만으로 통과하지 않음 |
| pair writer 취소·응답 유실 | commit 전 rollback, commit 뒤 pair가 소모될 수 있으나 재사용 금지 |
| hydrate 손상·gap·원천 단절 | readiness 거부, 빈 기본 snapshot으로 서비스 금지 |

DB 안의 generation만으로 전체 DB의 오래된 정상 backup 복원을 탐지할 수는 없다. realm·무작위 ID는 live clone 탐지 수단이 아니다. 자동 antirollback은 별도의 신뢰 가능한 단조 epoch/checkpoint 또는 서비스를 중지하고 기존 signing/source/session domain을 철회하는 검증된 복구 절차가 필요하다. M1은 이 지원 범위를 명시하고 시험해야 한다. 임의 SQL 변조·clone 방어, 외부 DBMS·분산 writer/follower 선형성을 주장하지 않는다.

## M2: 실제 SDK prepare 한 번

동일한 최종 선택 요청에 실제 body SDK 준비를 한 번 수행하고 private immutable prepared request·digest/body hash·compiled Scope·원래 frontend context·소유 Bytes를 유지한다. Route capture와 최종 비교가 이 데이터를 사용하게 하여 같은 body 재hash를 없앤다. 고정 scope fingerprint는 설정 compile 때 cache할 수 있다. 공개 prepare-from-digest·숫자 Observation factory·caller hash 입력은 금지한다.

v1·독립 H1v2 golden vector, empty/nonempty·같은 길이 body 변조, 단일/분할 frame, trailer/초과/느린 body, 헤더 없음/빈 값/중복/control, forwarding authority와 선택 origin 분리, stale revision·다른 scope, 최종 backend body SHA를 검증한다. 준비 뒤 mutable alias를 전달하지 않는다. 최종 URI/header/credential slot/framing seal과 transport fence는 유지한다.

## 계측과 공개 기준

먼저 테스트 전용으로 SQL 거래/문장·reader 재사용/생성·writer 대기/commit·RPC method class·body 수집/복사량·hash 횟수·scope 계산·record/quota·취소/실패 단계를 낮은 cardinality로 센다. 비밀·쿠키·사용자 ID·본문·전체 context는 기록하지 않는다. 최종 SQL/time fence 뒤 임의 counter callback을 넣지 않는다. production 전역 atomic counter 경합도 측정 없이 비용이 없다고 주장하지 않는다.

동일 exact source/input의 실제 기능 baseline을 먼저 만들고 provider/AAL별 조건부 비용을 분리한다. 이후 M1/M2 allocation·메모리·tail latency를 비교한다. 벤치는 하드웨어·버전·동시성·body/frame·provider/network·기간·실패·durable commit·시계/원천 의미를 명시해야 한다. bounded map·가짜 signer·in-memory microbenchmark는 전체100kRPS·production zeroSQL 증거가 아니다.

Service·Workload·generic 기본 wire/동작은 유지한다. 실제 provider/native/pair/backend와 해당 workspace/strict gate, exact hash 독립 검토 뒤에만 pin을 원자적으로 공개한다. SAR는 이미 구현·실제 API-server 검증됐다. 역방향 TokenReview 인증 webhook·admission/controller·외부 DB/분산 원천은 별도 남은 목표다. 이 설계로 릴리즈·운영 반영이나 전체 완료를 주장하지 않는다.
