# Hangang 0.3.10 최종 보안 후보 검증 — 2026-10-15

[English](../reviews/2026-10-15-hangang-0310-final-security-qualification.md)

공개 Hangang **v0.3.10**의 대상 원문은
`e3fdd60ef5fc3066994dbb5d2c179b31200a1b56`이다. 공개와 **백업을 갖춘 gateway/console 운영 채택이 완료**됐다. 이전 f45·보류97의 결과를 최종 산출물의 근거로
대체하지 않는다. 이 기록은 [이전 native 검증과 실패 이력](2026-10-15-workload-native-qualification.md)에
최종 보안·동일 후보 K3s 근거를 추가하며 전체 혼합 신원/provider 목표 완료를 뜻하지 않는다.

## 정확한 소스·공개 산출물 경계

최종 소스는 workspace **1,320개 통과·기존 58개 제외**, strict 전체 target/feature
Clippy·fmt를 통과했다. production Linux amd64 musl 실행 파일 8개를 정적 빌드했다.
Gateway 원문 SHA-256은 다음과 같다.

`900f91cb49b5b424807bd44296a5c2a126292b2fdbd39c3772db2c6a91720efd`

공개 파일 5개는 gateway 원문·Ed25519 update manifest·공개 키·archive·checksum
목록이다. archive에는 실행 파일 8개가 있지만 gateway manifest가 각 helper를 개별
서명하는 것은 아니다. staged signed 원문을 위 digest로 검증했다. 공개만으로 운영
배포나 특정 route 활성화를 입증하지 않는다.

비공개 근거는 `/tmp/hangang-sacho-http2-final-source-checks.json`, frozen
`/tmp/hangang-sacho-http2-artifacts-e3fdd60/PROVENANCE.json`,
`/tmp/hangang-0310-signed-e3fdd60`와 `.verified.json`이다. 키·자격·설정 본문·실제
사용자를 이 문서에 복사하지 않는다.

## 실제 컴파일된 TLS·애플리케이션 검사

동일하게 동결한 helper로 f45에서 먼저 RED를 보존했다. 정상 TLS 상태는 통과했지만
잘못된 trusted forwarding의400에 HSTS가 없었다. 보류97은 HTTP/1 **16/16**을
통과했으나 실제 HTTP/2 `h2`, Host 없는 `:authority`와 invalid XFF에서
400·HSTS 누락·origin0이 재현됐다. 이는 최종 통과로 바꾸지 않은 실패 근거다.

정확한 최종 e3 바이너리는 OpenSSL SAN 인증서·명시적 사설 CA·실제 인증서/호스트
검증으로 HTTP/1 **16/16**, HTTP/2 **4/4**를 통과했다. TLS 검증 우회는 없다.
선택한 두 테스트 host의200/401/403/404/502에 정확한 HSTS 하나가 있고, 잘못된
forwarding400에도 origin 호출 없이 HSTS가 있었다. 비선택 host와 위조 XFP의
평문 요청에는 HSTS가 없었다. 실제 ALPN `h2`에서 authority-only 정상 요청,
invalid XFF400의 HSTS, 비선택 authority404와 Host 충돌400의 HSTS 부재를 각각
확인했다. 클라이언트 URI/forwarded claim을 TLS나 다른 도메인 정책의 권위로 쓰지
않았다. 도메인 정책은 계속 명시적 opt-in이며 전체 fleet 적용을 뜻하지 않는다.

별도 실제 Sacho+Hangang loopback 검사는 공개/비공개·인증 계정/그룹·위조 신원
헤더 조합 **24개**를 통과했다. status/history/incidents/page는 Sacho 소유 이메일
membership을 사용하고 위조 groups를 권한 근거로 쓰지 않았다. 고정된 로컬 fixture
검증이며 실제 운영 route나 모든 계정·그룹을 검증했다는 뜻은 아니다.

비공개 근거는 `/tmp/sacho-compiled-hsts-e3-green.json`,
`/tmp/sacho-compiled-hsts-h2-e3-green.json`과 대응 로그,
`/tmp/sacho-e3-isolated-regression.log`와 비공개 result이다. 이전 f45/97 RED는
별도로 보존했다.

## 정확한 e3의 실제 K3s 검사

두 실제 실행 모두 exit0이었다. 동일 runtime 원문은 다음과 같다.

| 컴포넌트 | 원문 |
|---|---|
| Hangang | `e3fdd60ef5fc3066994dbb5d2c179b31200a1b56` |
| Hopae | `848dc83540e1eb722ddd7e8d8820b07e11fa9d76` |
| Pumgye | `adaf985042b7af7b6aecc48cf34a02661abd4644` |
| Sumunjang | `d6fc1dec893df963c30f483ddf755421a98920b4` |

Workload 실행은 실제 공개 SDK의 bound ServiceAccount/Pod subject(kind3/AAL0),
전용 `workload_users`, 사전 resource metadata, 품계 permit, contract3 paired
projection과 최종 backend credential을 검증했다. 기존 users grant를 빌리지 않았다.
audience/claim/고정 owner/realm 거부, reviewer role 회수, 실제 profile CAS·readback·
복원, Hop 교체, Pod UID 교체 후 새 grant와 ServiceAccount 회수를 검사했다. 같은
pair 재사용은 최초 응답 전 거부했고 전후 native auth/permit owner 검사와 backend
정확히1회가 유지됐다. 평탄화된 거부 상태만으로 특정 SQL row의 인과를 입증하지 않는다.

재시작 후 보유하던 옛 proof 거부는 원래1초 만료로도 설명되므로 재시작만의 인과를
분리하지 못했다. 실제 TokenReview 회수 전파는 Pod 약40.53초·ServiceAccount
약10.77초였으며 원래 최대1초인 source evidence 기한과 별개다. 복원 중
HTTP503/backend0 이후 HTTP200/backend1을 관측했지만 요청별 예산은 늘리지
않았다. 실행 중 Pod attestation은 문제 없이 성공했으며 선택된 imageID/Pod 필드
관측이다. 그 자체가 기능 grant나 독립된 process/config-ID 검증은 아니다.

별도 **Service Any** 실행은 native Sum 정책 원천, 고정 로컬 키/HTTPS verifier
slot과 명시적 검증 신원 관계를 사용했다. 실제 issue·독립 Observe·소비 refresh,
누락/실패/모호한 factor 거부, 비밀 격리, 실제 relay outage/circuit 유지, 권위 회수와
교체를 통과했다. 별도 origin bearer만 물질화됐다. Service/AAL0 경계이며
Human MFA나 Human/Workload 혼합 구성이 아니다.

같은 실행에서 **실제 컴파일된 host와 설치된 package**의 EN/KO 전환 시 draft/DOM
보존·추가 owner 요청 없음, host 메뉴 순서·품계 하위 주소3개·Back/Forward,
미설치 목적지 거부,390px panel/form/table 경계와 키보드 스크롤, 원천 소유 read-only
제어, stale admin CAS 충돌/profile 회수, mTLS 위임과 실제 정책 변경을 통과했다.
원천 RBAC 회수·checkpoint/authority 교체·삭제/UID 교체·명시적 repin도 새 인증
상태에서만 복구됐으며 거부에는 무단 backend 효과가 없었다.

로그에는 소유 namespace 및 정확히 생성한 global resource/CRD UID 정리가 남아
있다. synthetic Retain PV는 의도적으로 남는다. 노드2개는 하나의 물리 호스트를
공유하므로 실제 기능 검증이지 다중 호스트 HA·처리량 인증이 아니다. 보존한 cold/
off-host backup은 복원 훈련의 근거가 아니다.

비공개 근거는 `/tmp/workload-world-e3-run1.log`, 실행 중 attestation·pair/held
receipt, `/tmp/hangang-0310-e3-any-browser.log`, 준비된 명령·capability/image import
자료다. 최초 `NOT RUN`/미검증 표기가 있는 준비 문서를 완료 증명으로 다시 쓰지
않았다. 실행 근거는 terminal exit0과 완료 로그다. 비공개 설정은 공개 문서에 옮기지 않는다.

## 운영 채택과 최종 읽기 전용 확인

같은 최종 e3 원문과 gateway digest로 gateway·console rollout이 각각 exit0과
성공 receipt를 남겼다. Gateway는 비공개 설정/SQL/image rollback backup과 설정된
drain을 사용했고 라우팅 설정·자격/UID/network 경계를 유지했다. 최초 gateway
preflight의 권한 오류는 변경 전에 발생했다. 실패를 보존하고 바이너리 바이트 변경
없이 실행 권한을 정정한 재실행이 통과했다. 초기 실행 중 rollout script가 보완됐으므로
동결된 실행 script checksum을 검증했다는 주장은 하지 않는다.

채택 후 실제 인증서 검증 TLS 확인 **16개**가 두 설정 host에서 통과했다.
HTTP/1·HTTP/2의200/401/404, 잘못된 forwarding400의 HSTS, 평문 HTTP308의
HSTS 부재를 확인했다. 관측한 운영 HSTS 경계이며 모든 변형이나 미래 설정의 보장은 아니다.

최종 읽기 전용 K3s baseline도 통과했다. 두 노드 Ready·기존 Pod12개의 UID 유지,
추가 Pod·소유 테스트 namespace·테스트 CRD 없음과 기존 HTTP probe 결과를 확인했다.
Any browser의 추가 evidence 디렉터리는 비어 있으므로 완료 로그가 근거이며
screenshot·trace를 주장하지 않는다. Synthetic Retain volume은 유지한다.

비공개 근거는 `/tmp/hangang-0310-gateway-rollout-success.json`,
`/tmp/hangang-0310-console-rollout-success.json`,
`/tmp/sacho-post0310-live-verification.json`,
`/tmp/hangang-0310-e3-post-k3s-baseline.json`이다. 비공개 backup 경로·운영 설정·
자격 본문은 공개하지 않는다.

## 보존한 불명확성·남은 목표

이전 All browser의 Sum plugin child 누락 실패는 최초 안전한 mount 관측이 부족해
원인이 불명이다. 이후 All 진단 재실행·최종 e3 Any 통과로 원인을 설명하거나 첫
실패를 통과로 바꾸지 않는다. 이전 Workload의 ConfigMap과 영속 profile 소유 상태
불일치 실패도 남고 올바른 CAS/readback의 별도 통과 근거가 있다.

Standalone console SSO·모든 admin/error/locale/in-flight 상태·실제 Google 사용자
상호작용·Human observed/MFA 전체 체인·자체 계정/복구·Human/Workload 혼합 구성·
장기 stream 회수·inbound Kubernetes webhook·외부 DBMS adapter·clone/rollback/
fleet fencing·실측 처리량은 별도다. 공개 provider owner 소스와 미commit TOTP
선행 구현이 검증한848 runtime에 포함된 것으로 해석하지 않는다. 원래 전체 목표의
완료를 주장하지 않는다.
