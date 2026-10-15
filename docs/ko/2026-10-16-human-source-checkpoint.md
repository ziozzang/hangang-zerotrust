# 네이티브 Human 소스 검증 현황 — 2026-10-16

상태: 검증한 소스 기반이며 **Human 런타임 릴리스·전체 경로 활성화는 아니다**.
[English](../reviews/2026-10-16-human-source-checkpoint.md).

| 요구 | 현재 근거 | 남은 작업 |
| --- | --- | --- |
| 실제 인증 원천 | 호패87d19a0 H0 및 후속b317120398d95c2f87f08069ced1c5b6a395ba5a | 실제 품계 권한·쌍 projection·Root 최종 집행 |
| 최종 요청 바인딩 | 호패eefc358·독립 v2 벡터, SDK 기본60/native62·바인딩9·strict Clippy | 실제 요청·Human 원천·최종 전송 연결 |
| 영구 계정 namespace | 호패b317120: schema10 불변 공개 realm·ID 영구 예약·같은 Current 트랜잭션 join. 전체1125/0/43·strict Clippy/fmt·실제 소유 LDAP LDAPS/필수 StartTLS·OIDC/TOTP/CLI 재시작 통과 | 운영 schema 마이그레이션·전체 Human 체인. 실제 human1 도출은 아래 후속 소스에 포함 |
| typed Human 정책 | 품계9c3d69aee4f0691fe166a49c382be8e8aaa0620d: 독립 human_users·같은 컴파일러·AAL1/2·fallback 금지·IP/수문장/등급 교집합·API context/template 금지. 기본133/전체142·양쪽 strict Clippy/fmt | native permit·쌍 출력·운영 Human 관리자. 소스 매트릭스 UI는 아래 후속에 포함 |
| 원래 ingress 수명·실제 Human 증명 | 호패 `b08e105666de99f2ae957cff16ca9f3c75d3f7c5`: 공유 native Owner·디코딩 전 one-shot admission·실제 Source/RPC·scope를 검증하는 opaque SDK | 품계 네이티브 사람 권한·쌍 projection·Root 최종 전송 |

schema10은 기존 임의 형식 UserId를 유지하며 primary/factor 증명을 소급 생성하지 않는다. 이력은 migration10부터 시작한다. REPLACE까지 막는 realm/ID guard를 추가하고 기존 생성·연결·disable 처리는 유지한다. 실제 Current 검사는 의도적인 특권 realm 변경으로 비교·영구 retirement를 검증했으며 악의적 DB 변경·실행 중 복제 지원 검사는 아니다. 정상 앱 시작의 사전 백업을 유지하며 구버전 바이너리는 schema10을 읽지 못한다. 이번 단계에서 운영 호패 DB를 마이그레이션하지 않았다.

첫 개별 검사 실패는 변형한 GLOB 픽스처의 초기값이 조건을 통과하지 못한 문제였다. 양쪽 조건에서 유효한 상수 realm으로 실제 DDL 검증기까지 도달하게 수정했다. 첫 전체 검사에서는 정확한 테이블 목록에 새 테이블 두 개가 빠진 것이 발견돼 보강했다. 두 실패를 보존한 뒤 최종 전체1125개를 통과했다. assertion·증명 수명·런타임 보안 조건은 약화하지 않았다.

순수 코어의 metadata·숫자 AAL은 호출자가 실제 인증 경계를 지킨 경우에만 평가 입력이 된다. human1 파싱 자체는 신원·권한 증명이 아니다. 사용자별 역할의 AAL과 IP/리소스 조건을 결합하며 AAL3 요구는 초기 Human AAL1/2에서 충족되지 않는다. 오래된 불변 View는 스스로 폐기되지 않으므로 기존 서버의 native View/원천 철회 경계가 필요하다. 빈 Human 맵은 기존 정책 직렬화를 유지하며 새 맵을 게시하기 전 strict 소비자 의존성을 갱신해야 한다.

운영은 한강/콘솔0.3.11·품계0.1.9·호패0.0.10·수문장0.3.6을 유지한다. 이번 소스 변경은 새 Human 동작으로 릴리스·운영 반영하지 않았다. H0 현재 검사는 아직 SQL 기반이다. 인메모리 원천 스냅샷·follower·전체 수명주기/복구/혼합 인증·Human 관리자 브라우저·극단적 성능 실측은 전체 목표에 남아 있다.


## 실제 Human Source/RPC/SDK 후속 검증

호패 공개 main `b08e105666de99f2ae957cff16ca9f3c75d3f7c5`에 실제 네이티브 원천과
선택적 인증 Human RPC를 반영했다. SDK는 준비된 실제 요청 바이트를 해싱하며 RPC에는
제한된 메타데이터를 전달한다. 본문 업로드 프로토콜은 아니다. 독립 관측은 정확한
원천 record와 설정 scope fingerprint를 요구한다. 다른 앱·라우트·목적지·헤더 정책은
거부하고 갱신 중 scope를 바꿀 수 없다. 일반 UTC 검증으로 canonical observed Human
증명을 허용하지 않는다.

원래 질의 admission과 보유 인증 record는 동일한 마지막 네이티브 원천 시각을 쓴다.
질의는 admission 잔여시간만 줄이며 증명을 연장하거나 replay 보존을 단축하지 않는다.
잘못된 owner/domain·시간 역전·만료·거부 후 복구 금지를 실제 네이티브 테스트로 확인했다.
나중 증명은 살아 있지만 오래된 질의가 마지막 시각에서 만료되는 10개 경계도 검사했다.

워크스페이스 전체 1,190개를 통과했고 45개는 제외했다. 기존 gateway layer 41개와
소유 LDAP 테스트 4개다. 이후 타입 별칭·동일 테스트 모듈 위치·포맷만 바꾸고 SDK
기본69/native75·RPC 개별5·caller1·strict workspace Clippy/fmt를 통과했다. 검증 mTLS와
실제 OIDC·소유 LDAP LDAPS/필수 StartTLS로 세션/TOTP → Source → 공개 SDK 발급·독립
관측·갱신·로그아웃을 검사했다. Human 권한/projection/Root 전체 체인 근거는 아니다.
이전 실패도 보존했다. Service 양성 fixture 3개에는 실제 앱 선언이 없어 fixture만
수정했으며 issuer 검사를 약화하지 않았다. 이전 Workload Issue 거부 1건의 원인은
이후 동일 격리 검사와 전체 검사 통과만으로 입증되지 않아 미확정으로 유지한다.

한강 공개 main `67f481d`에는 별도 사람 권한 매트릭스와 품계 의존성 4종의 검증 코어
`9c3d69a` pin을 반영했다. 전체 1,322개(기존 제외58)·strict Clippy/fmt·관련 Chromium
52개를 통과했고 마지막 안내 문구 변경 후 관련 11개도 통과했다. 이는 메타데이터 관리다.
비어 있지 않은 `human_users`를 게시하기 전에 소유 품계 서버와 엄격한 리더를 갱신해야
한다. 운영 바이너리·DB 스키마를 바꾸거나 observed Human 라우트를 활성화하지 않았다.
