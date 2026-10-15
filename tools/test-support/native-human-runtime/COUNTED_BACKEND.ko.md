# 소유 HTTP backend 계수 fixture

`counted_backend.py`는 인증·권한 원천이 아닌 테스트 도구다. 영구 운영 서비스나 실제 사용자 설정에 연결하지 않는다. 실행 인자와 JSON 필드는 [영문 계약](COUNTED_BACKEND.md)을 따른다. 기존 `runtime_fixture.py` 바이트는 바꾸지 않는다.

새0700 디렉터리와 loopback 임의 포트를 사용하며 ready/result는0600 임시 파일·fsync·원자적 replace로 게시한다. 선택한 credential-header/file은 정확한 헤더 바이트를 검증하지만 값을 저장하거나 출력하지 않는다. stdin의 `snapshot`/`shutdown` JSON 명령만 제어 채널이다. EOF·SIGTERM·부모 종료 감지도 소유 listener를 닫는다. runner는 정확한 자식 handle의 종료를 기다려야 하며 SIGKILL 정리를 보장하지 않는다.

지원되는 HTTP 요청은 거부된 경우도 `request_count`에 반영한다. 고정 `/effect`에서 완전한 본문·정상 framing·credential 검증을 통과한 요청만 `effect_count`를 늘린다. 실제 부작용 검증에는 POST/PATCH를 사용하고 GET도 예상하지 않은 origin 도달을 감지한다. 최대 본문1MiB, 동시16개, socket1초와 요청별 연결 종료를 적용한다. 중복 길이·chunked·Expect·잘린 본문은 효과를 만들지 않는다.

기록은 method·안전한 고정 path·본문 길이/SHA256·헤더 이름·credential 존재/일치 여부뿐이다. 알 수 없는 target은 `[unrecognized]`로 기록하여 URL 비밀을 남기지 않는다. 본문·헤더 값·쿠키·토큰을 출력하지 않는다. 거부와 무실행 비교 사이에 계수를 초기화하면 안 된다.

실제 socket/child 테스트는 계수·framing 거부·개인정보·동시성·원자적 ready·종료를 검증한다. 두 계정/provider/scope 확장과 실제 네 코어 Human H4/Root 체인 검증은 아직 별도 작업이다. 분산 fencing이나 처리량·전체 완료 증거가 아니다.
