# ADR 0022: Kubernetes 네이티브 Hangang World 패키지

[English](../adr/0022-kubernetes-native-world-package.md)

상태: **제안**. [ADR 0015](0015-kubernetes-iam-authority.md)를 부분 대체합니다(원천 표현, Kubernetes 모드의
인가 lease 길이, 워크로드 신원 단위, 패키징 순서). ADR 0015의 소유 규칙, RBAC/IAM 의미, 안전 불변식은
유지됩니다. [ADR 0013](0013-snapshot-membership-scaleout.md), [ADR 0016](0016-decision-core-metadata-adapters.md),
[ADR 0021](0021-pumgye-authorization-model-revision.md) 모델 위에 세우며 판정 이벤트는 ADR 0019, 통합 콘솔은
ADR 0020입니다. 클러스터·이미지·차트·운영 설정은 바꾸지 않습니다.

품질 기준: Helm/OCI, 서명 이미지, 업그레이드/롤백, HA, 백업을 갖춘 운영급 Kubernetes 패키지이며 Teleport,
Cloudflare Zero Trust에 견줄 운영 경험. 아래 게이트는 제품 인수 기준입니다.

## 배경: 확인된 현재 상태

확인 revision: Hangang(`hangang-console-plugins`) `d6cb223`, Hopae(`hopae-hangang-integration`) `519aa58`,
Sumunjang(`hangang-safe`) `1300ecb`, Pumgye `849ca90`, 이 저장소 `447e1c9`.

- **패키징:** Helm/operator 없음. 4서버 실행은 테스트 생성기 `tools/kubernetes_world_smoke.py`뿐이며 문서도
  운영 배포 번들이 아니라고 명시. 조각: Hangang kustomize(placeholder 이미지, `emptyDir`, `replicas: 1`),
  Pumgye kustomize(`replicas: 1`, `Recreate`, PVC), Sumunjang YAML 템플릿 2개, Hopae는 compose만.
  이미지는 로컬 빌드 후 노드에 import, registry 게시·서명 없음. Secret 사전 생성, cert-manager/SPIRE·회전 없음,
  모든 권한 소유자가 SQLite 단일 writer. 원격 테스트 클러스터의 운영 게이트웨이는 클러스터 밖 host network에서 실행.
- **Hangang 라우팅:** `src/ingress.rs` 86–87, 190–191행이 Ingress 생성 경로에 `pumgye: None`,
  `pumgye_authority: None`을 설정하고 annotation은 버림. Gateway API 미지원. Service는 type 없음(ClusterIP),
  `externalTrafficPolicy`/PROXY protocol 없음 → Sumunjang IP 규칙이 SNAT 주소를 봄. 컨트롤러의 watch/소유/상태 품질은 높음.
- **Sumunjang:** NetworkPolicy/selector 의미를 userspace에서 진단용으로 컴파일하며 런타임 집행으로 승격하지 않음.
  승격해도 집행점은 게이트웨이(남북)뿐이라 Pod selector ingress는 거의 무의미하고 동서 트래픽은 보이지 않음.
  `SumunjangPolicy` CRD는 고정 이름 객체 하나를 500ms마다 GET, 1초 lease, `preserve-unknown-fields`, watch·status 없음.
- **신선도:** Pumgye Kubernetes 모드는 수집 전 가용성을 철회하고 수집 시작 1초 후 만료, Sumunjang도 1초 lease.
  API 서버 순간 장애·느린 list·잘못된 객체 하나가 보호 트래픽 전체 503이 됨. Hangang Ingress는 60초 staleness와
  마지막 스냅샷 유지. 세 가지 의미가 공존.
- **워크로드 신원:** namespace, SA 이름/UID, Pod 이름/UID 해시. 같은 SA의 다른 Pod는 guest, 롤아웃 후 부여 소멸.
  Hangang은 별도 정적 SPIFFE mTLS 모델 → 두 신원 모델.
- **Hopae 요청당 API 호출:** 매 인증마다 TokenReview + SA/Pod 메타데이터 GET, 결과 캐시 없음(`kubernetes.rs` 367–395행).
- **SAR authorizer:** Webhook/Deny만 있는 일회용 API 서버에서만 검증. 실제 클러스터에선 자신을 스케줄하는
  API 서버를 인가하는 순환, RBAC 뒤에선 가치 적음.
- **권한 모호성:** ADR 0015는 "Kubernetes가 원천"과 "Hangang World가 도메인 소유"를 동시에 말하고 실제 원천은
  컴포넌트마다 다름. 사용자 요구는 Hangang World zero-trust 권한이 **원래 도메인 원천**인 단일 네이티브 패키지.

**유지:** fail-closed, UID/resourceVersion fence, 완전 relist 후 게시, Secret 참조, nonroot scratch 이미지,
최소 권한 RBAC, Hangang Ingress watch/소유 품질, 게이트웨이와 CNI 집행의 정직한 구분 보고.

## 결정 1 — 권한: World 객체가 원천, Kubernetes는 저장소

- 단일 API 그룹 **`world.hangang.dev`**. Kubernetes는 발행자가 통제하는 도메인의 DNS 하위 도메인을 요구하며
  프로젝트는 이미 `policy.hangang.dev`를 사용. `world`는 컴포넌트가 아닌 도메인 권한을 가리키며 버전·변환을
  하나로 묶고 kind별 소유자는 분리. *미결:* v1beta1 전 `hangang.dev` 등록 통제 확인, 아니면 beta 전 개명.
- 클러스터 내에서는 **World CRD가 도메인 원천**. Kubernetes는 저장(etcd), 편집 RBAC, admission, watch,
  GitOps를 제공. Namespace/SA/Pod/Service/EndpointSlice/NetworkPolicy/RBAC는 **플랫폼 사실**이며 도메인 권한이
  아님. Kubernetes RBAC는 애플리케이션 권한으로 가져오지 않음(observe/가져오기 어댑터).
- 컴포넌트 DB는 컴파일 스냅샷의 **물질화 캐시**와 정책 외 데이터(Hopae 사용자·자격 증명·세션, 감사 spool).
  CRD 소유 도메인에 대한 네이티브 DB 쓰기는 거부.
- `WorldAuthority`(클러스터 단일 `default`)가 클러스터 ID, trust domain, 도메인별 `kubernetes|database|observe` 선언.
- **클러스터 외부 배포**는 `database` 모드이며 같은 스키마가 가져오기/내보내기·GitOps 형식. World당 도메인마다
  권한은 정확히 하나, 병합 없음, 모드 전환은 감사되는 명시적 이행(내보내기→검증→writer 동결→가져오기→marker 전환)과 롤백.
  다중 클러스터(P2)는 World당 원천 클러스터 하나.

## 결정 2 — CRD API(`v1alpha1` → `v1beta1` → `v1`)

| Kind | 범위 | 소유 | 목적 |
| --- | --- | --- | --- |
| `WorldAuthority` | Cluster 단일 | controller | 클러스터 ID, trust domain, 원천 모드, staleness 한도 |
| `WorldIdentityProfile` | Namespaced | Hopae | 인증 프로필(OIDC/LDAP/로컬/API key/Kubernetes 워크로드/SPIFFE, Secret 참조), AAL·세션 정책 |
| `IdentityGroupMapping` | Cluster | Hopae | LDAP `memberOf` DN/OIDC `groups` 값 → Hopae `GroupRef` |
| `AccessRoleTemplate` | Cluster | Pumgye | ADR 0021 역할 템플릿 |
| `AccessPolicy` | Namespaced | Pumgye | 서비스 권한 어휘, 매핑, Catalog 자원 참조, zone별 네트워크 상한 |
| `AccessBinding` | Namespaced | Pumgye | allow/deny, 주체 `ServiceAccount{namespace,name[,uid]}`/`Group`/`Principal`, 조건·만료·사유 |
| `CatalogResource` | Namespaced | Catalog | 자원 식별, 동작, 분류 라벨 |
| `NetworkZone` | Cluster | Sumunjang | 이름 있는 prefix/ASN 집합 |
| `NetworkControl` | Namespaced/Cluster | Sumunjang | 차단/허용/위험 규칙, 동서 의도(`SumunjangPolicy` 대체) |
| `ProtectionPolicy` | Namespaced | Hangang | Gateway API **direct policy attachment**(`targetRefs` → Gateway/HTTPRoute/GRPCRoute), 신원 프로필, AccessPolicy, 동작 매핑, 네트워크 요구, 실패 모드 |

API 규칙: `preserve-unknown-fields` 없는 구조적 스키마, 모든 문자열·목록의 상한, 로컬 불변식용 CEL 검증,
`observedGeneration`과 `Accepted/ResolvedRefs/Programmed/Ready` 조건(ProtectionPolicy는 Gateway API 정책 상태 관례),
`appliedRevision`과 권한 소유자별 ACK. 교차 객체 검증은 controller가 status로 보고하며 admission은
권한 소유자 가용성에 의존하지 않음.

**권한 상승 통제:** ValidatingAdmissionPolicy(CEL `authorizer`)로 allow 바인딩 생성 시 템플릿에 대한 사용자 정의
`bind` 동사, 템플릿 권한 변경 시 `escalate`를 요구. `world-admin/editor/viewer` 집계 ClusterRole 제공.
**버전:** v1beta1부터 변환 webhook(HA)과 저장 버전 이행, 제공 버전 제거는 경고와 함께 한 minor 이후.

## 결정 3 — 단일 controller, 서명 스냅샷, 제한된 staleness

- **`hangang-world-controller`**(2개 이상, Lease 리더 선출)가 World kind와 필요한 플랫폼 사실을 informer로 감시,
  검증·참조 해석·도메인별 후보 컴파일·status 기록.
- 첫 게시는 완전 동기화 후. 스냅샷은 revision+digest+epoch, controller 키(Ed25519)로 **서명**, 권한 소유자가 여는
  mTLS 구독 스트림으로 전달(xDS 방식: 전체 후 delta, 실패 시 사유와 NACK). 소유자는 서명·epoch·단조 revision·스키마
  검증 후 요청 경로 밖에서 컴파일·원자 교체·ACK.
- **데이터 평면은 마지막 정상 스냅샷을 제한 시간 동안 사용:** `maxSnapshotStaleness` 기본 5분(1–60분).
  10초마다 서명 heartbeat로 갱신. 한도 초과 시 보호 트래픽 fail closed, 그 전에 경보. 스냅샷 없는 새 Pod는 Ready 아님.
  권한 소유자는 정책용 API 서버 자격 증명을 갖지 않음.
- **빠른 회수:** 바인딩 삭제/deny, 긴급 deny, zone 차단, SA/Pod 삭제 tombstone, Hopae 주체 비활성은 우선 delta.
  SLO: 정상 control plane에서 API commit→모든 Ready 복제본 집행 p99 ≤ 2초. Hopae 세션 회수와 증거 lease(≤ 1초)는 변경 없음.
- **요청 경로에서 제거:** Pumgye·Sumunjang의 1초 API 관측 lease와 수집 전 철회. Kubernetes 모드에서 ADR 0015의
  "인가 lease 최대 1초"를 대체: 정책 신선도(분 단위, 명시·가시)와 증거/회수 신선도(초 단위)를 분리.
  Hangang 60초 규칙도 `snapshotAge`, `maxSnapshotStaleness`, `appliedRevision` 공통 보고로 정렬.
- 명시적으로 수용하는 위험: control plane 분할 중 제거된 부여가 한도까지 남을 수 있음. 완화: 도메인 관리 API로 직접
  긴급 deny(감사, controller가 CRD로 재조정), 한도 최소 1분, 분할 경보.

## 결정 4 — 집행점

- **남북: Hangang이 Gateway API 구현.** `GatewayClass` `hangang.dev/gateway-controller`, Gateway, HTTPRoute,
  GRPCRoute(P1), ReferenceGrant, 적합성 시험을 릴리즈 게이트로. `requireProtection` Gateway 아래 보호 정책 없는 경로는
  `Accepted=False` — 보호 없이 조용히 게시하지 않음.
- **Ingress**는 기존 의미(보호 없는 라우팅)로 호환 유지, 보호 Gateway 호스트와 겹치면 거부.
- **클라이언트 IP 보존 필수**(네트워크 조건 사용 시): `externalTrafficPolicy: Local`, 신뢰 LB CIDR의 PROXY v2,
  bare-metal용 `hostNetwork` DaemonSet. `none`이면 zone 조건 정책은 `Programmed=False`(`ClientAddressUnavailable`).
- **동서는 CNI에 위임.** Sumunjang은 (a) 게이트웨이 남북 IP 승인/위험 엔진, (b) `NetworkControl` 동서 의도를
  NetworkPolicy 또는 지원 시 CiliumNetworkPolicy/AdminNetworkPolicy로 생성하는 **생성기**(소유 라벨, dry-run diff,
  drift 교정), (c) 진단으로 재배치. 게이트웨이에서 Pod selector NetworkPolicy 집행 목표는 중단. 지원 CNI가 없으면 그렇게 보고.
- **서비스 간 L7(P2, 선택):** Hangang waypoint/sidecar 또는 Envoy `ext_authz` 어댑터.

## 결정 5 — 워크로드 신원과 컴포넌트 간 신뢰

- **워크로드 주체 = (cluster, namespace, ServiceAccount)**, Pod 이름/UID는 감사 속성. 정규형은
  `spiffe://<trust-domain>/ns/<ns>/sa/<sa>`, Hopae `wk2:`는 SA **UID** 포함(같은 이름 재생성은 새 주체).
  `AccessBinding`은 SA 이름으로 지정하고 controller가 현재 UID를 해석, `uid` 고정도 가능.
- **요청당 API 호출 없는 검증:** 전용 audience·짧은 수명(≥ 600초)의 projected SA 토큰을 클러스터 OIDC discovery/JWKS로
  **오프라인** 검증(issuer 고정, JWKS 회전 캐시, audience·만료·Pod/SA 결속 claim). 삭제는 controller tombstone을
  Hopae에 빠른 회수 delta로 전달. TokenReview는 짧은 긍정 캐시(≤ 10초)를 둔 선택적 fallback.
- **또는 SPIFFE X.509-SVID**(SPIRE, cert-manager `csi-driver-spiffe`). Hangang 워크로드 mTLS의 URI SAN을 **같은** 주체로 매핑.
- **컴포넌트 간 mTLS**는 cert-manager `Certificate`(차트 Issuer 또는 외부), 컴포넌트별 SPIFFE URI SAN, 기본 30일·2/3 시점 갱신,
  재시작 없는 hot reload. `tls.mode: external`도 같은 reload 요구.

## 결정 6 — 패키징, HA, 업그레이드, 백업

- **차트:** `hangang-world`(4개 컴포넌트+controller, 토글)와 `hangang-world-crds`(동일 버전, Helm이 `crds/`를
  업그레이드하지 않으므로 분리), **OCI** 게시·서명, `values.schema.json`으로 불완전 설정은 설치 전 실패.
- **이미지:** amd64/arm64, nonroot scratch, OCI registry, 차트에서 **digest 고정**, cosign 서명, SBOM(SPDX), SLSA provenance,
  admission 검증 예시.
- **HA·상태 결정:** SQLite 단일 writer는 단일 복제본 `database` 모드(개발·소규모)에만 유지. HA는 **PostgreSQL**
  (외부 또는 선택 시 CloudNativePG)로 ADR 0013 CAS+outbox 어댑터를 구현하며 CRD 외 데이터(Hopae 사용자·자격 증명 참조·
  그룹·세션, database 모드 Pumgye/Sumunjang, 감사 spool)를 담음. Kubernetes 모드의 Pumgye/Sumunjang은 권한 DB가 없는
  무상태 복제본(N ≥ 2). Hangang 데이터 평면은 무상태, 콘솔 관리는 Hopae SSO(ADR 0009)와 bootstrap 로컬 관리자만.
  controller는 Lease 기반 active/standby, 권한 소유자는 정책을 쓰지 않으므로 리더 선출 불필요.
- **가용성 기본값:** PDB, topology spread, anti-affinity, `maxUnavailable: 0`/`maxSurge: 1`, 적용 revision 기반 readiness,
  graceful drain, 자원 요청/한도, World namespace NetworkPolicy, ServiceMonitor/PrometheusRule.
- **업그레이드/롤백:** 스냅샷 스키마·wire·DB 스키마 N-1 호환(expand/contract, Helm pre-upgrade Job, contract는 한 릴리즈 뒤),
  controller는 연결된 모든 소유자가 받는 최고 스키마를 송출, `helm rollback` N-1 시험, 제공 버전 내 CRD 변경은 추가만.
- **백업/복구:** CRD는 GitOps/Velero, PostgreSQL PITR, 서명 키·CA·Secret 백업, revision/epoch fence가 있는 복구 runbook
  (복구된 controller는 새 epoch, 소유자는 운영자 재승인 없이 이전 epoch의 낮은 revision을 거부).

## 중단 / 폐기

| 중단 | 대체 |
| --- | --- |
| Pod UID 결속 워크로드 신원을 부여 주체로 사용 | SA 수준 `wk2:`/SPIFFE 주체, Pod UID는 감사용 |
| 1초 API 폴링 lease(Pumgye RBAC 원천, `SumunjangPolicy` 500ms GET) | informer + 서명 스냅샷 + 제한 staleness + 빠른 회수 |
| Hopae 요청당 TokenReview + Pod/SA GET | 오프라인 JWKS + tombstone, 캐시 있는 선택적 TokenReview |
| 게이트웨이에서의 NetworkPolicy 집행 목표 | CNI 정책 생성 + 진단 |
| 고정 이름·무스키마 `SumunjangPolicy` | 구조적 `NetworkZone`/`NetworkControl`(이행 도구) |
| Kubernetes RBAC → 애플리케이션 권한 매핑을 권한 원천으로 사용 | `AccessBinding`, RBAC 가져오기는 observe 전용 |
| 패키지 내 Pumgye SAR authorizer | **보류**, 코드는 유지하되 클러스터 외부/관리형 토폴로지 설계 전까지 차트 제외 |
| 테스트 생성기를 배포 경로로 사용 | Helm 차트, 생성기는 차트 위 검증 하네스 |

## 단계 계획

**P0 — 설치 가능·기능 완결·단일 클러스터:** v1alpha1 CRD(CEL/status), controller(informer, 서명 배포, 제한 staleness,
빠른 회수), Pumgye v2(ADR 0021 P0), Sumunjang zone/control, Hopae 오프라인 JWKS·tombstone, Hangang HTTPRoute +
`ProtectionPolicy` + IP 보존 모드, cert-manager mTLS hot reload, Helm 차트, digest 고정 서명 이미지, SQLite 단일·Hopae PostgreSQL 모드.

**P1 — 운영:** 전 구성요소 HA(PostgreSQL, N ≥ 2, PDB), 업그레이드/롤백 자동화, 변환 webhook·v1beta1,
NetworkPolicy/Cilium 생성, SPIFFE SVID, GRPCRoute, World 객체 콘솔(ADR 0020, GitOps 인지 읽기 전용), 판정 이벤트(ADR 0019),
백업/복구 runbook, Gateway API 적합성 보고.

**P2 — 확장:** 다중 클러스터, waypoint/ext_authz 동서 L7, JIT(ADR 0021), SAR authorizer 재설계, 10k/100k 부하 검증.

## 현재 검증 상태에서의 이행

1. `hangang-world export`로 현 네이티브 정책(Pumgye v1, Sumunjang, Hopae 프로필, Hangang 경로)을 World 객체로 내보내기,
   Pumgye v1은 ADR 0021 변환기 경유. 보고서 검토, 자동 적용 없음.
2. CRD와 controller를 `observe` 모드로 설치해 실행 중 소유자와 diff만. 게이트: 무설명 diff 0.
3. 도메인별로 writer marker를 전환해 `kubernetes` 모드로, 이전 DB 스냅샷은 롤백용 보관.
4. 확인 후 Pod 결속 부여를 SA 바인딩으로 교체, 동등성 확인 후 `SumunjangPolicy` 폐기.
5. 남북 진입을 클라이언트 IP 보존 Hangang Gateway로 이동, 외부 host network 게이트웨이는 기능 게이트 통과까지 유지 후
   폐기하거나 `hostNetwork` Gateway 인스턴스로 전환.

## 검증 게이트

순서: 사용자가 지정한 원격 k3s에서 **기능 우선**. **클러스터 변경 전 새 콜드 백업을 만들고 무결성 검증**(hash/tar,
오프호스트 사본, ADR 0015). 기존 워크로드·DNS·운영 게이트웨이 보존, 소유 namespace만 사용, 정리·롤백 문서화.
**기능 게이트 통과 전 부하 벤치마크 금지.**

P0 기능 인수(테스트 생성기가 아닌 차트로 설치한 서명 릴리즈 산출물 기준):

- OCI 차트 `helm install`로 Ready 도달, 잘못된 values는 객체 생성 전 실패, `helm uninstall`은 문서화된 대로 CRD·데이터 처리.
- 보호 HTTPRoute 요청이 실제 클라이언트 IP로 Hopae·Sumunjang·Pumgye를 통과. 익명, guest, 위조 헤더, 잘못된
  audience/issuer, 다른 SA, deny 바인딩, 차단 zone은 backend 미전달 거부. `requireProtection` Gateway 아래 무보호 경로는 미게시.
- 워크로드 Deployment 롤아웃 후에도 접근 유지, SA 삭제/재생성은 문서 규칙대로, Pod 삭제 시 토큰 회수 SLO 이내.
- 바인딩 삭제, 긴급 deny, zone 차단, 그룹 제거 회수 p99 ≤ 2초(기능 표본, 모든 Ready 복제본).
- API 서버 10분 중단(기본 5분 한도까지 제공 → 이후 fail closed → 복구), controller 종료(standby 인계, 데이터 평면 무영향),
  잘못된 객체 하나(status 거부, 나머지 무영향, 503 없음).
- 재시작·실패 요청 없는 인증서 회전, 서명 키 회전.
- 모든 World 객체의 `observedGeneration`·조건·적용 revision, 콘솔의 원천·신선도·ACK 표시.

P1 추가: 연속 기능 probe 아래 N-1 → N 업그레이드와 `helm rollback`, PostgreSQL failover, 새 namespace로의 백업/복구
훈련(revision 재현, 오래된 epoch 거부), 실제 CNI가 집행하는 생성 NetworkPolicy(게이트웨이 집행과 분리 보고),
Gateway API core 적합성. 그 다음 전체 경로 부하 검증(ADR 0013/0015 목표).

## 검토한 대안

- **컴포넌트별 API 그룹:** 버전·RBAC 집계·콘솔이 분산되어 거부, 소유는 kind 단위.
- **각 소유자가 API 서버를 직접 watch:** 모든 컴포넌트에 API 자격 증명, relist/fence 중복 구현, 교차 도메인 참조 일관 검증 불가. 거부.
- **Helm 대신 OLM operator:** controller가 이미 World operator이며 Helm OCI가 가장 일반적 배포 경로. OperatorHub 번들은 추후.
- **1초 lease 유지:** 가장 강한 staleness 보장이나 control plane 순간 장애가 전면 중단이 됨. xDS·OPA bundle처럼 제한된
  last-known-good가 상용 관례. Kubernetes 모드에선 거부.
- **Istio/Linkerd 집행:** mesh 의존 추가, 추후 ext_authz/waypoint로 지원.
- **지금 클러스터 내 SAR authorizer:** 순환 부트스트랩과 낮은 가치로 보류.

## 결과

명확한 원천과 통일된 신선도 의미를 가진 설치·업그레이드 가능한 서명 패키지, 실제 집행점과 일치하는 집행 주장,
롤아웃에도 유지되는 워크로드 부여. 비용: 새 controller와 CRD API 유지, Gateway API 적합성, PostgreSQL 어댑터(ADR 0013),
Hopae JWKS/tombstone 작업, control plane 분할 시 명시적으로 수용한 제한 staleness 구간.
