# 네이티브 사전 인증 시계 후속 과제

상태: Sol 소스 검토·제안이며 미구현·물리 실험 미완이다. Astra는 중단 상태다.
사전/최종 신원 연결 수정과 분리하며 해당 수정의 검증 범위를 확대하지 않는다.

일반 native Verify의 고정 machine deadline과 갱신형 스트림은 현재
`std::time::Instant`를 사용한다. Linux suspend 동안 이 시계가 멈출 수 있다.
최종 observed SDK는 별도 BOOTTIME 경계로 백엔드 전달을 보호하며, 해당 최종 경계의
우회는 확인하지 않았다. 기존 Lua 미도달 검사는 다른 신원 종류·잘못된 AAL·사전 권한
거부에 한정한다. suspend를 포함한 Lua 전 인증 만료나 이후 신원 불일치 시 Lua 효과
취소까지 증명하지 않는다.

후속 구현·검증 조건:

- TTL 생산자별 최초 증거 잔여 수명과 신뢰한 legacy 로컬 cap을 구분한다.
  TTL 누락을 서명된 원천 freshness로 취급하지 않는다.
- 최초 Verify RPC 전에 suspend를 포함하는 수신자 시계를 캡처하고 실제 생산자/수신자
  속도·양자화 경계를 적용한다. 큐·전송 시간을 모두 차감한다. 호스트 간 절대 시계를
  비교하거나 legacy TTL을 observed receipt로 바꾸어 부르지 않는다.
- 갱신 전·await 후·새 deadline 게시 직전에 기존 deadline이 살아 있어야 한다.
  새 성공 응답으로 만료된 스트림을 되살리지 않는다. 시계 실패는 권한을 회수한다.
- 비공개 결정적 시계로 suspend·최초 RPC 지연·원천 정지·갱신 중 만료·Lua/스트림 효과
  전 거부를 검사한다. 플랫폼 지원 범위와 실제 물리 실험을 구분한다.

이 과제로 observed 연결 pooling·증거 수명 변경·VM clone/rollback 안전성을 묵시적으로
완료 처리하지 않는다. 구체 API와 기존 기본 모드 호환성은 구현 전에 검토해야 한다.
