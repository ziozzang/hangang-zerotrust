# 네이티브 Workload 신원 전달 구현 제안

상태: 설계 제안. 네이티브 정책 구현을 시작했으며 전체 연결은 미구현이다.
기존 Service 검증 결과는 Workload·Human 지원 완료를 의미하지 않는다.

실제 호패 TokenReview 결과를 Workload/AAL0 그대로 전용 추가 RPC·SDK 증명·품계의
실제 컴파일 정책·호패의 paired 출력·한강의 최종 전송 검사까지 전달한다. 요청 헤더가
신원 종류나 인증 수준을 지정해서는 안 된다. 기존 Service API·신뢰·기본 활성화는 유지한다.

제안하는 wobs1 원천 epoch는 프로세스·authority·프로필·애플리케이션 세대를 묶는다.
발급자가 정확한 서명 증명과 TokenReview 이전 BOOTTIME 시작을 소유한 제한된 기록을
보관한다. 첫 증명은 원래 시작부터 최대 1초이며 갱신할 수 없다. Observe는 줄이기만
하며 새 인증이나 새 deadline을 만들지 않는다. Pod 삭제 철회는 실제 TokenReview 관측과
남은 짧은 유효기간의 제약을 받는다. 외부 철회가 즉각 반영된다고 주장하지 않는다.

품계는 같은 snapshot·컴파일러·View에 선택적 workload_users를 추가한다. Workload
판정은 이 map만, 기존 Service·legacy 판정은 users만 조회한다. subject 문자열이 같아도
교차 허용하지 않는다. 리소스·행위·역할 상속·정보등급·인증 수준·네트워크 조건을 함께
검사한다. Kubernetes mapping v1 의미는 유지하고 명시적 v2에서만 typed grant를 만든다.

새 출력 경로도 기존 paired replay ledger를 공유한다. RPC·contract 번호를 바꿔도 소비한
nonce를 재사용할 수 없다. Human은 실제 세션·핸들·사용자·팩터 owner와 검증된 AAL·철회
검사가 별도로 필요하다. API 인증 조합·Workload 인증을 Human MFA로 간주하지 않는다.

완료 조건은 실제 pod-bound TokenReview·품계 Allow/Deny·독립 SDK·네 서비스·백엔드
카운터 검증이다. 잘못된 audience·신원, 원천 회수, 원래 유효기간 만료, 재시작, replay,
최종 쓰기 철회가 모두 백엔드 영향 없이 거부되어야 한다. Service 회귀도 유지한다.
프로토콜 canonicalization·기록 보존/용량·매핑 호환성은 활성화 전 독립 검토 중이며
아직 새 릴리즈 완료를 주장하지 않는다.

## 프로토콜 활성화 전 검토 보강

관측 clock domain은 epoch의 32자리 프로세스 nonce와 같아야 한다. 전체 epoch나 별도
생성 domain으로 혼동하지 않는다. 콜론을 포함한 authority도 재인코딩 byte 일치로 검사한다.
원래 증명 기록이 없으면 거부한다. 서명·UTC 만료·현재 프로필·수신한 남은 시간으로 잃은
capability를 재생성하지 않는다. 용량이 차면 아직 유효한 owner를 지우지 않고 발급을 거부한다.

최대 1초의 원래 허용 기록과 영속 paired replay 증거의 보존 수명은 다르다. 원래 허용이
끝났다고 소비한 인증·권한 nonce 기록을 조기 삭제해서는 안 된다. replay는 전체 서명 증명의
상한까지 보존한다. receipt 만료와 최초 원래 예산의 관계도 구현 전에 함께 검토한다.

mapping v2 candidate는 버전과 outcome별 principal class를 명시한다. v1 직렬화는 그대로
유지한다. 기존 v1 candidate나 legacy subject 할당을 typed Workload 권한으로 승격하지 않는다.
