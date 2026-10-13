# ADR 0014: 권한 허용 후 서비스 자격 변환

상태: 제안 설계입니다. projection endpoint·wire format은 아직 구현하지 않았습니다.

구조 prototype은 [요청 schema](../../schemas/projection_request.schema.json),
[가상 요청](../../examples/projection_request.json), [검증기](../../tools/validate_contracts.py)에
있습니다. 요청·결정을 별도의 네이티브 문맥에 결합하고 신원·네트워크·plan·결정 만료 및
1초 한계를 검사하며 소비된 nonce 쌍을 거부합니다. 함께 위조한 subject, 호출자 권한
필드, 범위 변경·오래된 버전·만료 사례를 포함합니다. 실행 가능한 계약 테스트이며 서명
인증·실시간 회수 store·원자적 replay ledger·자격 발급 구현은 아닙니다. 요청 digest는
네이티브 문맥에서 제공하며 canonical hashing과 receipt 인증은 런타임 구현이 필요합니다.
예제의 과거 시각은 실제 자격 lease가 아닙니다.

호패 소스 `1322163`은 digest 기본 함수를 구현했습니다. domain
`hangang-zerotrust:credential-projection:request:v1`과 NUL 뒤에 서비스·대상·method·
정확한 origin-form target·완전한 entity SHA-256을 u32 big-endian 길이와 함께
해시하며 encoding·query 순서를 유지합니다. `ab`, `c`, `GET`, `/private?x=1`, 빈
entity의 네이티브·독립 Python 벡터는
`234488f459d8b3069a74d308d639fa9bfb402b12a9544a413c06c6136a8dab11`로 일치합니다.
테스트 2건·fmt·clippy·경계·문서 검사가 통과했습니다. 라우팅 연결·receipt 인증·발급은
후속이며 현재 배포 동작은 바뀌지 않습니다.

호패 `8b4d0ce`는 소스 단계 Ed25519 receipt 기본 함수를 추가합니다. 146 bytes,
인증/허용 목적 구분, domain을 분리한 정확한 byte 서명, native binding, 발급자가
제공하는 nonce와 최대 1초 lease를 사용합니다. 엄격한 검증은 약한 키·바이트 변조·
다른 키/목적/binding·길이·시각 오류를 거부합니다. 검증 wrapper는 소비자가 직접
생성·복제·직렬화할 수 없습니다. 암호 테스트 2건·fmt·clippy·경계·범위가 정해진 audit·
문서 검사가 통과했습니다. nonce는 네이티브 CSPRNG 발급이 필요하고 수신 키는
authority·purpose별로 제한해야 합니다. chain binding·key registry·시계 rollback
방지·실시간 회수·원자적 nonce 소비·품계 signer 연결·자격 발급은 후속입니다.
상태 없는 서명 확인은 반복 가능하며 replay 방지 구현은 아닙니다.

현재 호패는 auth-proxy 응답으로 검증된 신원을 반환하고 한강은 설정된 응답 header를
복사한 뒤 품계 권한을 판단합니다. 이 경로로 upstream 비밀을 반환하면 권한 확인 전에
자격을 전달하게 됩니다. 현재 접두사 혼합 라우팅은 입력 자격을 풀어 전달하는 기능이며
출력 자격 변환은 아닙니다.

제안 절차는 다음과 같습니다.

1. 호패가 사람·서비스·워크로드를 인증하고 짧은 불투명 인증 receipt를 발급합니다.
   수문장은 버전이 있는 네트워크 근거를 제공합니다.
2. 한강은 네이티브 route·catalog 등급을 확인하고 정확한 신원·서비스·resource·action의
   품계 결정을 요청합니다.
3. 허용 후 인증 receipt와 검증 가능한 품계 결정 receipt로 호패에 변환을 요청합니다.
   guest·거부·오류는 비밀 조회로 진행하지 않습니다. 서명·channel binding은 실행 가능한
   별도 계약으로 구현해야 하며 호출자의 `allowed:true`만 신뢰하지 않습니다.
4. 호패는 신원 신선도·회수·정책·route 버전·대상·승인된 자격 참조·재사용을 확인합니다.
   네이티브 transaction·admission fence가 발급을 소유하고 Lua는 receipt·권한을
   발급하지 못합니다.
5. 한강은 클라이언트 인증 header를 제거하고 결합된 upstream 요청에만 결과를 넣습니다.
   route 변경·redirect·오래된 상태·재검증 실패 시 버립니다. 비밀은 일반 auth 응답,
   브라우저·모듈 RPC·telemetry·결정 cache에 넣지 않습니다.

변환 plan은 검증 신원 header, 대상이 결합된 짧은 JWT, 승인된 bearer 참조, 요청 결합
HMAC, 워크로드 mTLS를 다룹니다. 대상·method·header allowlist·최대 인증등급/권한·
비밀 참조는 네이티브 설정이 고정합니다. 제공자 간 신원 연결은 명시적이며 출력 token이
원래 인증등급을 높이지 않습니다. 품계는 권한, 호패는 신원·발급, 수문장은 네트워크,
한강은 라우팅·집행을 소유하고 공동 다중 writer 업무 schema를 만들지 않습니다.

발급은 신원·네트워크·권한·plan 만료 중 가장 이른 시점으로 제한하며 결정 lease는
최대 1초를 제안합니다. 자격·연결 수명은 별도여서 정책 변경·신원 회수는 해당 stream도
종료해야 합니다. snapshot epoch·membership으로 오래된 replica 발급을 차단하고
signer·provider 장애는 동시성·시간·서킷 제한으로 거부하며 다른 인증으로 우회하지 않습니다.

활성화 전에는 guest·위조 허용의 비밀 조회 차단, receipt 재사용, 대상·method·path
변경, 허용과 발급 사이 회수·버전 변경, 클라이언트 header 제거, Lua의 미승인 URL·key·
인증등급, 다른 대상 redirect·연결 재사용, HMAC upload buffer 초과, signer 장애·취소·
만료를 각각 검증해야 합니다. HMAC streaming은 명시적으로 제한 설계하거나 거부합니다.

receipt schema·암호 검증·별도 네이티브 단계·소유자 게시/회전 API·위임 UI·stream 회수·
전체 스택 10k/100k 성능은 구현해야 합니다. 기존 gates는 기존 계약을 검사하며 이 제안
메커니즘의 완료 증거가 아닙니다.

호패 `535dc57`은 signer/key epoch, 신원 authority epoch, namespace가 결합된 신원/종류/AAL, 신원 revision/자격 generation, 서비스/대상/요청 digest의 canonical binding을 구현합니다. permit은 서명 인증 receipt 해시, decision/resource/action과 품계 authority/catalog/policy/network/route/plan 버전을 추가합니다. 인증은 다른 도메인의 정책·네트워크 상태를 주장하지 않습니다. 테스트 3건에 독립 Python 벡터와 신원 epoch·plan 버전·인증 chain 변경 후 실제 Ed25519 거부를 포함합니다. signing endpoint·검증된 소유자 입력·key registry·원자적 회수/replay는 후속이며 배포된 자격 발급은 아닙니다.

호패 `fc49a8a`는 네이티브 authority·용도·key epoch로 수신 키를 고르고 canonical binding·엄격한 서명을 검사하는 불변 registry를 추가합니다. 메모리 갱신은 제거 floor와 과거 공개 자료 소유권을 보존해 오래된 epoch·부활·회수된 인증 자료의 다른 authority/용도 이동을 거부합니다. 활성 항목 64개·floor 128개·과거 공개 값 256개로 제한하고 조회 시 issuer 문자열을 할당하지 않습니다. 테스트 2건·fmt·clippy·경계·문서 검사가 통과했습니다. 재시작 유지 DB floor·소유자 게시/원자적 활성화·시계/replay/회수·endpoint는 후속이며 새 registry가 없는 이력을 복원하지는 못합니다.

호패 `eac5d78`은 기존 SQLite meta에 공개 registry·제거 floor·자료 이력을 저장하는 네이티브 소유자 persistence를 추가합니다. 게시 시 revision CAS, 쓰기 전·commit 전 호출자 권한 확인, 상태와 참조 전용 감사의 단일 transaction을 사용합니다. load는 제한된 snapshot 관계·신뢰된 최소 revision을 검증하고 일반 재시작에도 제거 fence를 유지합니다. registry/store 테스트 5건은 재시작·오래된 게시·늦은 회수·잘못된 상태·감사 실패 rollback을 다룹니다. 운영 DB·비공개 signer 자료·배포는 변경하지 않았습니다. 원자적 snapshot 설치·endpoint 연결은 후속이며 오래된 DB 전체 복원에는 외부 revision/authority epoch floor가 필요합니다. DB 저장 자체가 복원 신선도나 receipt nonce 소비를 증명하지 않습니다.

호패 `762353c`는 DB 키 소유자를 공유 ArcSwap verifier에 연결합니다. 단일 mutable 소유자가 commit/설치를 직렬화하고 commit 전에 Arc를 준비해 성공 직후 설치합니다. 실패에는 기존 상태를 유지합니다. 검증 결과는 캡처한 registry revision을 가진 non-Clone receipt이며 게시 후 이전 tag의 로컬 pointer 현재 검사를 거부합니다. 서명된 키 제거·공유 reader 갱신·재시작 거부를 포함한 receipt 테스트 11건이 통과했습니다. 라이브러리 연결이며 배포 endpoint 활성화는 아닙니다. 발급은 nonce 소비와 함께 DB revision을 원자적으로 재검사해야 하며 로컬 검사가 이후 race나 분산 membership/follower fence를 대체하지 않습니다.

호패 `96f9d85`는 불투명한 검증 receipt의 소스 단계 원자적 소비 helper를 추가합니다. immediate 소유자 transaction에서 registry revision·네이티브 시각·권한을 다시 확인하고 authority/용도/nonce hash를 한 번 기록하며 관련 DB 작업을 함께 commit합니다. 작업 실패·작업 중 만료는 둘 다 취소합니다. 저장된 clock floor·monotonic 시간 검사는 정리/rollback을 보호하고 정렬된 meta 만료 인덱스는 호출당 최대 128개 쌍을 정리하며 활성 100만 개 한계를 둡니다. receipt 테스트 12건·fmt·clippy·경계·문서 검사가 통과했습니다. callback은 commit 전에 자격·취소 불가능한 네트워크 결과를 노출하면 안 됩니다. endpoint·분산 복원 floor·전체 스택 성능은 후속/미검증이며 운영 상태는 유지합니다.

호패 `6aa88d8`는 독립 SQLite 연결 8개의 동기화 소비에서 한 호출만 commit하고 관련 작업 count도 정확히 1이며 DB 재연결 후 재사용을 거부함을 검증합니다. 마지막 actor 회수는 nonce·작업을 함께 취소하고 이후 허용된 재시도는 성공합니다. receipt 테스트 14건·fmt·clippy·경계·문서 검사가 통과했습니다. transaction 남용 검증이며 활성 발급 endpoint·분산 membership 보장·처리량 benchmark는 아니고 운영은 유지합니다.

Hopae `5a6befb`는 호출자 작업·마지막 권한 검사 후 만료 검사와 commit 직전에 DB registry revision을 재검사합니다. 작업 내부 registry 변경 시 registry·nonce·작업이 함께 rollback되고 정상 재시도는 성공하는 회귀 테스트를 포함해 receipt 테스트 15건 및 fmt/clippy/boundary/docs 검사가 통과했습니다. 자격 endpoint 활성화·분산 검증은 남아 있으며 운영 상태는 유지됩니다.
