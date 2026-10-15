# 공개 Workload 검증 도구

운영 코드가 아닌 별도 검증 crate입니다. 기존 `native-workload-probe` 소스와 동결 faa10e 바이너리는 변경하지 않습니다. 공개 SDK4ea3e147/Pumac47d448을 사용하며 capability 생성자나 route mint/export API를 추가하지 않습니다.

`observed-workload-pair-probe`는 기존 인증 설정으로 `allow`, `deny`, `hold`, `held-refuse` 명령을 받습니다. hold는 정확한 context/receipt를 메모리에 보존하고 이후 독립 관측합니다. Pod 재시작이 원래 최대1초보다 오래 걸리면 단순 만료로도 거부되므로 원인을 재시작/철회로 단정하지 않습니다. 인증은 권한이 아닙니다.

`workload-replay-tap`은 별도 opt-in mTLS 중계기입니다. Root의 Hop peer만 중계기로 향하게 하고 Pum·plan의 Hop 관측은 실제 Hop으로 유지합니다. Verify 및 Workload 인증 RPC를 고정 실제 Hop으로 전달합니다. Project는 실제 Hop 첫 성공 이후, Root가 원래 route Capture를 유지하며 기다리는 동안 같은 auth/permit owner를 관측하고 동일 requestID/contract/permission_query 바이트를 즉시 다시 전달합니다. 재사용 거부와 전후 owner 유효성을 확인한 뒤 첫 응답을 변경 없이 반환합니다.

실제 Hop은 원천/ledger 거부를 Unavailable로 합치므로 특정 SQL 행이 원인이라고 단정하지 않습니다. 관측은 호출 전 BOOTTIME anchor와 기존 SDK rate/quantum 산술로 지연을 차감하고, 첫 관측의 로컬 최저 deadline을 이후에도 유지합니다. 원래1초 예산을 늘리지 않습니다. 추가 지연은 Root가 원래 RPC 예산으로 차감해야 하며 운영 성능 경로가 아닙니다.

설정 필드와 예약 도메인 예시는 영문 README를 따릅니다. 동시성1, 고정 메시지 한도, caller 인증, inbound mTLS, 고정 outbound HTTPS를 사용합니다. 증거/비밀 값은 로그에 출력하지 않습니다. 일부 보유 버퍼는 Zeroizing이지만 일반 RPC/transport 사본 전체의 메모리 삭제를 보장하지 않습니다.

단위 및 실제 생성 RPC loopback 테스트는 동일 바이트 재전송·잘못된 caller 차단·첫 응답 보존·재사용 성공 시 실패·원천 만료 시 비밀 미반환을 검사합니다. loopback은 평문 테스트 fixture이며 실제 암호/원천 전체 체인 검증이 아닙니다. 최종 Root0.3.10 실제 코어·TokenReview·Pum policy·backend 연결 검증은 부모 담당 후속 게이트입니다. 이 작업은 SSH/클러스터/서명/공개/배포를 수행하지 않습니다.
