# ADR 0015: Kubernetes와 IAM을 원천으로 연결

[English](../adr/0015-kubernetes-iam-authority.md)

상태: 채택한 방향. 네 모듈의 전체 배포와 정책 어댑터는 설계 단계입니다.
한강에는 이미 Kubernetes Ingress 컨트롤러, 오프라인 변환, 네임스페이스
배포/RBAC가 있습니다. 호패 워크로드 인증, 품계 RBAC 가져오기, 수문장
NetworkPolicy 집행까지 구현되어 있다는 뜻은 아닙니다. 내부 품계 집행은
명시적으로 연결한 검증용 라우트에 적용되며 전체 서비스 적용은 남았습니다.

## 책임과 원천

Kubernetes는 실행 환경을 넘어 정책·신원의 원천이 될 수 있어야 합니다.
한강은 Ingress/Service와 요청 집행, 호패는 ServiceAccount·프로젝션 토큰·
TokenReview와 외부 인증, 품계는 Role/ClusterRole과 Binding 및 명시적 앱
권한 매핑, 수문장은 NetworkPolicy·Pod/Namespace 선택자와 네트워크 근거를
담당합니다. EndpointSlice와 CNI 집행 연계는 별도 구현·검증 대상입니다.
품계 코어에는 Kubernetes 클라이언트를 넣지 않습니다. etcd 직접 접근이나
공유 업무 DB 다중 쓰기를 도입하지 않습니다.

영문 문서의 다이어그램과 책임 표가 공통 구조를 정의합니다. 도메인별 확장
CRD는 제안이며 실제 API 그룹/버전/스키마 정의 전에 구현된 API로 취급하지
않습니다. 비밀값은 Secret 참조로만 연결하고 상태·콘솔·로그에 넣지 않습니다.
Kubernetes에는 일반 사람 User 객체가 없으므로 Binding 생성이 인증이 되지
않습니다. Pod IP나 이름만으로 워크로드 신원을 인정하지 않습니다.

## 권위 모드와 스냅샷

클러스터·테넌트·도메인별로 DB 원천, Kubernetes 원천, 읽기 전용 관찰 모드를
선택합니다. DB와 Kubernetes를 마지막 쓰기 우선으로 병합하지 않습니다.
Kubernetes 원천 모드의 콘솔 변경은 resourceVersion 충돌 보호를 거쳐 실제
리소스로 쓰며 DB는 복구/구체화 저장소입니다. GitOps 소유 필드는 해당 변경
경로를 따르거나 읽기 전용으로 둡니다. UI에 원천·클러스터·namespace·UID·
resourceVersion·generation·digest·observedGeneration·적용 revision·신선도·
충돌·오류를 표시합니다. 컨트롤러 상태 필드는 권한을 부여하지 않습니다.

list/watch는 요청 경로 밖에서 제한된 후보를 컴파일합니다. resourceVersion은
불투명 값이며 숫자 비교나 클러스터 간 공통 revision으로 쓰지 않습니다.
watch 만료 시 완전한 재조회가 필요하고 일부 페이지를 권위로 게시하지 않습니다.
객체 간 watch는 전역 트랜잭션이 아니므로 의존성 변경 중에는 검증된 reconcile
장벽 또는 보수적 거절이 필요합니다. 클러스터 식별자와 객체 UID까지 묶어
삭제·동명 재생성·선택자·집계 역할 변경을 구분하고 적용 revision을 갱신합니다.

불변 메모리 인덱스를 원자적으로 게시하고 요청마다 Kubernetes/클라우드 정책을
조회하지 않습니다. 필요한 근거 캐시는 최대 1–5초, 인가 lease는 최대 1초와
모든 원천 만료에 제한합니다. TokenReview가 필요한 회수를 오프라인 서명 확인으로
대체하지 않습니다. 보안 원천 만료/불완전 시 해당 보호 트래픽은 stale 복제본에
직접 들어오는 경우도 거절합니다. readiness만으로 집행을 대신하지 않습니다.
한강의 기존 라우팅 신선도 동작은 이 보안 보장을 이미 구현했다는 뜻이 아닙니다.
장기 스트림도 원천 revision을 주기적으로 재검증해야 합니다.

## RBAC·IAM·네트워크 의미 보존

Kubernetes RBAC는 허용 규칙의 합이며 deny 규칙이 없습니다. apiGroup, resource,
subresource, verb, resourceNames, nonResourceURLs, namespace/cluster 범위, 집계,
wildcard, subject 종류를 보존합니다. `get pods`를 앱의 `read`로 자동 변환하지
않고 관리자 소유 매핑을 요구합니다. 지원하지 않는 규칙은 게시를 거절합니다.
`bind`, `escalate`, `impersonate`, 서비스 계정 토큰 발급은 별도 특권입니다.

품계의 추가 게이트웨이 제한을 Kubernetes 자체 deny라고 부르지 않습니다.
API 서버 직접 집행은 별도 authorizer/webhook 및 순서 검증이 필요하며 앞선
allow가 뒤 webhook을 우회할 수 있습니다. Admission webhook은 읽기 인가가
아닙니다. Ingress 앱 접근과 API 서버 접근 및 우회 경로를 별도로 검증합니다.
Binding은 신원이나 클라우드 권한을 생성하지 않습니다.

NetworkPolicy는 합산되는 L3/L4 격리이며 송신·수신 양쪽 선택 대상 정책을
고려합니다. namespace 선택자 범위와 policyTypes를 유지하고 위험 점수를
네이티브 deny 규칙으로 단순 변환하지 않습니다. 실제 집행은 지원하는 CNI가
필요합니다. DNS/NAT/hostNetwork/기존 연결은 플러그인별 검증 대상입니다.

클라우드 IAM은 공급자 의미와 원천을 보존합니다. AWS의 명시적 deny, 리소스
정책, boundary, 세션 정책, 조직 제어를 단일 역할 합이나 보편적 교집합으로
평탄화하지 않습니다. 호패는 범위·기간 제한 자격증명 중계, 품계는 게이트웨이
추가 제한을 맡지만 공급자가 거절하는 권한을 부여하지 않습니다. 자격증명은
네이티브에 두고 사용자 헤더로 흘리지 않습니다. 공급자 회수·만료·전파 지연을
문서화합니다.

## 구현과 검증 순서

1. 품계 메뉴를 통합 콘솔 ZERO TRUST 그룹에 배치하고 관리자 검사 유지.
2. 기존 한강 컨트롤러를 기준으로 네 모듈 독립 Deployment/Service, 최소
   ServiceAccount/RBAC, probe, 자원 제한, 인증서/Secret 회전, NetworkPolicy 구성.
   검증된 릴리즈 이미지만 사용. 도메인별 DB 소유와 검증된 복제/스냅샷 백본 필요;
   공유 SQLite 볼륨으로 스케일아웃하지 않음. CNI와 API 탐색 권한 명시.
3. 읽기 전용 연결기·원천 상태 UI부터 구현. CRD/명시적 앱 매핑 후 쓰기 지원.
4. 원천 모드·소유자 검사 게시·충돌·복제본 fence 및 회수 검증 후 보호 활성화.
5. 격리 클러스터에서 namespace/cluster 혼동, issuer/audience 오류, 바인딩 객체
   삭제, 동명 재생성, 집계 역할, impersonation/escalation, watch 만료, 부분 재조회,
   rollback, stale 복제본, 컨트롤러 장애, 우회, 비밀 회전, 드레인·증감 검증.
   전체 집행 경로에서 초당 1만/10만 쿼리 측정. 코어 단독 수치를 전체 성능으로
   주장하지 않음.

이 문서는 실제 클러스터나 클라우드 IAM을 변경하지 않습니다. 기존 풀스택
완성 goal은 계속 진행 중입니다. 공식 근거 링크는 대응 영문 문서에 있습니다.

구현 갱신: 품계 `55cea05`에 제한된 오프라인 읽기 전용 RBAC 검사 명령과 명시적 클러스터 식별자를 추가했습니다. 규칙·UID·불투명 resourceVersion을 보존하고 중복 객체·누락/다른 namespace 역할 참조·지원하지 않는 규칙을 거절합니다. workspace 테스트 11건, 엄격한 clippy, 실제 CLI의 DB 미생성 검사, 소유 mTLS HTTP/PPG1 게시·회수·재시작 smoke가 통과했습니다. 실시간 API watch·앱 권한 매핑·원천 게시 연계는 아직 남아 있으며 운영 권한은 바꾸지 않았습니다.

품계 `1972ace`에 별도 HTTPS 읽기 전용 실시간 수집 명령을 추가했습니다. 지정 CA 검증·리다이렉트/프록시 거절·제한된 토큰/CA 재읽기·완전한 페이지 조회·종류별 불투명 버전 보존·불변 메모리 관찰 상태와 최대 1초 신선도를 구현했습니다. 실패 시 이전 상태를 비우고 다음 주기 처음부터 재조회합니다. 격리 HTTPS 검증은 변경/삭제·페이지/범위/버전 오류·HTTP 410 복구·인증 파일 교체·비밀 미출력·DB 미생성을 확인합니다. workspace 14건과 엄격한 clippy·기존 mTLS 권한 smoke가 통과했고 의존성 감사에는 기존 허용 rustls-pemfile 유지보수 경고만 있습니다. 폴링 단계이며 확장형 watch나 앱 권한 원천 게시 구현은 아직 아닙니다. 운영 클러스터 설정은 바꾸지 않았습니다.

품계 `c4168da`에 명시적 RBAC→앱 권한 후보 매핑을 추가했습니다. 클러스터·Role/Binding UID/범위·source subject·리소스/verb/이름의 모든 정확한 조건을 요구합니다. 빈 사용자 템플릿부터 재계산해 원천 삭제/재생성 시 후보 배정을 없애고 코어 컴파일로 IP·수문장 조건을 유지합니다. 설정 digest와 실시간 최종 신선도 검사를 포함합니다. workspace 17건·엄격한 clippy·격리 HTTPS 매핑/삭제/복구 fixture·실제 CLI 예제·기존 mTLS 권한 smoke가 통과했습니다. Group/집계/특권 변환·API resource discovery·호패 워크로드 연관 검증·영속 원천 게시 연계는 남았습니다. 후보는 진단용이며 운영 정책을 바꾸지 않았습니다.

호패 `8aecbd5`에 네이티브 Pod-bound TokenReview 연결기를 구현했습니다. 고정 CA 검증 HTTPS·분리 reviewer·issuer/audience 사전 거절 검사 후 신뢰 API의 ServiceAccount UID·Pod UID/name 증명, issuer/cluster/바인딩 ID로 구분된 Workload 신원, 서비스 범위·최대 1초 근거, 제한된 풀 요청과 원천 회로를 제공합니다. 인증 거절 error는 회로를 열지 않고 모순된 양성 증명은 원천 오류로 처리합니다. 소유 TLS mock·최종 대상 테스트/엄격한 검사·문서/시나리오 검사·전체 회귀(907 통과·42 제외)가 통과했습니다. 감사에는 기존 검증 전용 RSA 범위 예외와 rustls-pemfile 허용 경고가 있습니다. mock은 실제 클러스터 서명/삭제 검증이 아닙니다. 루트 프로필·HTTP/HOP1·인증 파일 자동 회전·삭제 fence·품계 연관·receipt 발급 연계가 남았습니다. 1초 근거가 Kubernetes 삭제 유예를 없애지 않습니다. 운영 연결기는 활성화하지 않았고 릴리즈 자산도 그대로입니다.

네이티브 통합 갱신: 호패 `0a94fb0`·시작 키 검사 보완 `c759137`은 참조형 TokenReview 프로필을 명시적 접두사의 혼합 라우팅·owner 게시·HTTP/HOP1·workload/AAL 0 응답·현재 사람 step-up 거절에 연결했습니다. 한강 `0b8e343`·문서 `9291947`은 정규 workload AAL 0만 허용하고 매트릭스/서비스/네트워크/등급 검사와 자격 제거를 유지합니다. 소유 TLS HTTP/HOP1에서 라우팅 격리·진행 중 프로필 회수를 검증했고, 최적화된 사설 owner 복사본에서 workload HTTP/풀링 mTLS·기존 relay/Lua/MFA/TOTP Chromium 검증이 통과했습니다. 호패 전체 회귀 909 통과·42 제외, 시작 설정 키 등록 보완 후 config unit/preflight 24+18건·엄격한 검사·최적화 후보가 통과했습니다. 한강 신원 4건·전체 resource-policy 14건·엄격한 clippy·문서 링크 892개가 통과했습니다. 기존 RSA 범위 예외·rustls-pemfile 허용 경고는 유지합니다.

내부 반영: 한강 `0.3.2-workload-9291947`, 호패 `0.0.3-kubernetes-c759137`·스키마 v6, 콘솔 0.1.6(manifest SHA-256 `934fb613300b127df99f5b3ea7817d007877b5ff8c77bf710ae8a00ed855d4b4`). 설정·키·품계 정책을 보존했고 중지 상태 owner/delegation 백업·이전 이미지·콘솔 registry가 남았습니다. 실제 API/매트릭스/native/SSO·프로필/비활성 projection 화면 검사가 통과했습니다. 운영 프로필은 native-only로 실제 Kubernetes/reviewer를 구성하지 않았고 projection/receipt RPC는 비활성입니다. 기존 릴리즈 자산은 그대로입니다. 실제 클러스터 서명/삭제·매핑 권한 게시·확장 watch·스트림/복제본 fence·전체 성능은 남았습니다.

실제 Kubernetes 검증·현재 객체 fence: 호패 `207396d`을 별도 loopback kind v1.37.0 API와 실제 TokenRequest 서명으로 검증했습니다. authenticated/audiences 생략·user:{}인 실제 거절 응답도 원천 회로를 열지 않습니다. TokenReview만 쓰면 강제 Pod 삭제 전파가 약 9.8초였고, 현재 Pod/ServiceAccount partial-metadata GET·UID/삭제 상태·명시적 namespace를 확인한 뒤 소유 fixture 관찰은 106–122ms였습니다. fleet 보장은 아닙니다. reviewer는 TokenReview create와 해당 namespace의 지정 객체 GET이며 metadata 전용 RBAC 권한은 아닙니다. namespace 누락은 시작을 거절합니다. 실제 서명 변조·issuer/audience/unbound/reviewer 거절·객체 삭제·동명 Pod 재생성 검증이 통과했습니다.

전체 네이티브 회귀 911 통과·42 제외, TLS metadata/회로·HTTP/HOP1 회수·엄격한 검사·최적화 사설 owner workload/mTLS/relay/Lua/MFA/TOTP Chromium 검증이 통과했습니다. 기존 RSA 범위 예외·rustls-pemfile 경고는 유지합니다. 내부 호패 `0.0.3-kubernetes-207396d`·콘솔 0.1.7(manifest `d620fb19edc574e08341a32a01e1c36c3dfedb709573c4dd32889ad02f5eb578`)이 운영 중이며 설정/키/native-only 프로필·품계 정책을 보존하고 중지 v6 백업·이전 이미지/registry를 남겼습니다. 실제 API/매트릭스/native/SSO/프로필 화면이 통과했습니다. 테스트 클러스터는 운영과 분리했고 fixture namespace/RBAC는 제거했습니다. 운영 Kubernetes는 미구성입니다. watch 객체 인덱스·다른 버전/토폴로지·복제본/스트림 회수·자동 매핑 게시·전체 성능은 남았고 태그 릴리즈 자산은 그대로입니다.

품계 `ec2fe0f`을 소유 v1.37.0 API의 읽기 전용 RBAC 수집·명시적 후보 매핑으로 검증했습니다. 실제 typed list는 kubectl 합친 출력과 달리 항목 kind/apiVersion을 생략하므로 검증된 collection에서 누락값만 보완하고 모순된 타입은 거절합니다. Binding 삭제 후 후보 배정 제거·동명 재생성 UID 거절·자격 실패 시 관찰 fence와 복구가 통과했습니다. workspace 18건·엄격한 clippy·소유 HTTPS/매핑·기존 mTLS 권한 회귀가 통과했습니다. native subject는 가상 참조이며 권위 DB 생성·운영 정책 변경이 없습니다. 호패 연관·자동 게시를 완료한 것은 아닙니다.


품계 `f78dda7`은 명시적 관리자 신원 연관을 사용하는 선택형 Kubernetes 단일 작성자 정책 재조정을 구현합니다. 정책·revision·감사를 커밋한 뒤 불변 스냅샷을 게시하고, 수집 전에 판단을 철회하며 원래 관찰의 1초 기한을 따릅니다. 영속 소유 표시는 네이티브 작성자 전환을 거절하고 시작 시 저장된 권한으로 허용하지 않으며 관리 정책 PUT은 409입니다. 실제 소유 v1.37.0 API에서 mTLS HTTP/지속 PPG1 허용·거절 일치, Binding 삭제 영속 revision, 재생성 UID 거절, 인증 복구, 작성자 배제·재시작 fence를 검증했습니다. workspace 19건·엄격 clippy·관찰/native 전송 회귀가 통과했습니다. 한강 `80bdfb4`은 원천 정책을 조회 가능하되 읽기 전용으로 표시하고 브라우저 4건이 통과했습니다. 수집 중 사용 불가 구간이 있는 polling이며 분산 watch·호패 신원 자동 연관은 아니고 운영 원천 모드는 비활성입니다.


## UID 고정 호패 / 품계 워크로드 연관 — 2026-10-14

품계 `9f203e5`은 불투명 native 참조 대신 issuer·매핑 cluster·namespace·
ServiceAccount 이름/UID·Pod 이름/UID를 지정하는 workload를 받습니다. RBAC
ServiceAccount 이름/namespace 일치와 중복 형식 거절을 적용하고 호패와 같은
신원을 컴파일 시 계산합니다. 기존 네트워크·수문장·앱 권한 제약을 유지합니다.
주소 계산이며 인증은 아닙니다. TokenReview·issuer/audience·현재 UID/삭제 검증은
호패가 담당합니다.

소유 실제 v1.37.0 API의 서명된 Pod-bound 토큰을 네이티브 호패가 검증한 신원과
품계 매핑이 일치하여 mTLS HTTP/지속 PPG1 권한을 허용합니다. 같은 계정의 다른
실제 검증된 Pod는 guest이고 원래 Pod 삭제는 토큰을 거절합니다. Binding 삭제/
재생성·원천 인증 복구·작성자 배제·재시작 fence도 통과했습니다. 품계 workspace
20건·엄격 clippy·가상 오프라인 예제·관찰 매핑 회귀와 호패 `b20ffee`의 같은 가상
신원 벡터 native 검증이 통과했습니다.

관리자가 UID를 고정하는 연관이며 Pod 자동 발견·UID 재고정은 아닙니다. 한강은
신뢰 native 경로로 인증 신원을 받아야 하고 이 fixture는 전체 요청/스트림 경로
검증을 완료하지 않습니다. 운영 설정·이미지·릴리즈 태그는 그대로입니다. watch·
전체 연결·복제본·나머지 인증 프로바이더·Kubernetes 배포·공개 릴리즈는 원래
활성 목표에 남아 있습니다.


## 네 네이티브 런타임 Kubernetes 요청 경로 — 2026-10-14

품계 `c52e9e1`은 소유 실제 Kubernetes 워크로드/RBAC fixture에 실제 네 프로세스
검증을 추가합니다. 한강·호패·품계·수문장은 새 격리 DB/키, 공개 HTTPS와 네이티브
mTLS HOP1·PPG1·HGD1을 사용합니다. 실제 TLS 포트와 앱 포트를 일치시키며
TLS 기능이 없는 오래된 한강 바이너리는 거절하고 프로토콜 대역으로 바꾸지 않습니다.

실제 서명된 Pod 토큰은 호패 검증·수문장 enforce·UID 매핑 품계 권한을 통과해야
백엔드에 도달합니다. 백엔드는 canonical 신원·Workload·일치 service·AAL 0을
받고 클라이언트 위조 신원/AAL 헤더는 살아남지 않으며 원래 Authorization은
소비됩니다. 다른 실제 인증된 Pod·미인증·observe·IP 차단·Binding 삭제는 백엔드
전달을 막고 차단 제거는 회복합니다. 원천 인증 실패는 503, Pod 삭제는 401입니다.
실제 위임 관리 API는 Kubernetes 소유 표시를 전달하고 올바른 두 revision으로도
원천 정책 덮어쓰기를 거절합니다.

소유 v1.37.0 API에서 기존 신원 연관·원천 복구/재생성·재시작 검사까지 통과하고
고유 RBAC/namespace·프로세스를 정리했습니다. 운영 설정/이미지는 그대로입니다.
실제 요청 경로 검증이며 Kubernetes Pod 패키징·Ingress 소유·스트림 인증 회수·
CNI 전체 집행·분산 watch/follower·전체 처리량 검증 완료는 아닙니다. 보수적 polling
가용성 구간과 원래 목표의 나머지 완료 조건은 남아 있습니다.


## 제한된 네이티브 기계 인증 lease — 2026-10-14

호패 `0cd46ba`은 HTTP/HOP1에 남은 검증 근거 수명을 최대 1000ms의
x-hopae-evidence-ttl-ms로 전달하고 만료 시 신원 없는 503입니다. 한강 `ce08314`은
교환 시작 시각에 묶고 잘못된 값·중복·소진된 기한을 거절하며 공통 라우트 회수·
응답/업로드 본문·upgrade에 적용합니다. 헤더 없는 기존 신뢰 peer는 로컬 1초
한도입니다. 250ms 회수 poll 간격을 명시하며 정확한 1초 전송 보장이나 허용 캐시는
아닙니다.

정책/원천 변경 없는 격리 idle 스트림이 1.5초 안에 종료됩니다. 권한 테스트 15건·
TTL 공격 unit·엄격 clippy·문서 링크 892개가 통과했습니다. 원격에 추가된 Ingress
Host 보존 변경을 검토·통합했고 Actions 활성화는 바꾸지 않았으며 해당 테스트와
권한 테스트가 rebase 후 통과했습니다. 호패 수명 assertion·실제 HTTP/HOP1 회수
시나리오·엄격 clippy·영한 문서 검사도 통과했습니다. 최적화 바이너리·소유 실제
v1.37.0 API·네 native 프로세스에서 HTTP/mTLS HOP1 TTL·제한된 스트림 종료와
기존 요청/자격/회수 검사가 통과했습니다. 품계 `f45f38b`은 이 재현 도구를 유지합니다.
실제 fixture는 원천 freshness도 스트림을 닫을 수 있으므로 native 만료의 직접
근거는 변경 없는 격리 테스트입니다.

초기 보수적 구현은 짧은 인증 수명보다 긴 기계 연산/스트림을 종료합니다. 유효한
장기 연결을 유지하려면 인증된 갱신·호패 개별 자격 회수 구독이 더 필요합니다.
이번 단계는 운영 이미지를 바꾸지 않았고 정책·키·릴리즈 태그는 그대로입니다.
분산 watch/follower·Kubernetes 패키징·나머지 프로바이더/수명주기·전체 성능·공개
릴리즈/운영 완료 조건은 활성 목표에 남아 있습니다.


## 선택형 네이티브 기계 근거 갱신 — 2026-10-14

한강 `058fe3f`은 native 서비스/워크로드 요청의 auth.renew_native_evidence를
추가합니다. 같은 제한된 인증 풀로 원래 문맥을 수명 중간에 재검증하고 명시적 유효
TTL·같은 신원/종류/AAL/service를 요구합니다. 거절·장애·용량 소진·잘못되거나 짧은
근거·신원 변경·이전 만료는 영구 회수하며 늦은 근거는 복구하지 못합니다. 선택 인증
헤더는 메모리에만 사설로 유지하고 마지막 참조를 닫으면 태스크·문맥을 제거합니다.
프로세스당 최대 4096개와 native 풀 한도가 적용합니다. 기본은 갱신 없는 만료이고
갱신에는 native 전송이 필수입니다.

권한 테스트 17건·OpenAPI 참조 검사가 통과했습니다. 소유 native peer에서 정책/
원천 변경 없이 2초 넘게 유지한 뒤 거절·장애·신원 변경·짧은 만료로 닫히는 것을
검증했습니다. 전체 target 엄격 clippy·최적화 바이너리 실제 네 모듈/Kubernetes
기본 모드 회귀도 통과했습니다. 그동안 추가된 원격 변경은 Ingress 문서/예제/
changelog이며 검토·rebase했습니다. 이후 문서 링크 916개가 통과했습니다.

게이트웨이 갱신 메커니즘의 소유 native peer 검증이며 실제 호패/Kubernetes 지속
갱신·취소/한도 포화 측정·개별 회수 구독·대규모 처리량은 더 필요합니다. Kubernetes
RBAC polling은 원천 health를 독립적으로 철회하여 유효 스트림도 닫을 수 있으므로
watch/follower 연속성이 필요합니다. 이번 단계는 운영 이미지/설정·릴리즈 태그를
바꾸지 않았고 원래 전체 완료 목표는 활성입니다.


## 갱신 취소·한도·비가역 만료 — 2026-10-14

한강 `d963b8d`은 갱신 응답에도 남은 수명 최소값을 검사하고 보관 인증 문맥을
민감 값 표시로 보호합니다. 소유 전송 테스트에서 갱신 슬롯 4096개 소진 후 신규
거절, 마지막 참조 종료에 따른 실제 진행 중 native 소켓 취소·전체 슬롯 반환을
확인합니다. 응답 부재는 수명을 늘리지 않고 timeout하며 만료를 관찰한 뒤에는
기한을 늘려도 복구하지 않습니다. 짧은/만료 TTL 권한 테스트는 신원을 그대로 두어
신원 불일치가 수명 거절을 가리지 않도록 보완했습니다.

수명주기 전송 unit·권한 17건·전체 target 엄격 clippy·문서 링크 916개가 통과했습니다.
제한된 수명주기/전송 검증이며 대규모 처리량·실제 클러스터 지속 갱신 완료 주장은
아닙니다. 운영 이미지/설정·릴리즈 태그는 그대로입니다. 실제 원천 watch 연속성·
장기 프로바이더 검증·배포·나머지 인증 수명주기/프로바이더·분산 follower·전체
성능/릴리즈 완료 조건은 활성 목표에 남아 있습니다.


## 실제 네이티브 워크로드 스트림 갱신 — 2026-10-14

품계 `fb53091`은 실제 네 모듈·소유 Kubernetes fixture에 --qualify-renewal을
추가합니다. 일반 원천 권위 RBAC 삭제/재생성·장애·재시작 검사도 유지합니다.
별도 native 품계 DB는 이전 검증 후보를 고정하여 인증 갱신과 polling health 철회를
분리합니다. 명시적 테스트 분리이며 운영 fallback·RBAC watch 연속성 검증은 아닙니다.

실제 한강/호패/수문장/품계·서명 Pod-bound 토큰으로 native 갱신을 켠 heartbeat
스트림을 2.2초 넘게 유지합니다. 실제 Pod 삭제 완료 기준 fixture의 1.5초 안에
닫히고 후속 인증은 401입니다. canonical 신원/종류/service/AAL·백엔드 인증 토큰
미전달도 유지합니다. 최신 최적화 게이트웨이·소유 v1.37.0 API에서 전체 fixture가
통과했고 프로세스/자원을 정리했으며 운영은 그대로입니다. 고정 권한에서 실제
프로바이더 인증 갱신/회수 검증이며 동적 RBAC 연속성·대규모 성능 완료는 아닙니다.

원천 watch/follower·장애 토폴로지·Kubernetes 패키징·나머지 혼합 프로바이더/
수명주기·전체 성능·릴리즈/배포 조건은 원래 활성 목표에 남아 있습니다.


## 원천 수집 시간이 freshness를 소비 — 2026-10-14

품계 `ecf4544`은 관찰 수명을 수집 시작 1초로 변경합니다. 이전에는 느린 여러 목록
수집 뒤 완료 시 다시 1초를 부여할 수 있었습니다. 전체 수집 timeout도 1초이며
정규화/해시 뒤 나이·시계 overflow를 게시 전에 검사합니다. 매핑·컴파일·저장도
같은 예산을 소비하고 오래된/부분 관찰은 유효 권한이 되지 않습니다.

workspace 21건·엄격 clippy가 통과했습니다. 소유 HTTPS의 1.2초 응답 지연이
사용 불가·다음 정상 수집 복구로 이어지며 기한 unit은 경과 시간이 수명을 재시작하지
않음을 검증합니다. 실제 v1.37.0·네 native 모듈·격리 실제 워크로드 갱신/Pod 삭제
회수도 새 예산으로 통과했습니다. 운영 설정/이미지·릴리즈 태그는 그대로입니다.

원천 나이 확대를 수정하며 종류 간 원자성·watch 연속성 완료는 아닙니다. 큰/느린
원천은 예산 초과 시 권위를 조용히 늘리지 않고 사용 불가입니다. 확장 watch/follower·
배포·나머지 프로바이더/수명주기·전체 성능/릴리즈 조건은 원래 활성 목표에 남습니다.


## 고정 원천 연결 재사용 — 2026-10-14

품계 `508bb73`은 실제 CA/토큰 자료가 같으면 Kubernetes HTTPS 클라이언트를 재사용합니다.
제한된 파일은 매 주기 다시 읽어 검증하고 인증 헤더를 새로 만들며 자료 변경 시
이전 풀을 폐기합니다. 설정 CA·proxy/redirect 금지·수집 시작 1초 freshness·장애
차단은 유지합니다. 원천당 idle 최대 2개·10초 만료는 전송 설정이며 권한 캐시는 아닙니다.

소유 HTTP/1.1 TLS fixture에서 동일 완전 pagination 수집 두 번이 한 연결을 사용하고
자격 변경/복구가 새 연결을 사용하는 것을 셉니다. CA 오류/복구·원천 변경/삭제·
redirect/410·느린 수집·proxy 격리·비밀 미출력도 통과합니다. workspace 21건·엄격
clippy·실제 v1.37.0 네 native 프로세스·격리 갱신도 통과했습니다. 연결 재사용/회전
검증이며 전체 QPS 결과는 아닙니다. 운영 이미지/설정·릴리즈 태그는 그대로이고
확장 watch/follower·배포·나머지 혼합 인증 수명주기·전체 성능/릴리즈는 활성 목표에
남아 있습니다.


## 내부 품계 런타임 배포 — 2026-10-14

`508bb73`의 최적화 품계 서버를 내부에 배포했습니다. 이전 실행 파일·중지 상태
SQLite 백업을 rollback용으로 보관하고 native 정책 모드·정책 문서/revision·한강
설정·mTLS 리스너를 유지했습니다. 원천 소유 메타데이터 스키마 초기화는 기존
업무 정책을 바꾸지 않으며 인증 상태 API는 native 소유를 표시합니다.

릴리즈 실행 파일의 독립 mTLS HTTP/PPG1 신뢰/토큰 격리·제한된 pipeline·revision
하한·CAS 경합·즉시 권한 회수·DB 단일 소유·감사·재시작 복구가 통과했습니다.
배포 뒤 실제 HTTPS 서비스 인증/권한·메서드/guest/위조 거절·백엔드 토큰 미전달,
실제 통합 메뉴/매트릭스/로그아웃·native 수문장 연결도 통과했습니다. 서비스는
active이며 검증 뒤 정책·한강 설정이 원래 baseline과 일치합니다.

Kubernetes 원천 권위를 활성화하거나 호패/한강/수문장 운영 이미지를 변경한 것은
아닙니다. 공개 릴리즈 태그도 유지합니다. watch/follower 연속성·혼합 인증 수명주기·
대규모 처리량·Kubernetes 패키징·전체 릴리즈/배포는 활성 목표에 남아 있습니다.


## 내부 호패 인증 수명 배포 — 2026-10-14

호패 `48c8015`은 수명 wire assertion을 게이트웨이 영역으로 옮겨 전체 경계 검사를
통과시킵니다. 기존 포화 timing 실패(예상 최소 136 대신 133 overload)는 단독으로
통과했고 거절 기준을 낮추지 않은 채 지연 창을 늘려 전체 재실행도 통과했습니다.
native 전체 912 통과·42 제외, 엄격 검사/경계·문서·시나리오 커버리지가 통과합니다.
기존 RSA 검증 범위 예외·rustls-pemfile 유지보수 경고를 유지하며 예외 없는 감사
통과라고 하지 않습니다.

최적화 사본 상태 후보의 Kubernetes HTTP/지속 mTLS·prefix 격리·외부 relay/Lua·
브라우저 외부 MFA/TOTP·이전 handle 거절이 통과했습니다. 내부 이미지
hopae:0.0.3-evidence-48c8015를 배포하고 중지 v6 owner/위임 DB 백업·이전 이미지를
보관했습니다. 설정/인증 프로필/키를 유지했고 실제 API/매트릭스/모듈/SSO/native가
통과했습니다. 배포된 직접 검증 응답에서도 service 신원·AAL 0과 제한된 남은 TTL을
확인했습니다.

운영은 native 프로필이며 Kubernetes/외부 검증기/projection을 활성화하지 않았습니다.
한강 갱신 운영 반영은 별도 단계입니다. 공개 릴리즈 태그·나머지 프로바이더/
수명주기·watch/follower·Kubernetes 패키징·전체 성능/완료 조건은 원래 활성 목표에
남아 있습니다.


## 내부 한강 인증 수명/갱신 배포 — 2026-10-14

검증된 최적화 바이너리의 hangang/gateway:0.3.2-renewal-d963b8d 이미지를 내부에
배포했습니다. 이전 이미지/compose/설정/정책 백업을 유지하고 콘솔 바이너리는
보존했습니다. 교체 시 전체 설정·품계 정책을 먼저 유지했고 실제 API 권한·인증
토큰 제거·매트릭스/모듈/native 수문장·SSO/로그아웃이 통과했습니다. 배포 전 권한
17건·native TTL unit·Ingress Host 회귀도 통과했습니다.

별도 revision 조건 게시로 기존 protected native service-probe 두 라우트에만
갱신을 켰습니다. 게시 뒤 나머지 모든 설정 필드·품계 정책이 같음을 비교했고
실제 API·guest/위조/메서드 거절·모듈·SSO도 다시 통과했습니다. 제한된 내부 canary이며
전체 서비스 활성화·운영 장기 스트림 부하 검증 완료는 아닙니다. 현재 업데이트된
호패는 갱신에 필요한 제한된 TTL을 전달합니다.

Kubernetes 원천/watch 연속성·분산 배포/멤버십·나머지 인증 수명주기·전체 처리량·
최종 공개 릴리즈/완료 조건은 활성입니다. 이번 단계는 새 태그를 만들거나 GitHub
Actions를 활성화하지 않습니다.


## 실제 내부 갱신 스트림 검증 — 2026-10-14

제어된 임시 origin/라우트로 현재 내부 한강/호패/품계 canary를 확인했습니다.
갱신을 켠 heartbeat가 3.2초 넘게 이어지고 클라이언트 종료 시 origin도 정리되며
신원/AAL·원래 토큰 미전달이 맞습니다. 품계 정책은 그대로입니다. revision 조건
게시로 임시 라우트를 제거하고 기존 보호 설정을 복구했으며 정리 뒤 실제 API도
다시 통과했습니다. 단조 설정 revision만 증가합니다.

첫 실패는 갱신 장애의 증거가 아닌 fixture 구성 문제였습니다. 좁은 경로를 기존
prefix 뒤에 붙여 기존 origin에 도달했고 enforce scope 제거는 올바르게 거절됐습니다.
기존 namespace 안의 별도 resource_id도 올바르게 거절됐습니다. 정책/인증기가
같으면 resource_id 공유는 의도된 설계이며 공유 scope의 집행 해제·복구도 일관돼야
합니다. 경로 순서·공유 정책 전환을 수정한 실제 검증이 통과했습니다. 검증 규칙을
약화하거나 잘못된 중복 ID 거절을 추가하지 않았습니다.

짧은 실제 기능/취소 canary 검증이며 지속 부하·대규모 자격 회수·전체 QPS 측정은
아닙니다. watch/follower·프로바이더 수명주기·Kubernetes 패키징·전체 성능·최종
릴리즈/완료 조건은 원래 활성 목표에 남습니다.
