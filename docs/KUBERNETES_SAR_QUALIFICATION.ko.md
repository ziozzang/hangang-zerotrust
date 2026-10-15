# 별도 API-server native SAR qualification

상태: 로컬 실행 가능한 fixture 및 단위검사만 구현했으며 클러스터에서는 실행하지 않았다.
영문 `KUBERNETES_SAR_QUALIFICATION.md`가 정확한 옵션·전제·제한의 기준이다.

helper는 기본적으로 비공개 파일만 렌더한다. 명시적 execute/부모 승인/최신 콜드 백업과
오프호스트 전체 해시·tar 검증/Pum0.1.9 정확한 이미지·소스·binary SHA 증거가 있어야
kubectl을 실행한다. 기존 master authorizer/RBAC/CRD/PV/서비스는 수정하지 않는다.
새 namespace를 create로 원자적으로 만들고 비특권·비호스트네트워크 API-server+etcd,
Pum DB-native source를 사용한다. cleanup은 생성한 namespace UID/resourceVersion
precondition으로만 삭제하며 기존 PodUID 및 두 노드 Ready를 확인한다.

Kubernetes98e9 원천과 공식 문서를 확인했다. 양쪽 authorization cache는 false이며
유효한 필수 TTL은1s다(0s는 원천 validation에서 거부). Webhook failurePolicy는 Deny,
정확한 Service authority/CA/leaf/Bearer를 쓴다. 공식 registry index와 amd64 child
manifest digest를 별도 기록했으며 실제 runtime imageID와 혼동하지 않는다.

ordinary client는 system:masters가 아니다. bootstrap은 fixture Namespace/ConfigMap
생성과 독립 backend readback만 수행한다. 실제 named GET/PATCH 허용, grant 회수 후
PATCH403·backend 불변, 복구 후 변경, 미매핑 신원·리소스·AAL·정보등급 거부,
Pum 장애/새 Pod 복구를 검사한다. 개인 client key/CA signing key는 업로드하지 않는다.

아직 실제 API-server 실행, 실제 SAR envelope 캡처 및 webhook H1 연결 재사용 관측은
없다. source lease 만료/TokenReview/전체 네 코어/성능/서명 릴리스/운영 완료를
주장하지 않는다. 기존 Service/Workload/default runner는 변경하지 않았다.

추가 안전 경계: 관리 endpoint는127.0.0.1:8080만 사용한다. 백업은 원격 cold/hash/size/tar
확인의 신뢰된 부모 receipt와 단일 로컬 offhost 사본의 실제 전체 hash/size/tar를
대조한다(부모 receipt 자체가 암호학적 권위는 아니다). 중복 사본을 요구하지 않는다.
부모의 image별 정확한 runtime imageID attestation이 없으면 kubectl 전에 거부하며
실제 spec/status를 테스트 전과 복구 후 확인한다. 원래 실패와 cleanup/baseline 실패를
별도로 보존하고 후속 정리 검사를 계속 수행하여 실패를 성공으로 기록하지 않는다.

정리 전에 이 실행이 create한 정확한 PodUID의 상태와 container별 마지막200줄/최대64KiB
로그만 비공개로 보존한다. 원래 namespace UID와 로그 수집 전후 PodUID를 확인하고
교체되면 로그를 버린다(로그 API에 원자적 UID precondition은 없다). Secret API는
읽지 않는다. 진단 실패도 원래 실패와 별도로 기록하며 cleanup/baseline 검사를
막지 않는다. 기존 시작/port-forward deadline은 확대하지 않았다.
