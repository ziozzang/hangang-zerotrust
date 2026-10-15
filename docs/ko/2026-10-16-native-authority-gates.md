# 네이티브 Human 소유권과 Kubernetes API 소스 검증 — 2026-10-16

[English](../reviews/2026-10-16-native-authority-gates.md)

검토를 마친 **공개 소스** 변경이다. 운영 한강0.3.10·호패0.0.10·품계0.1.8을 교체하거나 Kubernetes authorizer를 활성화한 것은 아니다.

| 모듈 | 병합 소스 | 검증 |
|---|---|---|
| 호패 | `1fb5db3ba2eaa107b44a0159a0b08cecd341a9d6` | 1,080 통과·기존42 제외, strict Clippy·독립 검토 |
| 한강 | `d422c1cb8af5799d143abc4db450e6a2ce27c4c9` | 1,321 통과·기존58 제외, 브라우저45개·strict Clippy·독립 검토 |
| 품계 | `b184bdd2bbbfd8879deb7359724f430ad003e951` | 기본126·전체135 통과·실패/제외0, 양쪽 strict Clippy·독립 검토 |

## 구현 경계

호패는 실제 DB provider 행·소유 세대·설정 세대를 같은 읽기 트랜잭션에서 준비하고, 같은 행으로 OIDC/LDAP 어댑터를 컴파일해 정확한 애플리케이션 원천과 묶는다. 실제 사용 가능한 어댑터만 인정한다. 원천 변경·ABA·다른 Store/Registry 사용은 거부하며 일반 인증 동작은 유지한다. 실제 SQLite 대기 중 다른 검사가 같은 fence를 철회하는 테스트로 마지막 retirement 검사 누락을 재현하고 최종 Acquire 검사로 수정했다. 수정 전 실패도 보존한다. Human 세션 권한·외부 디렉터리 실시간 상태·인메모리 인증 고속화 완료는 아니다.

한강은 새 품계 정책 컨텍스트와 매핑·카탈로그를 보존한다. API 서비스 생성·AAL0 기본값·typed k8sapi 할당, 잘못된 네트워크/워크로드 할당 거부·raw 초안 보존을 추가했다. API 전용 정책은 일반 HTTP 라우트 설정 검증에서 거부한다. 브라우저는 소유한 mock API와 컴파일 UI 검사이며 운영 API-server 검사는 아니다. 실제 고정 코어로 정책 round-trip·일반 라우트 거부를 검증했다.

품계는 기본 비활성화된 실제 SAR 리스너를 구현했다. 고정 클러스터·검증 mTLS·정확한 client leaf 해시·요청별 전용 bearer를 요구한다. 제한된 HTTP/1 드라이버가 TLS 연결을 재사용하고 같은 네이티브 뷰의 매핑·권한과 원래 BOOTTIME 수명을 검사한다. TLS 아래 쓰기 경계를 검사하며 응답 전체 flush까지 기존 owner를 유지한다. 입력을 반사하지 않고 미확인·원천 불가 판정은 명시적 Deny로 응답한다.

실제 로컬 TLS·별도 main 프로세스에서 같은 연결의 native 정책 CAS Allow→Deny→Allow, ALPN 없는 HTTP/1을 검증했다. plaintext 수락 뒤 TLS flush를 Pending으로 고정하고 다음 요청을 큐에 둔 상태에서 철회·종료·취소해 추가 raw 전송0·다음 판정 미실행을 확인했다. scalar/vectored/flush/shutdown·영구 철회·태스크 취소도 검사했다. 커널이 이미 수락한 바이트나 Kubernetes에서 이미 허용된 효과를 되돌린다는 보장은 아니다. 제어된 원천 만료 테스트는 native capture 경계이며 실제 소켓의 source-expiry 테스트는 아니다.

## 다음 필수 검증

- 실제 로그인·factor·Engine Allow에서 정확한 handle/session/user/provider/factor/application 원천과 원래 요청 수명을 묶고 Human RPC/SDK·품계·한강 집행으로 연결한다. 현재 세션 입력에는 최종 body/header digest가 없어 향후 실제 wire binding을 빈 body로 가정해서는 안 된다.
- 기존 observed-authentication 기능을 보존한 릴리즈 후보를 만든다. 품계 default-feature 전용 빌드는 현재 관측 permit RPC가 없어 운영 교체에 쓰면 안 된다.
- 검증한 이미지의 격리 API-server/etcd와 일반 사용자를 사용해 캐시 명시적 비활성화·failurePolicy Deny를 검증한다. 기존 주 authorizer는 수정하지 않는다. 초기에는 품계 DB 원천으로 RBAC import/webhook 순환 의존을 피한다. 클러스터 변경 전에 재확인·cold/off-host 백업하고 소유한 UID만 정리한다.
- 정확한 static 산출물·통합 콘솔·실제 API-server 검증 뒤 서명·공개·내부 반영한다. H2·헤더 파서 최적화·처리량·분산 메모리 원천/복제·수명주기/복구와 전체 원래 목표는 계속 진행한다.

비공개 근거 manifest는 `/tmp/hopae-human-provider-registry-evidence.json`, `/tmp/hangang-kubernetes-api-console-evidence.json`, `/tmp/pumgye-sar-listener-evidence.json`이다. 키·운영 설정·실제 계정은 공개 문서에 넣지 않았다.

## 후보 및 실제 클러스터 검증 현황

Hangang `0b15bfb7f7d199b6b653cd5de567ccc667df7055`는0.3.11 버전 후보다. 전체1,321 통과/58 기존 ignored 및 strict 검사를 유지하고 musl 정적 실행파일8종을 동결했다. 새 정확한 gateway의 실제 로컬 TLS HSTS HTTP/1(16), HTTP/2(4), Sacho 가시성(24) 검사도 통과했다. 품계0.1.9 runtime 소스는 `5817ee4dc7023c91f43a73909d38406c974caa96`, 패키징 전용 후속 소스는 `5e47fc2e122596d490d1edbacd0b6d5bed35c8ee`이다. 운영 observed-authentication 기능을 유지하고 동결 raw의 실제 로컬 CLI/mTLS/연결 재사용/CAS 검사와 패키징9개 검사를 통과했다. 아직 두 후보를 서명·공개·운영 반영하지 않았다.

실제 클러스터 작업 전에 새 콜드 백업의 원격·오프호스트 전체 SHA/크기/tar 검증을 통과했다. 원래 Pod12개 UID/단계(11 Running, 기존 Failed debugger1개)와 노드2개 Ready를 보존했다. Echo/Ingress HTTPS200 및 비로그인 Headlamp401도 정상이다. 복원 리허설이나 여러 물리 호스트 장애 검증은 아니다.

두 노드에 정확한 이미지를 적재한 뒤 네 컴포넌트 Any/Service 결합·Kubernetes 네이티브 수문장 원천·관리자 브라우저 검사가 종료0으로 완료됐다. mTLS, 읽기 전용 제어, 한국어/영어, 소유 정책 CAS/회수, 오래된 관리자 충돌, 실제 Pod 교체, 원천 RBAC 회수/삭제/UID 교체와 거부 시 백엔드 미전달·인증된 복구를 확인했다. 기존 assertion/시간 제한은 유지했다. 근거는 `/tmp/world-0311-019-any-browser-run1.log` 및 기준선 기록이다.

별도 Workload 실행은 **실패**했다. 실제 공개 SDK 발급/관측/UID 검사 직후 첫 미인가 HTTP 응답 읽기에서3초 timeout이 났다. 권한 부여/permit/output/replay 단계에는 도달하지 않았다. 품계 초기 재시작은 관측했으나 종료 사유를 남기지 못했으며 tap 초기 연결 실패만으로 HTTP 원인을 단정할 수 없다. 해당 timeout 요청의 백엔드 효과0을 주장하지 않는다. 정리·원래 Pod/노드 기준선은 통과했다. 실패를 보존하고 제한된 Pod/이전 로그 진단을 보강하며 증거/HTTP 예산을 늘리거나 Any 통과를 Workload 검증으로 대체하지 않는다.

첫 별도 API-server 실행도 권한 assertion 전에 **실패**했다. 공식 바이너리의 파일 capability가 dropALL 경계에서 실행 EPERM을 일으켰고 같은 조건의 로컬 실행으로 재현했다. 포트 포워딩도 Pod Running 전에 시작했다. 후속 `1ff01bc7e77ca2ced63cbcae31b378c207eacec4`는 원래10초를 공유하는 시작/포워딩 순서와, 공식 바이너리 바이트는 그대로 두고 빌드 시 파일 capability만 제거하는 고정된 파생 이미지를 지원한다. nonroot/dropALL/권한 상승 금지와 기존 메인 authorizer는 유지한다. 로컬21개 검사는 통과했으나 파생 이미지의 실제 권한 검증은 별도 필수 게이트다. 이 실패들을 근거로 릴리즈·운영 반영하지 않는다.
