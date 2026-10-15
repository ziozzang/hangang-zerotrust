# 두 계정 OIDC·고정 scope 어댑터

`two_account_runtime.py`는 별도 테스트 어댑터다. 기존 검증된 `runtime_fixture.py` 바이트는 유지한다. 실제 portal 쿠키·TOTP 등록/승격·logout·원자적 비공개 파일·소유 자식 정리 함수를 재사용하지만 SQL 인증 행·proof·grant·SDK Observation을 만들지 않는다.

실행·JSON 필드는 [영문 계약](TWO_ACCOUNT_RUNTIME.md)을 따른다. `--source-scopes-json`은 요청이 아닌 서버 소유 시작 설정이며 한 번 읽고 검증한다. 한 실제 application의1..16개 명시적 route/destination과 고정 헤더 정책만 허용한다. 중복·잘못된 revision/destination·예약 헤더·알 수 없는 필드를 거부한다. 실제 Hop Source도 별도로 이를 검증해야 한다. 이 어댑터는 H4 receiver나 secret 설정을 활성화하지 않는다.

소유 loopback OIDC issuer의 a/b 계정은 서로 다른 RS256 subject를 발급한다. 실제 Hop가 issuer/audience/nonce/PKCE를 검증하고 실제 세션을 만들어야 한다. `human1`은 public SDK 실제 Issue·독립 Observe 결과에서 얻으며 도구에서 계산하지 않는다. ready는 양쪽 실제 AAL1 로그인 후0600으로 게시한다. `login`/`revoke`는 account와 AAL을 지정하고 실제 portal/TOTP/logout을 사용한다. 각 계정의 TOTP seed와 Browser 세션을 분리한다. TOTP 대기는 fixture 제어 시간이며 native proof 예산을 늘리지 않는다.

현재 열 Python 테스트는 실제 소유 OIDC 토큰 서명·subject 분리·nonce·일회용 code·PKCE 거부, scope 검증, 계정별 seed, 설정 전용 mocked startup을 검증한다. 별도 실제 공개 b08 production 바이너리(SHA50a447b0d437500745c248275a2fc413633482efc24229372c6f04ec73fac65e)로 단일 scope의 두 사용자 primary·독립 TOTP AAL2·A logout 거부와 B 세션 유지·자식 정리를 통과했다. SDK receipt·Pum·H4·Root/backend 검증은 아직 하지 않았다. 이전 단일 계정 결과를 새 체인의 완료 증거로 확대하지 않는다. 비밀은 출력하지 않고 소유 프로세스만 정리한다.
