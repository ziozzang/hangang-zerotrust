# Hangang 0.3.11 / Pumgye 0.1.9 후보 검증

상태: 정확한 후보 gate를 통과한 Hangang0.3.11·Pumgye0.1.9 서명 릴리스를 공개하고 gateway→Pumgye→standalone console 순서로 검증 receipt와 함께 운영 적용했다. gateway build source `0b15bfb7`, 문서 전용 release target `f352a1ca`, Pum runtime `435f1389`(observed-authentication), Hop `848dc835`, Sum `d6fc1dec`, 시험 전용 tap `640a3dd4`를 구분한다.

| Gate | 실제 결과 | 범위 |
| --- | --- | --- |
| 전용 Kubernetes SAR | 최종 run4, 18건, 종료0 | 실제 API server·검증 mTLS webhook, authorization cache 비활성, source 교체 없는 PATCH grant 철회, AAL/class 구분, 장애 거부·복원. 기존 cluster authorizer는 변경하지 않음. |
| Service Any + browser | 최종 Pum435 실행 종료0 | 실제 네 컴포넌트·native source·독립 SDK·compiled host navigation·Pum responsive·설치 plugin locale. 전체 관리자 UX 완료는 아님. |
| Workload | strict helper `73533380`의 run4 종료0 | 실제 TokenReview·공개 SDK·typed grant·contract3, 첫 응답 반환 전 원래 pair replay와 owner 검사, 철회·reviewer 권한 철회·Hop 재시작·bound Pod UID 교체와 명시적 새 grant·ServiceAccount 철회. |

각 최종 실행은 생성 자원을 정리하고 기존12개 Pod UID/phase와 Ready 노드2개를 독립 보존 확인했다. Workload는6개 Ready 이미지 identity를 import manifest/config 근거와 대조하고 현재·이전 상태/로그를 보존했다. 통과를 위해 assertion·요청 deadline·proof 수명·pooled channel을 바꾸지 않았다. 기존 복원 검사에서는 503/backend0 두 번 뒤 성공을 관측했다.

과거 실패는 유지한다. Workload run1 최초 미인가 응답 timeout과 run2 재시작 뒤 strict403 대신503은 원인 미확정이다. run3는 새 안전 Verify event와 replay parser의 호환 누락으로 실패했으며 strict schema 검증·별도 진단 저장으로 수정했다. 새 직접 SDK 연결은 기존 Root/tap 연결 복원을 증명하지 않는다. run4는 독립 통과이며 run1/2 원인 해결 주장이 아니다.

SAR 과거 실패는 공식 바이너리 file capability와 nonroot 실행, 잘못된 loopback 광고 주소, Go REST webhook `?timeout=3s` 상호운용 문제를 드러냈다. 최종 fixture는 nonroot/dropALL/권한상승 금지를 유지하고 Pod 주소와 엄격한 timeout query parser를 실제 API traffic으로 검증했다. 권한 확대·bypass로 해결하지 않았다.

Pod37.102초·ServiceAccount10.881초 관측은 API 전파 시간이며 원래 비갱신1초 evidence 예산과 별개다. 재시작 후 held 거부에는 원래 만료도 작용할 수 있다. 평탄화 replay 거부는 특정 SQL row 증명이 아니다. Human·Workload 관리자/browser·H2 stream owner·인과적 suspend/source-age·극단 처리량은 범위 밖이다. 전송 fence는 kernel 수락 bytes나 이미 허용된 작업을 회수하지 못한다. 운영 acceptance는 gateway revision268·UID1000:1000·host network를 유지하고 설치 gateway/console 해시·native authority/configuration·새 Pum JavaScript 자산과 실제 HSTS16건을 확인했다. 일관된 SQLite 및 binary/unit/config rollback 백업을 보존했다. 최종 운영 적용 후 browser 실행은 이 checkpoint에서 진행 중이며 위의 정확한 후보 소유 browser gate 통과와 구분한다. 더 넓은 운영 browser 완료를 주장하지 않는다.
