# Workload 실제 K3s 검증 준비 계약

현재 상태는 **선택적 실제 실행 orchestration 소스 구현, 실제 K3s 실행 미검증**이다. `--workload`는 composition(All/Any) 혼용과 미지원 browser/direct-client/통합 Sum source를 거부한다. 정확한 이미지 digest/소스/바이너리 SHA/capability 승인 파일과 고정 공개 Workload SDK probe SHA 검사를 변경 전에 통과해야 실행한다. 영구 preparation-only 차단은 제거했지만 parent의 최종 artifact 승인과 클러스터 lease 없이는 실행하면 안 된다. 기존 Service/default/All/Any 모드는 유지한다. helper로 실행 권한이나 인증 증명을 만들지 않는다.

실행 전 parent의 독점 클러스터 lease, 백업 전체 SHA/tar 확인, 최종 immutable 소스/바이너리 SHA/image 및 독립 Workload SDK probe가 필요하다. 새 owned-world namespace와 두 SA(리뷰어/클라이언트), 실제 bound Pod를 원자적으로 create한다. 리뷰어는 tokenreviews create만 허용하는 고유 ClusterRole/Binding을 사용하며 cluster-admin이나 wildcard를 금지한다. 클라이언트에는 API 권한/자동 token mount를 주지 않는다. Node utility 이미지가 필요한 bound Pod이며 scratch 호환을 주장하지 않는다.

실제 SA/Pod UID와 고정 API/CA/issuer/cluster/audience에서 Pod-bound TokenRequest를 만든다. JWT payload가 API/CA/원천을 선택하면 안 된다. 공개 Workload SDK Issue/Observe가 검증한 kind3/AAL0 subject와 helper의 documented hash 예상값을 교차검사한 뒤에만 Pum workload_users grant를 게시한다. private Observation 생성이나 숫자 budget 재구성은 금지한다. 기존 users fallback은 없고 단일 compiler/View가 권한을 판단한다. Root 고정 Workload class→전용 Pum RPC→Hop contract3 및 동일 paired ledger→실제 backend counter를 검증해야 한다. Human 세션은 별도 owner가 필요하다.

거부 행렬은 audience/서명/issuer/실제 SA·Pod UID/원천 설정, 종류 충돌, grant 삭제와 기존 permit Observe, resource/action/network/class/AAL, 리뷰어 RBAC 철회, provider/sign/output 지연, record 누락/owner 교체/재시작, replay, 최종 TLS/connect 지연 및 backend 미호출을 포함한다. 실제 다른 SA/Pod의 유효 token은 다른 subject이며 grant에서 거부해야 한다. cluster realm은 고정 설정이지 TokenReview의 가상 attestation 필드가 아니다.

Hop 원래 1초 수명은 성공한 원천 관측의 재사용 상한이다. Kubernetes Pod/SA 삭제부터 새 TokenReview 거부까지 1초라는 뜻이 아니다. 공식 문서는 pending deletionTimestamp 이후60초 이상의 거부 조건을 설명한다. API 전파 지연(별도 bounded polling, 초안90초)과 원래 proof 만료를 분리 측정하고 실제 결과를 기록한다. 즉시 원격 철회를 주장하지 않는다.

전역 Role/Binding cleanup은 생성 UID를 기억하고 DeleteOptions UID precondition으로 자기 객체만 삭제한다. CRD는 이 Workload fixture에 필요 없다. 토큰/키/CA 운영값은 로그·문서·evidence에 넣지 않는다. 실제 실행·전체 체인·browser·성능·릴리스 완료를 주장하지 않는다. 상세 순서/공식 출처/검증 행렬은 영문 문서를 따른다.

runner는 실제 namespace/SA/Pod UID, 최소 리뷰어 권한, 고정 CA/issuer, Pod-bound token을 준비하고 공개 SDK subject와 대조한 후 Pum CAS grant를 게시한다. backend counter, 잘못된 audience/UID/issuer/cluster 연관, users fallback, 리뷰어 권한 철회/복구, 실제 Hop Pod 재시작, bound Pod UID 교체와 새 grant, SA 삭제를 검증한다. API TokenReview 거부와 전송 오류는 구분한다. 기존 Service/browser 관리 단계로 넘어가지 않으며 Human/전체 관리자 UX 완료를 주장하지 않는다. 같은 쌍을 실제 수신자 재시작 너머 보존해 durable replay를 확인하는 게이트는 아직 남아 있다. 즉시 pair 재사용과 보유 인증 거부 도구가 추가됐지만 실제 실행은 대기다. 한계는 LIMIT으로 출력한다. 실제 실행은 이번 작업에서 하지 않았다.


## 별도 mTLS tap 통합

추가 필수 인자는 `--workload-backup-evidence`, `--workload-held-client`, `--workload-tap-image`다. capability version1에 qualification_tools.workload_tap의 정확한 image/source/binary_sha256가 필요하다. 정확한 동결 해시와 schema는 영문 문서를 따른다. 기존 faa10e probe는 변경 없이 유지한다. 모든 검사는 kube wrapper 해석·변경 전에 수행한다.

백업 evidence는 version1/cold_snapshot=true/offhost_verified=true/offhost_path/bytes/sha256를 포함한다. 로컬 오프호스트 파일의 크기와 전체 SHA를 스트리밍 검증하며 파일을 변경하지 않는다. cold 상태·tar 검증·클러스터 독점 lease는 운영자 검토 근거이며 해시 검사만으로 자동 증명되지 않는다. Node utility와 echo도 digest로 고정한다.

소유 namespace에만 workload-tap Deployment/Service를 만든다. 별도 서버/클라이언트 인증서와 고유 caller를 사용하고 API token 자동 마운트/권한은 없다. Root→tap→실제 Hop으로 Verify 및 Workload RPC를 전달하며 Pum 인증/plan 관측은 실제 Hop 직결을 유지한다. 실제 첫 contract3 성공 이후 Root가 원래 route Capture를 보유하며 기다리는 동안 동일 ID/contract/query bytes를 다시 제출한다. 전후 실제 auth/Pum owner를 관측하고 호출 전 BOOTTIME/rate/quantum과 최초 deadline을 유지한다. 첫 응답은 변경하지 않으며 추가 지연은 Root 원래 예산으로 차감한다. 임의 route mint/export나 public capability 생성자는 없다.

최초 권한 허용 HTTP는 새 tap PASS1개와 backend1회를 모두 요구한다. 실패/누락/중복 증거는 실패다. Hop Unavailable은 ledger/원천 거부를 합친 상태이므로 SQL 행 원인까지 단정하지 않는다. 실제 수신자 재시작 뒤 durable pair replay는 미완이다.

보유 인증 프로세스는 stable tap 연결을 통해 실제 Hop 교체 전 context/receipt를 유지한다. 교체 후 같은 연결의 별도 새 proof 성공과 기존 held 거부를 각각 확인한다. 원래1초 만료만으로도 거부될 수 있으므로 재시작이 원인이라고 단정하지 않는다. 잘못된 고정 authority 설정은 probe startup trust 거부로 분리하며 실제 원천 거부로 세지 않는다.

순수16개/기존 composition renderer3개 테스트 통과. 클러스터·SSH·Cargo 실행 없음. 최종 승인 바이너리로 실제 네 코어 전체 Workload 게이트는 반드시 별도 수행해야 한다. Human·Workload 관리자/browser UX 완료를 주장하지 않는다. 정리는 원래 UID precondition을 유지하고 한 객체 충돌 시에도 나머지 소유 객체 정리를 시도한다.

Pum workload_resource_metadata_decision 및 Root workload_typed_http_preliminary_gate capability도 필수다. 이전 일반 Workload flag만으로 사전 검사를 통과하지 못한다. 여전히 검토된 주장이지 바이너리 자동 증명은 아니다. 기존 선택적 Sum CRD 경로는 create 응답에서 원래 UID를 직접 보존해 create→GET 교체 간격을 없앴다. Workload와 CRD 결합은 계속 거부한다.
