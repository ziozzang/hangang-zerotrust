# 검증 전용 raw gRPC tap: 1단계

`grpc_tap.py`는 로컬 검증 전송 도구이며 인증 원천·서명기·capability 생성자·운영
프록시가 아니다. 고정한 loopback endpoint로 변경 없는 unary raw 바이트를 전달하고
단계별 횟수만 센다. protobuf 내용의 decode·로그·저장은 하지 않는다. cookie B
치환, Project replay, 실제 owner 현재성 확인과 4개 코어 성공 검증은 아직 구현하지
않았다. 정확한 설정과 명령은 [영문 계약](GRPC_TAP.md)을 따른다.

기존 grpcio 환경을 사용한다(이번 검증1.84.0). 디렉터리는0700, 설정·호출자·키
파일은0600으로 보관한다. 설정의 고정 method allowlist와 명시적 숫자 loopback
주소만 사용하며 DNS나 환경 proxy를 사용하지 않는다. 양쪽 TLS를 검증하고 수신
클라이언트 인증서를 필수로 요구한다. 각 전송의 별도 PKI/인증서를 설정할 수 있다.
서버 이름은 소유 localhost SAN이다. 호출자 파일에는 Bearer 접두사·개행 없는
32–256 ASCII graphic 바이트를 두며 수신·송신 호출자 값은 달라야 한다.

raw 수신 할당 상한은64KiB이며 실제 method별 더 작은 상한(영문 표)을 upstream
호출 전에 검사한다. 응답은32KiB 이하이다. 이는 raw 전송 검증이며 운영 protobuf
검증이나 인증 전 본문 poll 0을 입증하지 않는다. gRPC가 handler 전에 거부한 요청은
단계 계수에 없을 수 있다. 명시적 유한 원래 deadline이 필요하고 남은 시간을 최대
1초로 제한해 전달한다. 예산 갱신·retry는 없다. 취소하면 대기 중 upstream 호출을
취소하고 용량을 반환한다. upstream 상태 코드는 유지하되 오류 내용은 고정 문구다.

ready JSON은0600으로 원자 게시한다. stdin JSON 한 줄 `{"op":"snapshot"}`은
비밀 없는 단계 횟수만 출력하고 `{"op":"shutdown"}`은 종료한다. EOF/SIGTERM도
소유 서버와 channel을 정리한다. cookie·caller credential·receipt·query·출력
credential은 출력하지 않는다. 횟수는 권한이나 증명 원천이 아니다.

실제 TLS echo 테스트는 전송만 입증하며 Human grant나 실제 Hop/Pum/Root
증거를 대체하지 않는다. 후속 A/B 치환·원래 요청이 살아있는 replay에는 실제 wire
schema, 원래 deadline, 실제 Pum Observe와 Root route owner 생존 확인이 필요하다.
증명이나 별도 Source/nonce ledger를 만들지 않는다. 공개 검증된 H4와 통일된 SDK
pin 및 실제 전 경로 검증은 별도 필수 단계다.

launcher의 부모 PID 변경도200ms 주기로 감지하여 같은 정리 경로를 실행한다. stdin pipe가 열린 상태로 부모만 종료하는 실제 소유 subprocess 테스트가 listener 정리를 검사한다.

method 상한은 최대32KiB인 검증 부분집합으로 Source의128KiB frame 허용보다 좁다. Source의 모든 요청 크기를 검증했다고 해석하지 않는다.
