# 네이티브 Human 소스 검증 현황 — 2026-10-16

상태: 검증한 소스 기반이며 **Human 런타임 릴리스·전체 경로 활성화는 아니다**.
[English](../reviews/2026-10-16-human-source-checkpoint.md).

| 요구 | 현재 근거 | 남은 작업 |
| --- | --- | --- |
| 실제 인증 원천 | 호패87d19a0 H0 및 후속b317120398d95c2f87f08069ced1c5b6a395ba5a | 공개 Human issue/observe/SDK·최종 집행 |
| 최종 요청 바인딩 | 호패eefc358·독립 v2 벡터, SDK 기본60/native62·바인딩9·strict Clippy | 실제 요청·Human 원천·최종 전송 연결 |
| 영구 계정 namespace | 호패b317120: schema10 불변 공개 realm·ID 영구 예약·같은 Current 트랜잭션 join. 전체1125/0/43·strict Clippy/fmt·실제 소유 LDAP LDAPS/필수 StartTLS·OIDC/TOTP/CLI 재시작 통과 | 실제 고정 issuer/현재 Store 원천에서 human1 도출·proof/SDK |
| typed Human 정책 | 품계9c3d69aee4f0691fe166a49c382be8e8aaa0620d: 독립 human_users·같은 컴파일러·AAL1/2·fallback 금지·IP/수문장/등급 교집합·API context/template 금지. 기본133/전체142·양쪽 strict Clippy/fmt | 실제 private Human SDK·native permit·쌍 출력·UI |
| 원래 ingress 수명 | 같은 native Owner·디코딩 전 one-shot admission을 tonic/내부 gateway로 전달하는 구현 진행 | 실제 전송/원천 검사·전체 검증. wire 완료 주장은 아님 |

schema10은 기존 임의 형식 UserId를 유지하며 primary/factor 증명을 소급 생성하지 않는다. 이력은 migration10부터 시작한다. REPLACE까지 막는 realm/ID guard를 추가하고 기존 생성·연결·disable 처리는 유지한다. 실제 Current 검사는 의도적인 특권 realm 변경으로 비교·영구 retirement를 검증했으며 악의적 DB 변경·실행 중 복제 지원 검사는 아니다. 정상 앱 시작의 사전 백업을 유지하며 구버전 바이너리는 schema10을 읽지 못한다. 이번 단계에서 운영 호패 DB를 마이그레이션하지 않았다.

첫 개별 검사 실패는 변형한 GLOB 픽스처의 초기값이 조건을 통과하지 못한 문제였다. 양쪽 조건에서 유효한 상수 realm으로 실제 DDL 검증기까지 도달하게 수정했다. 첫 전체 검사에서는 정확한 테이블 목록에 새 테이블 두 개가 빠진 것이 발견돼 보강했다. 두 실패를 보존한 뒤 최종 전체1125개를 통과했다. assertion·증명 수명·런타임 보안 조건은 약화하지 않았다.

순수 코어의 metadata·숫자 AAL은 호출자가 실제 인증 경계를 지킨 경우에만 평가 입력이 된다. human1 파싱 자체는 신원·권한 증명이 아니다. 사용자별 역할의 AAL과 IP/리소스 조건을 결합하며 AAL3 요구는 초기 Human AAL1/2에서 충족되지 않는다. 오래된 불변 View는 스스로 폐기되지 않으므로 기존 서버의 native View/원천 철회 경계가 필요하다. 빈 Human 맵은 기존 정책 직렬화를 유지하며 새 맵을 게시하기 전 strict 소비자 의존성을 갱신해야 한다.

운영은 한강/콘솔0.3.11·품계0.1.9·호패0.0.10·수문장0.3.6을 유지한다. 이번 소스 변경은 새 Human 동작으로 릴리스·운영 반영하지 않았다. H0 현재 검사는 아직 SQL 기반이다. 인메모리 원천 스냅샷·follower·전체 수명주기/복구/혼합 인증·Human 관리자 브라우저·극단적 성능 실측은 전체 목표에 남아 있다.
