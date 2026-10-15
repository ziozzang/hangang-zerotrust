# Native Human 원천 scope 결합

상태: 구현 후보 검증 중이며 운영 Human endpoint 또는 전체 체인 검증 완료가
아닙니다. [English](../reviews/2026-10-16-human-source-scope-binding.md).
[Human wire 설계](2026-10-16-human-native-wire-design.md)를 보완합니다.

service/audience와 최종 요청 digest만으로 독립 검증자가 실제 앱·라우트·헤더
manifest를 알 수 없습니다. 전역 원천 revision은 여러 scope에 공통일 수
있으므로 호출자가 제시한 resource/route 이름으로 원천 scope를 추정하면 안 됩니다.

HumanReceiptTimeReply에 `bytes scope_sha256 = 10`을 추가합니다. 원천은 실제
Engine이 생성한 record에 보관된 compiled scope에서 값을 읽습니다. ObserveTime은
정확한 proof/context/request digest와 현재 owner를 재검증한 뒤 고정 mTLS 연결로
보고합니다. 해시만으로 인증·권한·원천 record를 복원할 수 없습니다. 기존
Service/Workload 메시지와 요청 바인딩 코덱은 바꾸지 않습니다.

SHA256 입력은 다음 순서입니다.

1. `hopae:native-human-scope:v1` 뒤 NUL.
2. service/audience/app ID/route ID 각각 LP32.
3. BE u64 route revision, destination raw32.
4. BE u64 header-policy revision, BE u16 bound-header 개수.
5. ASCII 오름차순으로 정렬한 각 bound-header 이름의 LP32.

LP32는 BE u32 바이트 길이와 정확한 UTF-8 바이트입니다. native ASCII 식별자,
양의 safe revision, 0이 아닌 destination과 기존 H1 header-policy 검증을 유지합니다.
동일한 허용 slot 목록에 대한 추가 reserved filter·본문 크기 상한은 해시에 넣지
않지만 검증은 필수입니다. 본문·헤더 값·쿠키는 넣지 않습니다.
[독립 벡터](../../fixtures/human-scope-v1.json)는 전체 preimage와 SHA를 기록합니다.
원천과 SDK는 설정 준비 때 한 번 계산합니다.

SDK는 보고된 32바이트를 proof의 service/audience 및 고정 설정 scope와 비교합니다.
발급은 여러 sibling scope가 허용되어도 실제 준비한 scope와 일치해야 합니다.
독립 Observe 준비 데이터만으로 opaque Observation을 만들지 않습니다. 실제
인증된 보고를 통과한 뒤에만 검증된 불변 scope 참조를 노출하며 consuming refresh도
같은 지문을 유지합니다. 누락·0·다른 앱/라우트/destination/header 지문은 거부합니다.

품계는 검증된 scope를 실제 route/plan owner와 결합하며 본문을 꾸며내거나 요청
해시를 인증 원천으로 취급하지 않습니다. 실제 OIDC/LDAP/TOTP·generated mTLS·공개
opaque SDK와 scope 변조 거부를 통과해야 H2/H3를 검증 완료로 볼 수 있습니다.
코덱 벡터와 mock 보고만으로 완료를 주장하지 않습니다.
