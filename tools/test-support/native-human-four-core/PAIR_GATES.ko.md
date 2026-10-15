# 실제 Human A/B 계보 및 정확한 pair 검사

`--pair-gate lineage|replay`는 기존8/9번 근거를 바꾸지 않는 로컬 선택 검사다. 실제 네이티브 계정·공유 Hop Source·실제 Pum/Sum/Root route capture·같은 canonical ledger를 사용하며 서명·route reference·opaque 관측을 만들어 내지 않는다. 같은 실행에 fresh MFA 검사를 섞지 않는다.

A/B는 tap 시작 전에 실제 Hop 포털에서 로그인한다. Source 설정/프로세스를 다시 시작하지 않는다. 공개 SDK Issue와 독립 Observe로 얻은 두 canonical subject를 실제 Pum CAS로 모두 허용한다. unarmed 상태의 A/A·B/B가 각각204/효과1을 통과한 뒤 private 단방향 arm을 한다. 새 A 요청의 일반 Verify/정책은 A로 유지하고 Source Issue의 cookie만 실제 B로 바꾼다. Verify·Human Decide·실제 Source Issue 성공을 요구하며, 이후 Root503/backend0·Pum Issue0·Project0이어야 한다. 정책 거부를 계보 검증으로 오인하지 않으며 이전 Lua 효과를 되돌린다고 주장하지 않는다.

replay도 unarmed 양성 후 arm한다. 실제 Root 요청의 새 auth/permit pair로 첫 실제 Hop Project가 성공한 직후, 원래 응답을 Root에 돌려주기 전에 실제 Pum Observe→동일 raw Project/ID replay→실제 Pum Observe를 실행한다. Root capture는 계속 소유된다. 원래 증거의 유효성과 단조 감소를 확인하고 첫 응답은 바꾸지 않는다. backend 효과는 정확히1이어야 한다. 재접속·증거 갱신·예산 확대를 하지 않는다.

고정 파서는 PUBLIC b08 gateway 전체 snapshot(SHA745a367...)과 f6 Pum snapshot(df2ed98...)을 명시적으로 사용한다. 실제 Hop/SDK는 e1dd이며 b08→e1dd 차이는6줄의 additive 서비스뿐, 메시지 정의는 byte 단위로 동일하다. 파서 snapshot을 네이티브 신뢰와 혼동하거나 실제 파일을 잘라 이전 해시를 꾸미지 않는다. 전체 commit/path/SHA는 [영문 문서](PAIR_GATES.md)에 있다.

거부 상태만으로 ledger 원인을 단정하지 않는다. 실제 Hop 시작 파일은 기본과 같은 verify_budget_ms400을 명시한다. native Human admission은399ms이며 spawn 직전 설정 SHA와 검사 시 읽은 바이트가 같아야 한다. 첫 Project 호출 전부터 replay 완료까지의 BOOTTIME 경과에 실제 rates500/500을 적용해 `ceil(ns*(1000000+500)/((1000000-500)*1000000))+2` ms를 보수적으로 계산하고399보다 엄격히 작아야 한다. 추가2ms는 native tick 양자화와 remaining-at의 추가 차감을 보수적으로 반영한다. 경계·변경된 설정·다른 예산은 실패/불명확이며 TTL이나 caller 숫자로 대체하지 않는다. 네이티브 ledger/rollback 테스트도 함께 근거로 사용하고 분산 원자성이나 모든 실패 원인 배제를 주장하지 않는다.

결과에는 상태·counter 차이·해시·scope/AAL·경과 시간·정리 정보만 남긴다. cookie·proof·secret 값은 공개하지 않는다. 실제 실행과 순수 제어 테스트를 구분하며 진행 중 철회·다른 provider·운영 반영·처리량은 별도이다.
