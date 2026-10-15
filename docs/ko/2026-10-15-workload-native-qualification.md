# Native Workload 실제 검증 — 2026-10-15

실제 K3s run2가 exit0으로 완료됐다. 정적 후보는 한강 f45fe3e, 호패848dc835,
품계adaf985, 수문장d6fc1dec이며 테스트 도구는504f5c3다. 새 공개 릴리즈·운영
교체를 의미하지 않는다. 두 노드는 한 물리 호스트에 있으므로 다중 호스트 HA가 아니다.

공개 SDK가 실제 bound ServiceAccount/Pod 신원(kind3/AAL0)을 검증하고, 검증한
subject만 workload_users에 부여했다. 실제 한강 요청이 품계 전용 Workload 사전
판정·native permit·contract3 인증 변환을 거쳐 백엔드에 도달했다. 원래 시간·소유권
검사를 유지하면서 동일 증거쌍 재사용을 거절했다. legacy users 권한 차용, 누락·잘못된
audience·변조 credential, 고정 authority 불일치와 realm 변경은 각 경계에서 거절됐다.
realm 변경과 복원은 실제 DB 소유 CAS 게시와 정확한 읽기 확인으로 수행했다.

호패 Pod 교체 후 같은 공개 연결에서 새 증거는 성공하고 보관한 예전 증거는 거절됐다.
단 원래1초 만료도 예전 증거 거절을 설명하므로 재시작만의 효과로 단정하지 않는다.
reviewer 권한 회수·복구, Pod UID 교체 후 기존 grant 거절·새 grant 부여, Pod/SA 삭제에
따른 인증 거절을 확인했다. 원천 API TokenReview 거부까지 Pod 약36.2초·SA 약10.9초가
관측됐다. API 전파 시간과 원래 증거의 최대1초 수명은 별개다. 복구 중503/backend0만
허용하다200/backend1이 됐으며 요청별 시간 예산을 늘리지 않았다.

초기 관찰에서 네 코어·tap·echo 모두 Ready였고 실제 imageID가 각 노드의 승인 import
manifest digest와 일치했다. Pod API의 manifest ID를 관측했으며 실제 config ID·프로세스
UID를 별도 검사한 것은 아니다. 코어·tap의 nonroot UID65532·읽기 전용 rootfs·권한 상승
금지·capability drop 선언을 확인했다. Echo의 보안 설정 완성은 주장하지 않는다.

소유 namespace·전역 자원은 UID 조건으로 정리됐다. 노드2개 Ready·기존 Pod UID12개
유지, Echo/Ingress200·익명 Headlamp API401을 재확인했다. 콜드 백업·전체 SHA 검증한
오프호스트 사본은 보존했으며 실제 복원 리허설은 미실시다.

run1은 bootstrap만 변경해 DB 소유 profile 변경에 실패한 실행으로 보존한다. 부분 성공과
실제 코어 image attestation 미확보를 전체 통과로 고치지 않는다. 수정 도구의 순수 테스트
28개는 stale·응답/읽기 불일치·복원·응답 유실 시 변경 재전송 없는 상태 확인을 검증했다.

다음 필수 단계는 동일 후보의 별도 실제 Service/composition·컴파일된 콘솔/브라우저
검증, 서명 공개 자산 왕복 검증, 백업 후 내부 반영이다. Human/MFA·Workload 관리자 UX,
Kubernetes 인증/인가 webhook 원천, 외부 DBMS 어댑터, fleet/복제/rollback 및 처리량은
이번 통과 범위에 포함되지 않는다.


## 후속 Service·실제 설치 관리자 검증

동일 f45/848/adaf/d6fc 동결 후보로 로컬 observed All·strict All·기존 bearer 회귀를
통과했다. 별도 실제 K3s 일반 Service 실행도 임베디드 관리자/브라우저·수문장 native
원천·회수/재시작 검증을 통과했고 코어/echo Ready5개의 실제 imageID가 노드별
승인 import와 일치했다. All 혼합 인증 재실행은 실제 SDK·HTTPS relay 서킷·브라우저
검증을 통과했다. 설치한 호패0.1.6·수문장 plugin0.1.4의 실제 EN/KO 전환에서 초안/DOM을
보존하고 추가 owner 요청이 없었다. 호스트 메뉴와390px도 통과했으며 소유 namespace/CRD
정리 후 기존12PodUID가 유지됐다.

첫 All 브라우저 실행은 수문장 내부 요소가 없어 전체 실패했다. 앞선 native 인증·SDK·
서킷은 통과했으나 당시 도구의 안전한 mount 오류 근거가 부족해 원인을 특정하지 못했다.
재실행은 API 모의 응답·selector 완화·증거 예산 변경 없이 경로/상태/시간과 alert 해시
진단을 추가했다. 재실행 성공을 첫 실패 원인의 설명으로 간주하지 않는다. 두 기록을
보존한다. standalone hangang-console SSO나 모든 오류/언어/in-flight 상태 완료는 아니다.

이후 상태 페이지 펜테스트에서 TLS400/HSTS 경계가 추가 확인됐다. 운영 한강에는 두
호스트 HSTS 설정을 적용했지만 소스 수정은 새 후보이므로 전체 소스·정적 빌드·정확한
바이너리의 후속 검증이 필요하다. f45 결과를 새 보안 후보의 릴리즈/운영 완료 근거로
대체하지 않는다.
