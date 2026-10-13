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
