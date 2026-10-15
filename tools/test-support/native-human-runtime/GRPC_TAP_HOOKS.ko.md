# 명시적 사람 검증 hook (2단계)

[기본 raw 전송](GRPC_TAP.ko.md)에 선택적으로 추가하는 소유 로컬 보안 테스트다.
운영 프록시·인증·증명 검증·SDK Observation·grant 생성자가 아니다. `qualification`
설정이 없으면 기존 전송을 유지한다. 실제 A/B·replay·backend 성공은 공개 검증된
H4/Root와 통일된 SDK pin을 사용하는 별도 전 경로 gate가 필요하다.

정확한 설정 예와 공개 소스 SHA는 [영문 계약](GRPC_TAP_HOOKS.md)을 따른다.
공개 Hop b08 gateway.proto와 Pum f6 decision.proto를 한 번씩 제한된 크기로 읽고
고정 SHA를 검증한다. 기존 grpcio-tools/protobuf로 비공개 임시 descriptor set을
생성하여 별도 DescriptorPool에서 DTO만 파싱한다. 서빙 전 임시 파일을 삭제하며
SDK capability·서명기·다운로드·설치는 없다. 기존 최대32KiB method 부분집합과
용량 제한을 유지하며 Source의128KiB 전체를 검증하지 않는다.

`issue_cookie_b`는 Human IssueObserved의 단일 Cookie header 안 단일
`__Host-hopae` 값만 실제 B 세션의0600 파일 값으로 바꾼다(이름·개행·JSON 없이
값만, 최대4096바이트). 중복·누락·빈 값·이미 B인 cookie는 거부한다. 다른 cookie,
header, 원래 native 문맥·ID·고정 scope·최종 본문 메타데이터·unknown field는
유지한다. 초기 Verify와 나머지 method는 그대로 전달한다. 실제 양쪽 계정과 허용,
서로 다른 canonical 주체, A/A·B/B 성공 대조군을 runner가 입증해야 한다.
이는 명시적 악성 인증 peer fixture이며 운영 기능이 아니다.

`exact_pair_replay`는 첫 Project 응답을 제한된 메모리에만 보류하고 원래 raw
permission_query로 실제 Pum Observe → 원래 raw Project/ID/query 재사용 →
같은 raw Pum Observe 순서를 수행한다. 정확한 Unavailable와
`native Human projection refused`만 기대 거부로 받는다. 두 번째 성공, 임의의
Unavailable·TLS/전송 실패·잘못된 상태/문구·correlation/receipt SHA/domain/revision/
TTL0/양수·비증가 예산 검사 실패는 모두 실패다. Linux BOOTTIME으로 첫 Project
전부터 원래 출력·RPC 예산을 감쇠하며 갱신·retry를 하지 않는다. 성공 시 원래 첫
응답 하나만 그대로 돌려준다. 취소·응답 유실은 이미 소비한 pair를 소진할 수 있고
rollback을 의미하지 않는다. 비밀 payload의 로그·저장은 없으며 Python 메모리의
완전한 삭제를 보장하지 않는다.

**이 순서만으로 replay 원인을 확정하지 않는다.** Snapshot의
`requires_runner_query_budget_check: true`, replay BOOTTIME 경과 시간과 전후
Pum 하한을 runner가 읽어 실제 소유 Hop 시작 설정의 원래 query 예산 및 clock-rate
오차를 검증해야 한다. 호출자가 제시한 숫자나 proof 수명으로 대체하지 않는다.
replay가 실제 query 예산 안에 있었음을 보수적으로 입증할 수 없으면 inconclusive/
실패다. 살아있는 signed proof도 개별 query보다 오래 남을 수 있다. 원래 Root 요청과
route owner를 유지하고 실제 owner 대조군·Source pair ledger 테스트도 남긴다.
`control_sequence_complete`는 grant나 정확한 SQL 한 행의 소비 증거가 아니다.

재현 테스트에는 영문 문서의 두 공개 proto 경로 환경변수를 명시한다. 경로가 없으면
명시적으로 skip하며 다른 schema로 대체하지 않는다. 실제 소유 TLS 테스트 peer의
바이트는 증명이 아닌 fixture다. 파서 보존·raw 순서·오류 분류·예산·취소 검증만
수행하며 실제 H0/서명/SDK/permit/replay 소비/backend 성공을 주장하지 않는다.
