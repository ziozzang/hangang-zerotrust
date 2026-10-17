# ADR 0021: 품계(Pumgye) 인가 모델 개정

[English](../adr/0021-pumgye-authorization-model-revision.md)

상태: **아키텍처 채택 — 2026-10-18**. 이 ADR은 Pumgye·Hopae·Sumunjang·Hangang 코드, 정책, 이미지, 배포를
바꾸지 않습니다. [ADR 0010](0010-pumgye-ownership.md)의 품계 소유 인가 *모델*을 개정하며,
[ADR 0013](0013-snapshot-membership-scaleout.md)·[ADR 0016](0016-decision-core-metadata-adapters.md)의
판정 코어·스냅샷 원칙은 유지합니다. Kubernetes 표현은 [ADR 0022](0022-kubernetes-native-world-package.md),
판정 이벤트 스키마/exporter는 ADR 0019, 통합 콘솔은 ADR 0020(병행 작성 중)이며 이 ADR은
그들이 사용하는 explain API를 정의합니다.

품질 기준: Okta/Auth0 FGA, Teleport, Cloudflare Access 인가 계층에 견줄 상용 제품입니다.
아래 기준은 개념 검증이 아니라 제품 인수 기준입니다.

> 채택 기록(사용자 재개 지시, 2026-10-18): 명시한 소유 경계와 상한·실패 시 거부하는
> 설계를 채택합니다. 구현은 서로 다른 미병합 검토 단위에 있으며 채택은 구현 완료·출시·배포·
> 보존 정책 활성화·conformance 주장이 아닙니다. 아래 배경은 설계 당시의 기준선입니다.
> 미결 질문과 단계별 인수 게이트는 백로그로 유지합니다.
> [현재 로드맵](ENTERPRISE_ROADMAP_2026-10-18.md)을 참고하세요.

## 배경: 확인된 현 모델 결함

근거: Pumgye `849ca90` `crates/pumgye-core/src/lib.rs` 14–137행(`Policy`, `Service`,
`Resource`, `Role`, `Network`), 230–440행(역할 해석·컴파일러), 447–510행(평가),
`docs/SERVER.md`, `docs/KUBERNETES.md`.

| # | 결함 | 근거 |
| --- | --- | --- |
| D1 | 개별 주체 ID 단위 할당만 존재, 그룹 주체 없음. LDAP/OIDC 그룹 사용 불가. | `users/workload_users/human_users: BTreeMap<String, Vec<String>>`. 별도 Kubernetes API 매핑에만 `required_groups`가 있음. Hopae `groups`는 *later*, Hopae LDAP 문서는 그룹에 명시적 Pumgye 매핑이 필요하다고 기술. |
| D2 | 하나의 개념에 세 개의 주체 맵. `users`는 임의 문자열을 받아 legacy 사람 주체, `s_` 서비스 주체, `k8sapi:` 주체가 섞임. | 같은 `s_` 값이 두 맵에 반대 권한으로 들어가는 kind 충돌 시험이 존재하는 이유. |
| D3 | 역할이 서비스마다 정의되어 동일한 역할이 N번 반복. | `Service.roles`, 서비스 내부에서만 상속 해석. |
| D4 | 정보등급이 역할과 자원 양쪽에 있음(RBAC + 임시 MLS). 설계된 Catalog 권한과 중복. | `Role.information_classes`, `Resource.information_class`, 64개 무순서 bitset. |
| D5 | `networks` CIDR→역할이 Sumunjang의 IP 집합 소유와 중복: "이 IP가 허용되는가"에 두 곳이 답함. | Pumgye 자체 `PrefixTrie`; Sumunjang은 allow/block/ASN pool radix 인덱스 소유. |
| D6 | 할당에 만료·사유·부여자·승인 없음, 명시적 deny 없음. | 역할 ID 목록과 합집합뿐. |
| D7 | Hopae 주체 삭제 시 고아 할당, 조정 없음, 콘솔은 해시만 표시. | Hopae 생명주기 피드 미소비. |
| D8 | 관리용 explain/dry-run 없음. `/v1/decision`은 판정 자격 증명 전용. | ADR 0019/0020 시뮬레이터에 필요. |
| D9 | Pumgye AAL은 0–3이나 Hopae는 사람에게 AAL1/2, 기계에 AAL0만 발급. AAL3는 별도 passkey 작업. | `minimum_aal <= 3`, Hopae `sessions.aal` 1 또는 2. |
| D10 | 서비스당 권한 64개, 등급 64개, 전체 할당 65,536 한도. | `vocabulary()`, `compile()` 한도. |

유지할 성질: 불변 스냅샷 위 결정적 평가, 요청 경로 DB 무호출, 기본 guest, Sumunjang deny 우선,
enforced Guard 요구를 observe/unavailable로 충족 불가, 미지 서비스·동작·등급 거부, revision
하한과 CAS 게시, bitset 고속 경로.

## 결정

Pumgye는 명시적 deny, 타 소유자 어휘 참조 조건, 할당 생명주기 메타데이터를 갖춘
**주체 / 그룹 / 역할 템플릿 / 바인딩** 모델을 채택합니다. 컴파일된 스냅샷은 bitset 기반이며
고속 경로에서 할당(allocation)이 없습니다.

| 개념 | 소유자 | Pumgye 보관 |
| --- | --- | --- |
| 주체 식별자(human, service, workload) | Hopae | 불투명 안정 ID 참조 |
| 그룹·멤버십(로컬, LDAP `memberOf`, OIDC `groups`) | Hopae | 바인딩의 그룹 참조, 스냅샷 내 멤버십 projection |
| 정보등급 어휘·자원 라벨 | Catalog(ADR 0003) | 템플릿별 **clearance 상한**만 |
| 네트워크 zone(이름 있는 prefix/ASN 집합) | Sumunjang | 조건·서비스 상한의 zone 참조 |
| 역할 템플릿, 서비스 권한 어휘, 바인딩, deny, 접근 요청 | Pumgye | 권한 원천 |
| 경로 → 서비스/자원/동작 바인딩 | Hangang(Catalog 바인딩) | — |

### 데이터 모델 개요

영문 원문의 스케치를 규범적 의도로 삼습니다(필드명 동일). 요점:

- `Principal = {kind: human|service|workload, ref}`; ref는 Hopae 소유·재사용 불가 ID
  (`human1:`, `s_`, 새 `wk2:` = issuer·cluster·namespace·ServiceAccount 이름·UID 해시; Pod UID는 감사 속성).
- `GroupRef = grp1:…`, 원천(local/ldap/oidc)과 외부 키는 Hopae 메타데이터.
- `RoleTemplate {permissions, inherits ≤ 8, clearance_ceiling{level, compartments}, minimum_aal, requestable}`.
- `ServicePolicy {permissions, permission_map, resources(Catalog 참조), network_ceiling[{zone, max}], require_guard, authorization_context}`.
- `Binding {effect: allow|deny, subjects ≤ 64, role 또는 deny permissions, scope, conditions{zones, minimum_aal, not_before, expires_at}, metadata{reason, granted_by(인증 주체), approval_ref, source}}`.

그룹 멤버십은 Hopae가 서명·revision된 **멤버십 projection**(현재 정책이 참조하는 그룹만)으로
제공합니다. Pumgye는 LDAP/OIDC를 직접 읽지 않고, Hangang이 전달한 헤더·토큰의 그룹명을 신뢰하지 않습니다.

### 평가 의미와 우선순위

순서대로 평가하며 첫 종결 결과가 이깁니다.

1. **Fence:** 스냅샷 신선도, `minimum_revision`, 멤버십·zone projection revision. 미충족 시 `Unavailable`(503).
2. **Context:** 미지 서비스 `UnknownService`, context 불일치 `PermissionDenied`.
3. **Sumunjang:** `Deny` → `GuardDenied`, `require_guard`인데 enforced allow 아님 → `GuardUnavailable`.
4. **Catalog:** 자원/동작 → 권한 bit와 라벨(level, compartments). 미지 동작 거부, 미지/`unknown` 등급 `ClassDenied`.
5. **주체:** Hopae 타입 증거의 kind 사용(문자열 접두어만으로 판단 금지, 불일치 시 거부). 항목·그룹 없음 → `Guest`.
6. **명시적 deny:** 일치하는 deny가 있으면 `ExplicitDenied`. **deny는 모든 allow보다 우선.**
7. **Allow 집합:** 유효 기간·zone 조건이 맞는 allow 바인딩(직접+그룹)의 합집합. 없음 → `Guest` 또는 `NetworkGuest`.
8. **네트워크 상한:** 가장 구체적인 상한 zone으로 교집합(현재 longest-prefix 덮어쓰기, 더 구체적인 guest 포함 보존). 상한은 권한을 줄이기만 함.
9. **권한:** bit 없음 → `PermissionDenied`.
10. **Clearance:** 요청 권한을 *부여한 템플릿*의 상한으로 등급·compartment 검사(템플릿별 평가, 등급 합집합 금지).
11. **Assurance:** AAL ≥ max(템플릿, 바인딩, 자원) 아니면 `AssuranceDenied` + 요구 AAL obligation(Hopae step-up용).
12. `Allow`.

### AAL 정렬

AAL0 = 비인간 증거, AAL1–3 = Hopae가 발급하는 NIST SP 800-63B 수준. 현재 Hopae는 AAL1/2만
발급하며 AAL3는 passkey 작업으로 추가됩니다. Hopae가 AAL3 능력을 알리기 전 AAL3 요구는
`UnsatisfiableAssurance` 경고로 컴파일되며 절대 하향되지 않습니다. 사람/기계 kind는 컴파일 시 검사합니다.

### 명시적 deny와 break-glass

deny 바인딩은 사고 대응용이며 긴급 deny는 우선 배포됩니다(ADR 0022 빠른 회수 경로).
deny를 우회하는 break-glass allow는 없고 긴급 접근은 승인·감사가 있는 JIT 부여(P2)입니다.

### 할당 생명주기와 JIT

- `expires_at`/`not_before`는 고속 경로에서 정수 비교 1회, 다음 만료 경계에 재컴파일 예약.
  만료 없는 바인딩은 운영 모드에서 사유 필수.
- `granted_by`는 게시 전송로의 인증된 관리자(현재 클라이언트 인증서 지문, ADR 0009/0020 이후 위임된 콘솔 actor), 문서 본문 값은 불가.
- **JIT(P2):** `AccessRequest` → `requestable.approvers` 승인(자기 승인 불가) → `source: jit:<id>` 시간 제한 바인딩, 전 과정 감사(ADR 0019).
- **접근 검토(P2):** who-can/what-can 기반 정기 인증 캠페인.

### 고아 조정과 표시 이름

Hopae는 outbox로 주체 생명주기 피드(`created/disabled/enabled/deleted/merged`)와 그룹 변경을 게시하고
Pumgye가 소비합니다. `deleted`면 해당 바인딩은 즉시 컴파일에서 제외되는 **고아**가 되어 감사 보존 기간 동안
읽기 전용으로 남고, `disabled`는 표시만, `merged`는 권한을 자동 이전하지 않고 검토 항목을 만듭니다.
유실은 watermark와 주기적 전체 조정으로 탐지하며, 해석 불가 참조가 있는 새 바인딩 게시는 실패합니다.
Pumgye는 이름·이메일을 저장하지 않고, 콘솔이 관리자 위임 권한으로 Hopae 디렉터리를 일괄 조회합니다.

### 관리용 explain·시뮬레이션 API

판정 자격 증명과 분리된 관리 API(관리 mTLS/위임 콘솔 actor):

- `POST /v2/admin/explain` — 주체(또는 가상 주체와 그룹), 서비스, 자원·동작, IP 또는 zone, AAL,
  가정 Guard 증거, 스냅샷 선택(현재/revision/후보) → Decision, 사유, obligation, **단계별 순서 trace**
  (각 단계의 입력, 일치한 바인딩·템플릿·상한·deny ID와 출처, 결과).
- `POST /v2/admin/candidates`, `…/diff` — 미게시 문서 컴파일과 권한 변화 집합.
- `GET /v2/admin/who-can`, `GET /v2/admin/what-can` — 역방향/정방향 유효 권한.

구현 규칙: explain은 **동일한 평가 함수**를 trace sink 제네릭으로 사용합니다. 운영 경로는
크기 0 `NoTrace`로 단형화되어 trace가 사라지고 explain은 제한된 `VecTrace`를 씁니다.
PPG1/HTTP/gRPC와 동치성 시험을 둡니다. explain은 속도 제한·감사되며 허가로 캐시되지 않습니다.

### 컴파일 스냅샷 영향

- 템플릿은 컴파일 시 `permission_map`으로 서비스별 bitset이 됩니다. 어휘는 `[u64; 4]`(256개)로 확대.
- 서비스별 세 맵 대신 스냅샷당 하나의 `HashMap<PrincipalRef, PrincipalEntry>`; 항목은 평탄
  `Vec<GrantEntry>` 범위와 `GroupMask([u64; 4])`를 가집니다.
- `GrantEntry`는 고정 크기 `Copy`(서비스, allow/deny 마스크, zone 마스크, clearance, AAL, 유효 구간).
  주체·서비스당 ≤ 64 항목과 그룹 bit(≤ 256)만 순회합니다.
- Zone: Sumunjang 소유 prefix trie 1회 조회로 `ZoneMask`와 상한 승자를 얻어 기존 서비스별 trie·hosts를 대체.
- P0 한도: 직접 바인딩 주체 1,048,576, 그룹 65,536(서비스당 관련 256), 서비스 4,096, 템플릿 1,024,
  바인딩 1,048,576. 기준 8코어 호스트에서 컴파일 ≤ 2초, ≤ 1 GiB RSS를 GA 전 측정·공개.
- 회귀 하한: `0409a7a`의 138–142k 판정/초 대비 동일 cardinality에서 10% 이내.

### wire 호환

P0에서 PPG1/HTTP/gRPC 요청 형식은 그대로입니다. kind는 Hangang이 이미 전달하는 Hopae 타입 증거에서 얻고,
class 필드는 Catalog 라벨과 같아야 하며 다르면 거부합니다(클라이언트 권한 분류 금지). 응답 코드는
`ExplicitDenied`, `Unavailable`로 확장하고 구형 peer에는 가장 가까운 기존 거부 코드를 보냅니다.
zone 마스크·AAL obligation을 담는 PPG2는 P1, ALPN 협상.

### Kubernetes 권한 모드 호환

Kubernetes 모드(ADR 0022)에서 같은 모델은 `world.hangang.dev`의 `AccessRoleTemplate`, `AccessPolicy`,
`AccessBinding`(주체 `ServiceAccount`, `Group`, `Principal`)으로 표현되고, world controller가 동일한 v2
문서로 컴파일해 서명 스냅샷으로 전달합니다. 기존 RBAC→애플리케이션 매핑은 `observe`/가져오기 어댑터로만
남고, `kubernetes_api` context와 SAR 서버는 변경 없이 보류합니다.

## 정책 v1에서의 이행

결정적 변환기(`pumgye migrate v1-to-v2`)가 v2 문서, 타 소유자 제안, 보고서를 생성합니다.

1. **역할 → 템플릿** `<service>.<role>`; 서비스 간 동일 역할은 병합 후보로만 보고, 관리자 확인 후 병합.
2. **주체:** `human_users` → human, `workload_users` → workload(5단계), `users`는 Hopae 조회로 분류;
   해석 불가 항목은 **이행하지 않음**(fail closed). kind 충돌은 서로 다른 kind의 두 바인딩으로 보존.
3. **네트워크 → zone + 상한:** 각 CIDR은 Sumunjang zone 제안 `legacy.<service>.<n>`과 `network_ceiling`이 됨.
4. **등급:** 어휘·자원 등급 → Catalog 제안. 역할 등급 집합이 하향 폐쇄일 때만 상한으로 변환, 아니면 compartment 제안/검토. 묵시적 확대 금지.
5. **Pod 결속 워크로드 부여:** 관리자가 namespace/ServiceAccount를 확인한 경우에만 `wk2:`로 변환, 아니면 deprecated legacy로 유지.
6. **shadow·전환:** v1 옆에서 v2를 observe로 실행하고 생성 corpus(주체×서비스×권한×상한 zone×등급×AAL 경계)와
   실트래픽을 비교. 7일(또는 운영자 승인 기간) 무설명 불일치 0과 승인 기록이 전환 조건. 롤백은 v1 문서 재게시(90일 보관).

## 검토한 대안

- **Cedar 코어 채택:** Rust·형식 분석·forbid 우선이 장점이나 요청별 entity 구성과 해석이 할당·정책 수 비례 비용을
  만들어 bitset/100k 목표와 ADR 0016에 어긋남. deny 우선·스키마 검증 아이디어는 채택, 오프라인 검증용 Cedar export는 P2 후보.
- **OpenFGA/Zanzibar ReBAC:** 객체 공유 그래프에 탁월하나 tuple store 그래프 탐색과 일관성 토큰이 필요.
  게이트웨이 거친 판정에는 부적합, 애플리케이션 수준 어댑터 후보로 유지.
- **OPA/Rego:** 범용이나 비용·메모리 한계가 정책 의존적. 코어로 거부.
- **v1 유지 + 그룹 맵:** D2–D7과 소유 중복이 남아 거부.
- **Pumgye가 그룹 소유:** 두 번째 디렉터리가 되어 거부(ADR 0001/0002).
- **Sumunjang 증거에 zone 멤버십 포함:** 평가자를 하나로 줄이나 PPG/HGD wire를 결합하고 `require_guard=false`
  서비스에 도움이 안 됨. PPG2/HGD 개정(P1)에서 재검토. P0은 Sumunjang 소유 zone 스냅샷을 읽기 전용으로 가져와 IP 집합 *소유자*는 하나.

## 단계 계획과 인수 기준

**P0(ADR 0022 P0 선행):** v2 스키마·예제·컴파일러·평가기, explain(`NoTrace`/`VecTrace` 동치), 후보 diff,
변환기·shadow. Hopae 멤버십 projection·생명주기 피드(로컬/LDAP/OIDC). Sumunjang `NetworkZone`과 zone 스냅샷.
게이트: 성질 시험(deny 단조성, 상한은 감소만, 바인딩 없이는 권한 없음, kind 격리, 만료), 적대 fixture(헤더 그룹 위조,
고아, AAL3 불가, class 헤더 불일치), 기존 corpus v1/v2 동치, `0409a7a` 대비 10% 이내 성능과 한도 측정,
원격 k3s 실제 4개 컴포넌트 요청 경로(ADR 0022 게이트).

**P1(운영):** 영향 diff가 있는 콘솔 바인딩 편집, who-can/what-can, 고아·비활성 화면, 이름 해석,
trace 샘플 이벤트(ADR 0019), PPG2, 증분 컴파일, 사유 필수. 게이트: 편집→diff→게시→explain 실제 브라우저 검증,
감사 완전성, Hopae 그룹 멤버십 제거가 ADR 0022 회수 SLO 안에 접근을 제거.

**P2(거버넌스):** JIT 승인, 접근 검토 캠페인, Cedar export 검증, ReBAC 어댑터 평가. 게이트: 자기 승인 금지,
시계 시험 하의 만료(ADR 0018), 캠페인 증거 export.

GA는 서명된 릴리즈 산출물에서 P0·P1 게이트 통과, v1에서의 업그레이드·롤백 문서화, 정책·감사 백업/복구가 조건입니다.

## 결과

하나의 주체 모델, 그룹 기반 관리, 재사용 역할, 등급·네트워크 집합의 단일 소유자, 감사 가능한 할당
생명주기, 사고 대응 deny, 콘솔·exporter가 요구하는 설명 가능성을 얻습니다. 비용: Hopae 그룹·멤버십
projection·생명주기 피드, Sumunjang zone, v2 스키마·변환기, 소유자 간 revision fence로 인한 `Unavailable`
감시 필요, 모호한 v1 문서에 대한 관리자 작업.
