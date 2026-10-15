# Workload 게이트웨이 반영 계약

상태: 구현 계약이며 Workload 최종 전달 검증 완료가 아니다. 운영 한강 0.3.8의 observed
경로는 Service 전용이다. 호패 원천과 공개 SDK의 로컬 결합 근거가 있어도 인증 서명은
권한이나 자격 출력 허가가 아니다. [영문 계약](../../design/WORKLOAD_GATEWAY_ADOPTION.md)을
기준으로 한다.

라우트가 인증 class를 명시적으로 소유하며 기본값은 기존 Service다. Workload는 observed
인증·서명된 권한 permit·observed 출력 전체를 구성해야 한다. legacy UTC/strict 조합은
설정 단계에서 거부한다. 요청 헤더나 응답으로 class를 선택하거나 거부 후 다른 class로
재시도하지 않는다.

게이트웨이 내부에서 공개 SDK의 타입별 opaque 요청·관측을 유지한다. 공통 요청 수집·해시·
최종 raw 전송 검사는 재사용하되 Workload를 Service로 변환하지 않는다. Workload는 kind3,
AAL0이며 품계의 전용 RPC와 동일 compiled policy의 workload_users만 사용한다. 출력은
전용 RPC·contract3을 선택하고 모든 class/endpoint에서 동일 atomic paired replay ledger를
사용한다. 기존 owner·revision·최종 비밀 공개 검사를 유지한다.

인증·권한·출력의 외부 절대 시각을 비교하지 않는다. 각 receiver-local 보수적 deadline을
사용하고 refresh로 최초 원천 예산을 늘리지 않는다. 짧은 전달 허용과 긴 replay 보존을
구분하며 라우트 교체는 이전 SDK owner를 회수한다.

기존 Service 회귀, 잘못된 Workload 설정, class/권한/해시 불일치의 백엔드 미도달,
최초 지연·만료·레코드 누락·정책/라우트/plan/secret 회수·동시 refresh·교차 endpoint replay를
검증한다. 이후 실제 K3s audience-bound ServiceAccount JWT·TokenReview부터 품계·출력·
카운터 백엔드까지 동결 정적 파일로 검증한다. 동일 OS 프로세스의 새 서버 instance는
OS 재시작 검증이 아니다. Pod/토큰 회수의 Kubernetes API 전파와 이미 성공한 Hopae 관측의 최초 최대 1초
재사용 한계는 별도로 측정·설명한다. 삭제 후 1초 안에 새 인증도 거부된다는 보장은 아니다.
공개 파일 검증·백업·rollback 후 내부 반영하며 처리량·pooling·HA·복원 fence는 별도다.


[Kubernetes 공식 문서](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/#bound-service-account-tokens)는
삭제 대기 중인 객체의 deletionTimestamp로부터 60초 이상 뒤에는 인증을 거부하며,
참조 객체 부재나 UID 불일치도 거부한다고 설명한다. 실제 클러스터의 거부 전파 시간을
별도로 측정해야 한다. 새 TokenReview가 계속 성공하면 새 관측이 생기므로 각 관측의
1초 수명만으로 상위 API의 회수 전파 시간을 제한할 수 없다.
