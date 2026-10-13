# 구현 과제

[English](TODO.md) · [구현 순서](docs/ko/ROADMAP.md)

주 작업: 운영 Hangang 콘솔의 실제 Guard 메뉴, 플러그인 권한/회수/감사 검증,
Hopae 관리 위임과 사용자/세션/이벤트 메뉴, HTTP 의미와 같은 고속 verify 프로토콜,
Hangang 네이티브 로그인·로그아웃, 호환 컴포넌트 검증·릴리즈입니다. Hangang/Guard는 서명 자산, Hopae는 체크섬 자산을 게시했습니다.

Hangang 통합 권한과 명시적 계정 매핑을 통한 SSO 로그인은 [ADR 0009](docs/ko/ADR_0009.md)에 기록했습니다.

설계 서브태스크: 전체 구조·소유권 도표와 영어/한국어 문서, 카탈로그·분류·통합 판단·exporter 제안을 구성했습니다.
등급·테넌트/객체 증거·하향 승인, 프로토콜과 위임/회수 보장, 실제 엔진/exporter 구현은 남아 있습니다.
단말/워크로드는 환경 조사 후 ADR로 결정합니다. 문서가 작성되었다고 런타임 구현을 완료 처리하지 않습니다.

## 온톨로지 및 자동 보안 강화
- [x] Sillok/Jikji 선택과 펜테스트→Guard→Hangang 대응 설계 기록.
- [ ] Sillok 버전·작업량 제한 어댑터, 출처·테넌트 격리.
- [ ] Jikji 자동·반자동 도구/승인 통합.
- [ ] 제한된 펜테스트 작업과 취약점 근거 계약.
- [ ] Guard 대응·Hangang 라우팅 패치 CAS/멱등 어댑터.
- [ ] 영속 복구·카나리 검증·충돌 안전 롤백.
- [ ] 공격적 검증과 일반 요청 성능 격리.

## 관측 / 온톨로지 / 펜테스트 피드백
- [x] 관측→대응→검증→재사용 루프 영어·한국어 설계 기록.
- [ ] 제한된 로그/트레이스/메트릭·펜테스트 근거의 출처 기반 상관 분석.
- [ ] Sillok 사실/가설/정책/적용 상태/결과 구분과 근거 철회.
- [ ] Jikji case 수명주기·근거 검색·제한된 결과 재사용.
- [ ] 사전 기준에 따른 적용 후 재펜테스트·정상 트래픽 회귀 검증.
- [ ] 피드백 증폭·허위 성공·테넌트 혼합 공격적 검증.

- [x] Hearim 지능·판단 백엔드 선정 및 다이어그램 갱신.
- [ ] 제한된 Jikji/Hearim 어댑터·출처·장애 처리·보정 검증.

## 통합 구현 근거 — 2026-10-12

Hangang/Hopae/Guard PR #1을 모두 머지했습니다. Native 메뉴·host 인증·위임 및 HOP1 지속 연결을 구현하고
기존 provider/session/grant/CSRF/fence를 유지합니다. 영어 TODO에 테스트 수와 근거를 기록했습니다.
운영 콘솔 활성화·플랫폼 릴리즈 검증·Hopae 전체 처리량 측정은 별도 완료 항목입니다.

- [x] 운영 HTTPS 두 메뉴·익명 거부·네이티브 진입 리다이렉트·로그아웃 정리·Guard 서명 updater 확인.
- [x] 네이티브 플랫폼 검증·게시 완료: Hangang 5개, Guard 4개, Hopae 4개 대상.

2026-10-13 게시·배포: [Hangang v0.3.1](https://github.com/ziozzang/hangang/releases/tag/v0.3.1), [Guard v0.3.1](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.1), [Hopae v0.0.2](https://github.com/ziozzang/hopae/releases/tag/v0.0.2). 배포 전 Hangang/Guard 서명과 Hopae 체크섬을 검증했습니다. Guard 감독형 서명 자동 업데이트는 활성화했습니다. Hopae 서명 자동 updater는 구현하지 않았습니다.

- [ ] Hopae 전체 세션 처리량 측정; 전송 검증을 100k QPS 근거로 사용하지 않음.

## 통합 콘솔·SSO 근거 — 2026-10-13

[Hangang #4](https://github.com/ziozzang/hangang/pull/4)와
[Hopae #2](https://github.com/ziozzang/hopae/pull/2)를 머지했습니다. 검토·테스트한 Linux
빌드와 고정 Hopae UI 0.1.2를 운영에 적용했습니다. 기존 릴리즈 이후 기능 배포이며,
새 크로스플랫폼 서명 릴리즈를 게시한 것은 아닙니다. 현재 단일 Hopae 관리자를 기존
활성 Hangang 관리자에 명시적으로 연결했으며 계정/grant를 생성·변경하지 않았습니다.

Hangang 관리자 API 89개·private lease/native SSO·실제 broker 검증,
Hopae unit 384개·시나리오 359개(명시적 제외 40개), strict Clippy·문서/경계/게시 검사,
브라우저 버튼 위치·복귀·viewer 역할/복구·플러그인 권한 검증을 통과했습니다.
운영 HTTPS에서 ID/PW+SSO 버튼, Hangang 로그인만으로 Hopae 상태/사용자 조회,
추가 로그인 제거, 로그아웃 정리, 익명/origin/쿠키/lease 우회 거부,
네이티브 provider 진입 리다이렉트를 확인했습니다. 실제 Google 로그인은 운영자의
프로바이더 인증 동작이 필요하며 자동 로그인 검증에는 소유한 mock provider/session을 사용합니다.

## 품계 / 수문장 통합

- [x] 이름과 소유권 확정 ([ADR 0010](docs/ko/0010-pumgye-ownership.md)).
- [x] 제한된 내장 품계 컴파일러 및 공격적 검증.
- [x] Hangang 정책 게시·감사·콘솔 권한 매트릭스.
- [x] 보호 라우트의 호패 신원·사용자/IP 권한·수문장 집행 결합.
- [x] 캐시·철회·전송·브라우저 검증 및 검토된 배포.
- [x] 장부·기존 사초·실록의 분리된 설계 책임 기록.

- [x] 사헌을 별도 감사 시스템으로 기록. 런타임 통합은 설계 단계.

## 수문장 실행 파일 전환

- [x] 기본 `sumunjang` 실행 파일·버전 및 기존 실행 파일/서명 자산 호환성.
- [x] 워크스페이스·패키징·Clippy·실 서명 업그레이드/롤백 검증.
- [x] 서명 검증한 Linux 운영 반영 및 콘솔/SSO 회귀 검증.
- [x] 네 플랫폼 검증·공개 v0.3.2 릴리즈·운영 GitHub 업데이트 확인.

## 호패 인증 게이트웨이

- [x] 다중 인증·네트워크 근거 방향 기록(ADR 0011).
- [ ] 공통 주체/근거/커넥터 계약 및 기존 다중 OIDC 유지.
- [ ] LDAP·API 릴레이 및 제한된 자격 증명 변환.
- [ ] any/all/step-up·네트워크 주체·품계 주체 종류 집행.
- [ ] 네이티브/HTTP 동등성·통합 관리·장애/철회/보안 검증·배포.

## 독립 분산 런타임

- [x] 호패·수문장·품계 독립 서버 소유권 확정(ADR 0012).
- [ ] 독립 품계 권한·지속 저장/CAS·판단 서버.
- [ ] 원격 인증 HOP1/HGD1/품계 전송 및 범위 제한 관리 위임.
- [ ] 복제 리비전/만료/철회·서킷/노드 전환 검증.
- [ ] 세 실 프로세스 통합과 지속/종단간 처리량 검증.

### 수문장 저장소 이전 검증 (2026-10-13)

- [x] 공개 공식 저장소 [ziozzang/sumunjang](https://github.com/ziozzang/sumunjang)으로 이전하고 Git 원격·Hangang/품계 의존성·문서 주소를 정렬했습니다.
- [x] [v0.3.3](https://github.com/ziozzang/sumunjang/releases/tag/v0.3.3): 네 네이티브 플랫폼이 [CI](https://github.com/ziozzang/sumunjang/actions/runs/38326599970)를 통과했습니다. 공개 자산 22개의 해시가 원본과 일치하고 Ed25519 manifest 8개를 독립적으로 검증했습니다.
- [x] 이전된 저장소에서 받은 실제 v0.3.2 manifest·바이너리의 기존 서명 URL·고정 공개키·크기·해시를 검증했습니다. 다른 저장소·태그·파일명은 테스트에서 거부합니다.
- [x] 공개 Linux 바이너리 서명 검증 후 설치했습니다. 새 저장소의 감독형 updater는 활성화/up_to_date(v0.3.3)이며 통합 콘솔과 인증된 HGD1 회귀 검증이 통과했습니다.

v0.3.2 이하 바이너리는 고정된 구 GitHub API의 리다이렉트를 거부하므로 서명을 검증한 v0.3.3으로 최초 전환 설치가 필요합니다. [이전 안내](https://github.com/ziozzang/sumunjang/blob/main/docs/ko/UPDATES.md)를 참조하세요. 이 검증은 위의 인증 게이트웨이·독립 원격 런타임 작업 완료를 의미하지 않습니다.

## 스냅샷 백본과 스케일아웃 멤버십

- [x] 메모리 스냅샷·도메인 DB 백본·합류/드레인/제거 계약과 Hangang 구독 의무를 기록했습니다(ADR 0013).
- [ ] 호패·수문장·품계의 인증된 snapshot/outbox 어댑터, 보호된 검증 인덱스와 세션/토큰 회수.
- [ ] lease 멤버십 authority, Hangang watch/재동기화·제한된 풀·incarnation/리비전 fencing·드레인.
- [ ] 실제 복제본 증감·partition·통지 유실·오래된 근거·세션/네트워크/역할 회수와 지속 전체 경로 스케일아웃 검증.

## 독립 품계 검증·내부 배포 — 2026-10-13

[Pumgye #1](https://github.com/ziozzang/pumgye/pull/1)에서 순수 권한 코어·제한된 PPG1 codec·지속 mTLS client·독립 SQLite 소유 서버를 분리했습니다. [Pumgye #2](https://github.com/ziozzang/pumgye/pull/2)는 실제 Hangang/품계 두 프로세스 검증을 추가했습니다. [Hangang #7](https://github.com/ziozzang/hangang/pull/7)은 머지되었으며 원격 네이티브 판단·소유 서버의 정책/상태/감사 위임·권한 범위 CAS·정책 변경/서버 장애 시 스트림 종료를 구현합니다. 이 회귀 검증에서 호패/수문장의 근거는 소유한 프로토콜 fixture이며 실제 컴포넌트 서버는 아닙니다.

독립 품계 서버를 내부에 배포했습니다. mTLS 필수, 판단/관리 자격 분리, 초기 서비스 매트릭스 비어 있음, 정책 revision 1입니다. 배포된 PPG1에서 미등록 서비스 거부와 클라이언트 인증서 없는 연결 거부를 확인했습니다. 사용자/서비스 권한은 부여하지 않았습니다. Hangang 0.3.2 CLI·OpenAPI 검증을 통과했습니다. 로컬 정적 빌드의 프록시 10건·UDP 수명주기·감독형 재시작·Lua syscall 격리·실제 Hangang/품계 mTLS 회귀 검증도 통과했습니다. 기존 고정 신뢰 키로 서명하고 OpenSSL로 별도 검증한 바이너리와 새 콘솔을 내부 게이트웨이에 배포했습니다. 실제 HTTPS에서 독립 정책/상태/감사 조회·세 메뉴·기존 ID/PW 및 호패 SSO 진입·익명/origin 거부·로그아웃 정리를 설정 변경 없이 확인했습니다. 0.3.2 크로스플랫폼 릴리즈 게시는 남아 있습니다. 비용에 관한 사용자 요청에 따라 GitHub Actions는 비활성 상태로 유지합니다.

복제 서버 membership·분산 snapshot·호패 전체 인증 게이트웨이 connector 구현은 남아 있습니다. 이번 배포를 해당 보장이나 전체 스택 100k QPS의 근거로 사용하지 않습니다.

## 호패 원격 전송·내부 dogfooding — 2026-10-13

호패 main에 제한된 OIDC origin 서킷과 인증된 원격 mTLS HOP1 리스너를 반영했습니다. Hangang main에는 명시적인 CA/서버 이름/클라이언트 인증서 검증·고정 주소 지속 HOP1 풀·동일 전송을 사용하는 콘솔 SSO를 반영했습니다. 로컬 정적 바이너리의 실제 Hangang/호패 프로세스에서 익명 로그인 리다이렉트·클라이언트 인증서 없는 연결 거부·잘못된 서버 신원 거부/설정 복구·위조 신원 격리·호패 장애 시 503을 검증했습니다. 이 fixture는 외부 인증 성공이나 인증 처리량의 근거가 아닙니다. 기존 네이티브 세션 시나리오는 유지된 mTLS 연결에서 세션 회수를 검증합니다.

검증된 Linux 빌드를 내부 배포하고 기존 호패 네이티브 경로 11개와 콘솔 SSO를 독립 호패 CA의 mTLS로 전환했습니다. 기존 provider 설정·신원 매핑·grant·서비스 권한은 유지했습니다. 실제 HTTPS 브라우저에서 SSO 진입·통합 호패/품계/수문장 메뉴·역할/origin 격리·로그아웃 정리를 통과했습니다. 배포 스크립트의 null 라우트 처리 실패는 롤백 후 수정하여 적용했습니다. 일관된 SQLite 백업·롤백 파일은 비공개로 유지합니다. 기존 릴리즈 이후 기능 배포이며 새 크로스플랫폼 공개 릴리즈는 아닙니다. Hangang Actions는 비활성 상태이고 통합 머지는 CI 비용을 생략했습니다. LDAP/자체/API/네트워크 connector·자격 변환·원격 수문장 전송·분산 및 세션 메모리 검증은 남아 있습니다.

## 수문장 네이티브 mTLS 내부 배포 — 2026-10-13

수문장 main에서 0.3.4를 준비했습니다. 클라이언트 인증서 필수 원격 HGD1 리스너·collector 인증·ALPN·핸드셰이크/연결 수명 제한·부분 프레임 전체 기한을 구현했습니다. Hangang main의 지속 Guard 풀에는 고정 주소·명시적 CA/이름/클라이언트 인증서 검증을 추가했습니다. 실제 두 프로세스의 로컬 빌드로 허용·수동 IP 차단/해제 즉시 반영·잘못된 이름 거부/복구·장애 시 거부를 통과했습니다. 워크스페이스 테스트·엄격한 Clippy·Hangang 라이브러리/콘솔/CLI 테스트도 통과했습니다.

고정 키 서명/해시를 검증한 수문장 0.3.4 GNU·Hangang 정적 바이너리를 내부 설치하고 독립 수문장 CA의 mTLS 네이티브 질의 연결을 적용했습니다. 기존 observe 정책·collector/admin 자격 정보·provider/유저/서비스 할당은 유지했습니다. 실제 HTTPS에서 세 메뉴·품계 조회·호패 SSO 진입·로그아웃을 확인했습니다. 배포된 HGD1 핸드셰이크/질의의 인증서/이름 검증을 통과했고 클라이언트 인증서 없는 연결을 거부했습니다. 일관된 DB 백업과 롤백 자료는 비공개입니다.

공개 크로스플랫폼 0.3.4 자산은 아직 게시하지 않았습니다. 감독형 updater는 활성 상태이며 내부 설치 0.3.4를 더 낮은 공개 0.3.3으로 내리지 않고 현재 이를 거부합니다. 전체 인증 connector/변환/수명주기·전체 처리량 검증은 남아 있고 네이티브 전송 테스트를 전체 스택 100k QPS 근거로 사용하지 않습니다.

## 서비스 API 권한·내부 dogfooding — 2026-10-13

호패 main에 인메모리 SHA-256 index·IPv4/IPv6 prefix tree의 서비스 범위 API 인증을 추가했습니다. 환경변수 참조·realm·host/port audience·제한된 만료를 명시적으로 설정합니다. credential이 없을 때만 설정에 따라 기존 세션 엔진을 사용할 수 있고, 제시한 credential이 잘못되면 유효한 브라우저 세션으로 전환하지 않습니다. 서비스 신원은 사람 신원과 분리하고 AAL 0과 인증 서비스 audience를 전달합니다. Hangang main은 강제되는 품계 게이트·정확한 audience·명시적인 subject 권한·메서드/등급/network 조건·명시적으로 AAL 0을 허용한 역할을 요구합니다. 정책/변환 전에 credential을 소비하고 upstream 직전에 다시 제거합니다.

실제 debug 및 로컬 정적 바이너리의 mTLS HOP1/PPG1 세 프로세스 fixture에서 영속 권한 회수/복원·Guest 거부·network/등급/사람 assurance 요구 거부·서비스 범위 격리·품계 장애 시 거부를 통과했습니다. 이 fixture에 수문장은 포함하지 않습니다. 기존 신원/서비스/grant를 유지한 채 생성한 서비스 전용 프로브 credential 하나와 읽기 전용 품계 권한으로 내부 배포했습니다. 네이티브 TLS ingress에서 실제 서비스 인증·미등록/잘못된/위조 신원/메서드 거부·upstream Authorization 제거를 통과했습니다. 브라우저에서 서비스 매트릭스·통합 모듈 메뉴·기존 SSO·로그아웃 정리도 검증했습니다.

내부 프로브에는 명시적인 named HTTPS listener 범위가 필요합니다. network 정책은 지정된 사설망과 루프백만 허용하고 이 범위 밖의 공인 DNS hairpin 요청은 의도적으로 거부합니다. 일관된 백업·credential·재사용 가능한 비공개 검증은 공개 저장소 밖에 둡니다. 새 공개 크로스플랫폼 릴리즈는 아닙니다. 현재 파일 소유 API profile 변경에는 재시작이 필요합니다. DB 게시·관리·credential 회전/변환·스트리밍 credential 회수·LDAP/자체 비밀번호/원격 API 릴레이·전체 처리량 검증은 남아 있습니다.


## 외부 API 검증 릴레이 — 2026-10-13

호패 main에 프로필별로 선택하는 고정 endpoint API 검증 커넥터를 추가했습니다. 제시된 bearer credential과 서비스/IP 문맥을 설정된 검증 서버로 전달하고, 응답의 audience·서비스 신원·절대 만료를 검증하여 서비스 전용 AAL 0 근거를 발급합니다. redirect·환경 proxy·URL credential/query·기본 사설망 접근을 거부합니다. 응답 크기·기한·프로필 동시성을 제한하며 취소와 전송/의미 오류는 프로세스 로컬 circuit에 반영합니다. 잘못된 credential은 401, 검증 서버 장애·열린 circuit은 503이며 세션/로컬 키로 우회하지 않습니다.

전체 target 테스트(라이브러리 395·기타 통합 15·시나리오 363 통과, 명시적 ignored 시나리오 40), 엄격한 Clippy·format·문서·경계·시나리오 매핑 검사를 통과했습니다. Cargo audit에 미처리 취약점은 없고 기존 rustls-pemfile 유지보수 중단 경고는 남아 있습니다. 실제 debug·정적 호패/Hangang/품계 fixture로 로컬 키 및 외부 검증 경로, 권한 범위·회수/복원·credential 소비·circuit 호출 억제를 검증했습니다. 검증 서버 fixture는 소유한 루프백 환경이며 실제 외부 provider 또는 전체 처리량을 증명하지 않습니다.

정적 릴레이 지원 호패 바이너리를 일관된 비공개 백업과 이전 이미지 복구 경로를 갖추어 내부 배포했습니다. 기존 설정은 유지했고 실제 서비스 권한·네이티브 전송·통합 모듈/매트릭스 조회·SSO 진입·로그아웃 격리를 통과했습니다. 내부 프로브는 로컬 키 프로필을 계속 사용하며 외부 검증 활성화는 선택 사항입니다. 공개 다중 플랫폼 릴리즈·표준 introspection adapter·upstream credential 교환·LDAP/자체 사람 인증·DB 소유 profile 게시·전체 수명주기/처리량 검증은 남았습니다. 이 커넥터의 별도 독립 적대적 검토 산출물은 아직 기록하지 않았으며 자동 gate만으로 전체 인증 게이트웨이 완성을 주장하지 않습니다.


## 영속 인증 프로필·콘솔 게시 — 2026-10-13

호패는 참조 전용 인증 프로필을 자체 DB에 최초 한 번 가져온 뒤 revision ArcSwap
스냅샷으로 읽습니다. 원래 파일이 있어도 삭제가 재시작 후 유지됩니다. 게시 전에
컴파일하고 트랜잭션 내부 및 commit 직전 관리자 fence·revision CAS를 검증하며
상태/감사를 함께 commit한 뒤 await 없이 스냅샷을 설치합니다. 전용 blocking worker
permit은 호출자 취소 후에도 조회/게시 작업을 제한합니다. 비밀 참조 및 사설/verifier
credential endpoint 바인딩에는 운영자 선언이 필요합니다. HTTP/HOP1은 스냅샷
하나를 사용하며 삭제된 bearer 프로필은 브라우저 세션으로 우회하지 않습니다.

콘솔 패키지 0.1.3·정적 Linux 바이너리를 내부 배포했습니다. 실제 Hangang 브라우저로
프로필을 조회하고 서명 broker에서 동일 설정을 게시하여 프로필 revision 증가와
라우팅 revision/설정·기존 grant 유지를 확인했습니다. 익명 거부·로그아웃 정리·API
인증·권한 매트릭스·전체 모듈 메뉴·네이티브 전송·기존 SSO 회귀 검사를 통과했습니다.
소유한 프로세스 재시작·트랜잭션 롤백 검사도 통과했습니다. 전체 target gate는
라이브러리 400·기타 통합 15·시나리오 365건 통과, ignored 40건이며 기존 PEM parser
유지보수 중단 경고는 남아 있습니다. 일관된 백업·이미지/패키지 복구 자료는 비공개입니다.

upstream credential 변환·LDAP/자체 사람 인증·근거 조합·열린 stream credential
회수·분산 follower/membership·전체 처리량·공개 다중 플랫폼 릴리즈는 아직 남았습니다.
파일 중심 preflight/비밀 참조 이전과 connector circuit 상태 유지도 후속 작업입니다.


## LDAP 직접 로그인 소스 연결 — 2026-10-13

호패에 TLS 전용 LDAP 커넥터·분리된 서비스/사용자 bind·텍스트/바이너리 불변 subject
namespace·직접 인증 결과 출처 검증·프로세스 로컬 circuit·제한된 비밀번호 제출을
구현했습니다. 소유한 OpenLDAP fixture는 LDAPS·필수 StartTLS 및 upgrade 실패 후
평문 bind 미전송을 검증합니다. LDAP는 schema v4·스냅샷·registry에서 OIDC와
분리되며 일반/재인증 선택기에 포함됩니다. portal은 바인딩 form을 준비하고 POST에
HTTPS·Origin/CSRF·고유한 제한 필드·시도 admission을 요구합니다. 실제 store에서
challenge·자격 실패·AAL 1 세션/handoff·replay·provider 비활성/브라우저 바인딩 거부를
검사합니다. email/MFA의 암시적 승격은 허용하지 않습니다.

현재 전체 target gate는 라이브러리 421·기타 통합 15·시나리오 366건 통과입니다.
LDAP fixture 1건·시나리오 40건은 명시적 ignored이며 디렉토리 fixture는 별도 검증합니다.
기존 PEM parser 유지보수 중단 경고는 남았습니다. 소스는 호패 main에 있지만 운영
LDAP 설정 활성화는 제한하고 내부 배포는 이전 기능 이미지/schema를 유지합니다.
v4 운영 업그레이드 복구에는 일관된 v3 DB 백업이 필요합니다.

활성화 전 실제 디렉토리 브라우저/gateway 검증·엄격한 BER 응답 제한·commit 시
커넥터 설정/epoch fence·계정/분산 admission·디렉토리 세션 회수를 완료해야 합니다.
자체 비밀번호·인증 변환/조합·인메모리 세션/분산 follower·전체 스택 10k/100k 처리량·
공개 다중 플랫폼 릴리즈도 남아 있습니다. 이 소스/검사 결과가 전체 목표의 완성은 아닙니다.

## 내부 배포와 도그푸딩 완료 기준 — 2026-10-13

완료한 런타임 변경은 소스 테스트·공개 반영에 더해 내부 배포와 도그푸딩을
필수로 수행합니다. 비공개 일관성 백업, 버전 아티팩트, 마이그레이션을 고려한
롤백, 실제 Hangang 요청·관리자 검증을 사용합니다. 공개 증거에 자격증명을
포함하지 않습니다. 운영자 의도에 따라 GitHub Actions는 비활성 상태를 유지하고
검증·릴리즈 빌드는 로컬에서 수행합니다.

현재 내부 Hangang·호패·품계·수문장을 다시 검증했습니다. HTTPS 서비스 인증,
메서드 권한 거부, guest·잘못된 자격·위조 신원 거부, 업스트림 자격증명 제거,
세 관리 메뉴, 매트릭스 조회, SSO 진입, 로그아웃·익명·Origin 격리,
인증된 네이티브 HGD1이 통과했습니다. 세 user service도 active입니다.
이 검증은 라우팅·정책을 변경하지 않았습니다. Hangang 이미지는
`0.3.2-service-api-647c93b`, 호패는 `0.0.2-profile-console-9b307c0`이며,
이후 LDAP 소스는 아직 배포·활성화되지 않았습니다.

- [ ] schema-v3 백업과 검증된 schema-v4 복원 롤백을 갖춰 다음 호패 스냅샷을
  검증·배포하고 서비스·관리자 회귀 검증을 반복합니다.
- [ ] 실제 LDAP 브라우저·게이트웨이·회수 검증, BER 크기 상한, commit fencing을
  완료한 뒤 내부 디렉터리 인증을 활성화합니다.
- [ ] 내부 도그푸딩을 지속하고 장애·복구·지연·메모리·처리량을 기록한 뒤
  운영 완성과 공개 성능 목표 달성 여부를 판단합니다.

## 필수 2차 인증·확장 작업 — 2026-10-13

- [ ] Google Authenticator 호환 네이티브 TOTP: 등록 확인, 사용자별 seed 암호화,
  복구·해제, 시도 제한, 프로세스 간 원자 counter 재사용 방지·시계 역행 방어.
- [ ] 서비스별 step-up과 브라우저·user·audience에 묶인 single-use challenge,
  코어의 보증 수준·세션·stream 회수, Hangang 통합 관리.
- [ ] 인증된 binding 응답, 고정 egress·deadline·서킷을 갖춘 외부 인증·요인 API
  adapter. 필수 요인 장애에서 우회하지 않음.
- [ ] CPU·메모리·시간 상한, 승인 host 호출, 감사·revision 배포를 갖춘 선택적
  Lua capability 확장. Script의 세션 발급·AAL 선택은 금지.
- [ ] 알고리즘·호환성·수명주기·동시성·장애·sandbox·내부 도그푸딩 검증.
  현재는 설계 요구사항이며 이미 구현된 MFA로 취급하지 않음.

영문·한국어 계약은 호패 main의 `docs/AUTH_GATEWAY.md`에 기록했습니다.
LDAP 중첩 BER 검사·악성 TLS peer는 소스에서 검증했지만 내부 활성화와 전체
인증 게이트웨이 완성은 아직 남아 있습니다.
