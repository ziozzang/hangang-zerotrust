# 네이티브 Human 소스 검증 현황 — 2026-10-16

상태: 검증한 소스 기반이며 **Human 런타임 릴리스·전체 경로 활성화는 아니다**.
[English](../reviews/2026-10-16-human-source-checkpoint.md).

## 로컬 네 코어 첫 실제 성공

소유한 로컬 환경에서 실제 OIDC → 한강 → 호패 Source/SDK → 품계 Human 권한 → 호패 contract4 자격증명 발급 → HTTP 백엔드 흐름이 통과했다. 첫 요청은204이며 백엔드 도착·효과가 정확히1회, 최종 본문 SHA256 `105677b049653381c974d1312bb087650075a48682fc6555274735007afd9c02`와 발급 Bearer가 일치했다. 쿠키·네이티브 신원·호출자 헤더는 백엔드에 전달되지 않았다. 관측한 RPC7개가 각각1회 성공했다. 정리 실패는 없고 기록한 전용 loopback 리스너12개도 종료 후 모두 연결을 거부했다.

사용한 한강은 **아직 릴리즈하지 않은 로컬** 제품 후보 `ada331c4796681cd4cb6da4d9257a0fba2e946d2`(raw SHA256 `1e2e234bc0842b449ee71339e3b1e4a267a191f59031607b1fcc6c9e8a32bfe4`)다. 공개 호패 `e1dd972`·품계 `98ecfcd`·수문장 런타임 원천 `d6fc1de`, 실제 공개 SDK 신원 조회 도구와 소유한 raw 중계기를 함께 사용했다. 안전한 결과 파일의 SHA256은 `ae92869c9cc32aba2b726ee06b2f7c1a4e35b8a5b59559291d26d0a5c850ed80`이다. 실행 중 자격증명·쿠키·증명 페이로드는 이 기록에 포함하지 않는다.

앞선 실패로 한강의 두 결함을 구분했다. Human 원천 발급에 신뢰된 라우트 문맥이 없었고, 권한 서명 검증 입력에서 AAL0을 고정했다. 후보는 실제 선택한 런타임에서 Human 문맥을 생성해 클라이언트·정적 설정 헤더 뒤에 적용하고, 검증한 실제 AAL1/2를 서명 입력에 유지한다. 머신의 AAL0 제약은 유지한다. 이전 픽스처 실패와 정리 결과도 별도로 보존했다.

새 전용 DB를 사용하는 실제 AAL1 HTTP 성공1건의 근거다. AAL2·다른 프로바이더·A/B 치환·재사용·진행 중 회수·최종 전송 철회·분산 스냅샷·처리량·브라우저 관리·릴리즈 검증·운영 마이그레이션까지 완료한 것은 아니다. 후속 검사와 전체 후보 검증을 계속하며 운영 버전은 바꾸지 않았다.

## 최신 공개: 네이티브 Human 쌍 projection

[호패 e1dd9728e184eb4975fbe1ce8dae0505571f4ff1](https://github.com/ziozzang/hopae/tree/e1dd9728e184eb4975fbe1ce8dae0505571f4ff1)에 contract4 Human 쌍 projection을 공개했다. 실제 네이티브 Source·receiver clock을 공유하고 품계 permit을 독립 조회하며 두 증명을 클래스 공통 canonical ledger에서 소비한다. RPC·네이티브 SQL·출력 준비 이후에도 디코딩 전 원래 요청 예산을 유지하고 commit 직전 callback 없는 current·취소 검사를 수행한다. 선택 Human 메타데이터를 만들 수 없는 기존 신원은 일반 Verify를 유지하되 Human 발급은 거부한다. Store 오류는 계속 거부한다.

정확한 최종 소스에서 native71개 통과·5개 제외, 실제 SDK/품계 쌍 재사용 검사1개 통과, strict workspace Clippy·fmt·diff 검사를 통과했다. 앞선 전체1208개·SDK69개 결과는 이후 호환성·테스트 수정 전 후보의 결과다. 실제 쌍 검사는 네이티브 OIDC/TOTP·실제 호패 RPC/SDK·실제 품계 프로세스를 사용하지만 네트워크·route는 인증된 픽스처다. 실제 네 컴포넌트 HTTP/backend 흐름까지 입증한 것은 아니다.

다음 단계는 품계 SDK 고정 갱신과 한강 최종 Human 전송 연결이다. 새 런타임 릴리즈·운영 schema 마이그레이션·Human 활성화는 아직 하지 않았다. 아래 내용은 이전 기반 체크포인트를 보존한다.

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


## 네이티브 Human 권한·관리자 후속 검증

공개 품계 `f6fb7d9a7e92b615d3c2525999b55a66e7a491ac`는 선택적으로
Human observed permit Issue/Observe와 메타데이터 전용 TTL 0 resource 판정을
제공한다. 공개 호패 SDK `b08e105`를 고정하고 observation의 정확한 scope
fingerprint를 검사한다. Human 전용 할당·AAL1/2·네트워크 제한·현재 정책
publication·설정 route/plan을 함께 요구하며 기존 user 할당이나 API context
템플릿으로 대체하지 않는다. 전체 feature workspace 150개 통과·외부 fixture
명시적 제외 1개이며 엄격한 Clippy/fmt도 통과했다.

실제 호패 production 바이너리·공개 opaque SDK·SQLite를 쓰는 실제 품계
바이너리로 OIDC, 소유한 LDAPS, 필수 StartTLS를 각각 실행해 통과했다.
primary 로그인/handoff·TOTP AAL2·독립 observation·소비형 refresh·권한
발급·충족할 수 없는 AAL3·정책 회수/복구·원래 증명 예산이 남아 있는 상태의
logout 거부를 확인했다. 네트워크·route·plan peer는 인증된 프로토콜 fixture다.
이는 인증→권한 구간의 검증이며 paired credential projection·한강 backend
전달·실제 4종 서버 전체·K8s·스냅샷 복제·처리량 검증이 아니다. 실제 호패
바이너리 소스는 `b08e105`이며 버전 문자열만으로 이 소스를 식별할 수 없다.

공개 호패 `769ae4b4fecb996f38cbae17f96d8453cfd205b7`의 인증된 관리자
사용자 응답과 읽기 전용 콘솔 패키지에 실제 증명과 같은 canonical Human
정책 식별자를 제공한다. 최대 200개 계정을 한 번의 제한된 쿼리로 조회하고,
지원하지 않는 기존 ID는 좌표 없이 계속 표시한다. issuer·Store realm은
설정과 실제 데이터에서 가져오며 관리자 query로 받지 않는다. 이 메타데이터는
인증 증명이나 권한 부여가 아니다. 최종 전체 workspace 1,193개 통과·명시적
제외 45개이며 엄격한 Clippy/fmt와 브라우저 검증도 통과했다. 콘솔 패키지
소스는 0.1.7이며 운영 설치는 아직 하지 않았다.

재현 가능한 [소유 런타임 fixture](../../tools/test-support/native-human-runtime/README.ko.md)를
공개했다. 증명 행이나 capability를 조작하지 않고 실제 네이티브 인증을
수행한다. 비공개 IPC의 원자적 publication 테스트 3개와 저장소 validator의
schema 예제 7개·공격/개인정보 사례 42개가 통과했다. 생성한 키·쿠키·준비
파일·비공개 런타임 증거는 공개 소스에 포함하지 않았다.

이전에 관측한 Workload 최초 Issue 거부의 역사적 원인은 여전히 미확정이다.
별도 결정적 실험에서 소유 Kubernetes verifier의 준비 파일 생성→쓰기
사이 경합과 원자적 publication 보강 효과를 입증했지만, 당시 포트 바이트를
수집하지 않았으므로 그 장애의 확정 원인으로 표현하지 않는다. 이 후속
소스 검증은 운영 릴리즈나 DB 마이그레이션을 의미하지 않는다.
