# 실제 native Human 네 컴포넌트 로컬 검증

이 도구는 검토된 manifest의 실제 Hangang/Hopae/Pumgye/Sum 바이너리만 실행한다. 실제 OIDC 포털 계정과 세션, 공개 SDK Issue/독립 Observe, 소유 정책 CAS, 실제 Sum/Root route owner/Hop contract4를 연결한다. 서명·route capability·비공개 Observation을 만들어 내지 않으며 운영 서비스나 클러스터에 접근하지 않는다.

manifest는 네 컴포넌트별 바이너리 경로·실측 SHA·검토된 전체 소스 commit을 요구한다. 선택 provenance 경로/SHA도 고정할 수 있다. 소스 좌표는 별도 검토 사실이며 버전 문자열로 증명하지 않는다. 바이너리의 이전 base commit을 실제 소스로 표기하지 않는다. 실행 명령과 정확한 필드는 [영문 문서](README.md)에 있다.

새 CA와 컴포넌트별 leaf, 검증된 mTLS 및 고정 caller를 사용한다. Root→tap과 tap→Hop caller는 다르며 Pum은 실제 Hop에 직접 관측한다. 공개 raw tap은 원래 payload/deadline을 전달하고 재시도·증거 갱신을 하지 않는다. 본문·자격 증명·오류 메시지 대신 제한된 method counter만 보존한다. Root의 decision RPC도 같은 inbound caller를 쓰되 실제 Hop/Pum outbound caller는 분리한다. 실제 Pum의 기존 Authorization.Decide health(2048bytes), HumanResourceAuthorization.Decide(2048bytes), Human permit Issue(8192bytes)만 추가 전달한다. 관리 HTTPS는 Pum에 직접 연결하며 첫 authorization에 시작하는 Root watcher의 사전 성공을 꾸미지 않는다.

Hop의 Source/receiver/permit key/plan은 첫 로그인 전부터 설정한다. 실제 origin과 route11/header policy13/x-tenant를 고정하고 Authorization 자격 슬롯은 제외한다. Root/Pum/Hop은 db:orders/select를 동일하게 쓴다. 공개 SDK가 독립 검증한 두 Human subject만 실제 HTTPS CAS로 배정한다. 네트워크 AAL1과 사용자 AAL2 요구를 분리하며 네트워크에 AAL2 역할을 넣어 AAL1 양성을 주장하지 않는다.

첫 실제 POST는 backend204와 요청·효과 각각 정확히1 증가, 실제 본문 SHA, cookie/native identity/caller 제거를 요구한다. 실패 응답은 알려진 고정 오류 enum/길이/SHA만 남긴다. 재시도·예산 완화·상태 허용 확대는 없다. 프로세스 group guardian은 core가 먼저 종료돼도 PGID를 보유하며 supervisor 사망 시에도 자기 group만 정리한다. 종료 상태는0600 임시 파일/fsync/atomic replace로 공개한다. 모든 cleanup을 시도하고 원래 실패를 보존한다.

현재 구현·순수 테스트와 실제 통과는 구분한다. 로컬 시도의 admin 설정 누락, 과도한 fixture network AAL에 따른 올바른403, 이후 최종 native503/backend0 실패는 보존한다. 네 컴포넌트 통과나 제품 수정으로 주장하지 않는다. 실제 양성/적대/replay/provider별 흐름, suspend·분산 철회·처리량은 별도 근거가 필요하다. 새 요청 철회 검사는 진행 중 작업의 원자적 철회를 증명하지 않는다.
