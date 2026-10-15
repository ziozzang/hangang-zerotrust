# 실제 Sum 네트워크 원천 fixture

`sum_runtime.py`는 새 SQLite DB·enforce bootstrap·실제 production Sum의 필수 mTLS Network/Check를 사용한다. 가짜 network proof peer가 아니다. 기본 public0.3.6 binary SHA와 실제 network.proto SHA를 고정하며 로컬 grpcio/grpcio-tools 환경만 사용한다. Cargo·인터넷·클러스터·운영 쓰기를 하지 않는다.

[영문 계약](SUM_RUNTIME.md)의 인자와 JSON 명령을 따른다. 새0700 디렉터리·0600 원자적 ready·loopback 임의 포트·자체 TLS/관리자/collector 키를 사용한다. 공유 CA를 지정하면 실제 localhost/127 SAN과 serverAuth/clientAuth 인증서가 필요하며 TLS가 이를 검증한다. ready에는 경로·해시만 있고 비밀값은 없다. Pum은 실제 이 endpoint와 collector 파일을 사용해야 하며 clientIP도 실제 신뢰 경로와 같아야 한다.

`deny`는 실제 policy document CAS로 allow 예외를 지운 다음 실제 block을 추가한다. `restore`는 CAS allow 복구와 block 삭제 후 실제 gRPC를 확인한다. 빈 allow를 deny-all로 취급하거나 없는 deny 필드를 만들지 않는다. 두 관리 동작은 하나의 원자적 거래가 아니다. 독립 block은 allow 우선순위 때문에 단독 거부를 보장하지 않는다. 기존 상태를 임의로 덮어쓰지 않는다.

실제 opt-in 테스트는 Allow→CAS/block Deny→오래된 CAS409·거부 유지→복구 Allow, revision 증가, 잘못된/관리자 caller 거부, client 인증서 누락 거부, listener 종료를 검증한다. 제어 명령은 예산을 늘리지 않는다. 소유 자식 handle/process group만 정리하고 비밀·본문·토큰은 출력하지 않는다. 이 결과는 Human 네 코어·Kubernetes 원천·분산 DB·처리량 완료 주장이 아니다.
