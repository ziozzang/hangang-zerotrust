# ADR 0014: 권한 허용 후 서비스 자격 변환

상태: 런타임 통합 제안입니다. 호패에 receipt 암호·키 소유권·증명 쌍 원자 승인 소스가
있지만 projection endpoint는 아직 활성화하지 않았습니다.

구조 prototype은 [요청 schema](../../schemas/projection_request.schema.json),
[가상 요청](../../examples/projection_request.json), [검증기](../../tools/validate_contracts.py)에
있습니다. 요청·결정을 별도의 네이티브 문맥에 결합하고 신원·네트워크·plan·결정 만료 및
1초 한계를 검사하며 소비된 nonce 쌍을 거부합니다. 함께 위조한 subject, 호출자 권한
필드, 범위 변경·오래된 버전·만료 사례를 포함합니다. 실행 가능한 계약 테스트이며 서명
인증·실시간 회수 store·원자적 replay ledger·자격 발급 구현은 아닙니다. 요청 digest는
네이티브 문맥에서 제공하며 canonical hashing·receipt 인증의 호패 라이브러리 구현은
아래에 기록합니다. 네이티브 요청·endpoint 통합은 남아 있습니다.
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

Hopae `21dba4c`는 인증된 자격 변환 증명 쌍 승인을 추가합니다. 용도별로 검증한 두 receipt의 네이티브 신원 epoch·subject/종류/AAL·신원 revision/자격 generation·서비스/대상/요청 digest가 일치하고 permit은 서명을 포함한 전체 인증 receipt의 SHA-256과 결합해야 합니다. 비공개·Clone 불가능한 승인 객체는 두 nonce와 소유자 작업을 하나의 SQLite transaction에서 소비합니다. 두 번째 nonce 재사용·어느 receipt든 만료되면 첫 소비와 작업까지 취소합니다. 새 공격 테스트 4건은 정상 서명된 문맥 불일치·chain hash 변경·더 빠른 인증 만료·두 번째 nonce 거부 시 rollback·독립 연결 8개에서 정확히 한 전체 commit을 확인합니다. 인증 gateway 테스트 총 44건과 fmt/clippy/경계/문서 검사가 통과했습니다. 실시간 신원/정책/네트워크/plan 소유권은 네이티브 guard가 검사해야 하며 소스 승인 단계이지 자격 발급·endpoint 활성화·분산 검증·처리량 보장이 아닙니다.

Hopae `849d5e1`는 고정 신원 헤더·bearer 참조용 네이티브 변환 소스 코어를 추가합니다. 서비스/대상별 중복 없는 최대 128개 plan에 자원/행위·최소 AAL·자격 참조를 고정합니다. 승인 문맥은 서명된 권한 범위·plan 버전·두 receipt의 공통 유효 구간을 보존합니다. plan 불일치는 자격 조회 전에 거부하며 첫 권한 검사 뒤 증명 쌍 transaction에서 제한된 네이티브 동기 로컬 조회를 실행합니다. 잘못된 토큰은 거부하고 마지막 회수/만료/registry 검사 실패 시 두 nonce를 rollback하고 폐기 출력은 zeroize합니다. Clone/Debug/직렬화 불가능한 출력은 결합된 서비스/대상/요청·시각에만 sensitive 고정 헤더로 변환됩니다. 새 테스트 5건과 인증 gateway 총 49건 및 fmt/clippy/경계/문서 검사가 통과했습니다. endpoint·일반 auth 응답의 자격 전달을 활성화하지 않습니다. 관리자 게시·네이티브 signing/전송·발급 audit/outbox·Hangang 최종 집행/stream 회수·JWT/HMAC/mTLS·분산/전체 스택 성능 검증은 남아 있으며 운영 상태는 유지됩니다.

Hopae `5baa048`는 참조 전용 자격 변환 plan의 영속 소유자를 추가합니다. revision CAS·digest·비활성 tombstone·게시 audit을 함께 commit하고 쓰기 전/commit 전 관리자 검사 및 마지막 문서 byte 검사를 적용합니다. 컴파일된 Arc는 commit 전에 준비해 성공 직후 공유 reader에 설치합니다. 이전 reader는 증명 쌍 승인 전후 cached statement와 빌린 row byte로 현재 DB 문서를 정확히 비교하므로 요청 경로에서 JSON decode·plan 컴파일·문서 할당을 하지 않습니다. DB 비활성/교체 후 오래된 snapshot은 거부하고 재활성화에는 새 버전으로 서명된 permit이 필요합니다. 새 테스트 5건과 인증 gateway 총 54건 및 fmt/clippy/경계/문서 검사가 통과했습니다. 시작/readiness·위임 관리자 endpoint/UI·발급 audit/outbox·전송 통합은 남아 있으며 DB를 사용하는 승인은 분산 membership·목표 처리량 증명이 아닙니다. 운영 상태는 유지합니다.

Hopae `e61a347`는 애플리케이션 시작과 보호된 관리자 경로에 plan 소유자를 연결합니다. 참조 전용 시작 선언은 서비스/대상/자원/행위·자격 방식/참조·최소 AAL을 제한하며 DB 소유자 row가 없을 때만 버전 1 bootstrap을 가져옵니다. 저장된 활성 상태도 선언 범위에 들어야 하고 tombstone은 재시작 후 비활성을 유지합니다. 보호된 GET/PUT·서명 Hangang 조회/게시 변환은 네이티브 역할/CSRF/replay/마지막 관리자 검사를 재사용합니다. 실제 HTTP 프로세스로 viewer/CSRF 거부·필수 버전·미선언 capability·오래된 쓰기·재시작 후 비활성/재활성화를 검증하고 위임 테스트에서 replay·네이티브 grant 회수를 확인합니다. 전체 target 테스트 898건 통과·42건 제외, fmt/clippy/경계/문서/시나리오 커버리지도 통과했습니다. 의존성 감사는 기존 검증 전용 RSA 예외·rustls-pemfile 유지보수 중단 경고 아래 통과했습니다. 소스의 plan 관리 연결이며 변환 전송/issuer endpoint·upstream 자격 전달 활성화는 아닙니다. Hangang 모듈 UI·signer/key 관리·발급 audit/outbox·집행/stream 회수·분산/성능 검증은 남아 있습니다. 공개 불변 릴리스 자산과 운영 이미지는 유지합니다.

Hopae `1319351`는 콘솔 패키지 0.1.5에 자격 변환 관리 탭을 추가합니다. 범위/AAL/참조를 텍스트로 요약하고 viewer 편집 금지·충돌 시 내용 보존·다음 설정 버전 자동 부여·명시적 null 비활성화를 제공합니다. manifest GET/게시 capability와 asset hash를 pin합니다. 실제 Chromium 영문 관리자/한국어 viewer에서 악성 텍스트·JSON 오류 거부·충돌 보존·게시/비활성화·기존 프로필 회귀를 검증합니다. 내부 dogfooding은 해당 정적 소스 이미지·pin된 패키지를 사용합니다. 최적화 DB 복사본 bootstrap/readback·HTTP/pooled mTLS·Chromium MFA/TOTP, 운영 API/매트릭스/모듈/SSO/네이티브 회귀와 실제 운영 Hangang 프로필/자격 변환 탭이 통과했습니다. 기존 운영 설정/키를 보존하고 변환은 미설정/비활성입니다. 운영 브라우저는 게시 없이 소유자 문서/버전을 유지하며 정지 상태의 일관된 소유자/위임 DB 백업·이전 이미지·registry 백업을 보존합니다. Rust 소스는 898건 통과·42건 제외로 검증한 갱신과 동일합니다. 관리자 UI/런타임 통합은 내부에서 검증했으며 네이티브 receipt 발급/전송·최종 upstream 집행/stream 회수·발급 audit/outbox·분산/전체 스택 성능 검증은 남아 있습니다. 불변 태그 릴리스 자산은 유지합니다.

Hopae `1f486ea`는 human 검증 엔진 출력을 인증 receipt 발급 소스에 연결합니다. 비공개·Clone/serde 불가능한 seal로 원래 서비스/user/session/provider/인증 시각/만료/AAL/generation·검증 시각을 결합해 공개 필드를 바꾼 신원은 서명하지 못합니다. 인증 전용 signer에 공개 자료/issuer/key/신원 epoch·최대 128개 서비스/대상 쌍을 고정합니다. 네이티브 clock/RNG·작업 전후 소유자 검사·검증 후 1초/신원 만료 한계·monotonic 작업 시간·프로세스 clock watermark로 발급을 검사합니다. 컴파일된 scope key를 빌려 조회하고 출력은 불변 metadata를 Arc로 공유합니다. 실제 SQLite 엔진 시나리오로 서명을 확인하고 신원/서비스 변경·미선언 대상·잘못된 pin·마지막 거절·작업 중 만료·시계 역행을 거부합니다. 전체 target gates 899건 통과·42건 제외 후 마지막 metadata 공유 개선의 발급 시나리오·전체 target 정적 검사도 통과했습니다. 문서/시나리오 커버리지·기존 예외/경고 아래 의존성 감사도 통과합니다. 기존 gateway wire 동작·운영 이미지는 유지합니다. 네이티브 adapter는 정확한 요청 문맥을 가져오고 경로별 인증 수준/실시간 소유자를 재검사해야 합니다. 영속 signer/key 게시·재시작/분산 floor·service/workload 발급·RPC 활성화·전체 집행/성능 검증은 남아 있으며 인증 서명은 권한 허용이 아닙니다.

Hopae `ec1ed5d`는 프로필 소유 서비스 인증 receipt를 추가합니다. 비공개·Clone/serde 불가능한 proof에 key/relay 검증 후 네이티브 소유자 버전을 담고 Service/AAL0·설정된 서비스/대상·evidence/검증 만료 한계로 발급합니다. 프로필 버전을 신원/자격 generation·서비스 전용 epoch에 사용하고 기존 gateway와 canonical subject hash를 공유해 자체/relay namespace를 유지합니다. 테스트 3건은 서명·만료·namespace·거짓 MFA 거부·범위/종류 거부·회수/마지막 guard/시계 역행을 검증하며 workload/network 발급은 미지원입니다. 실시간 guard는 프로필/key/app/경로/네트워크를 검사하고 자료 교체 시 프로필 generation도 갱신해야 합니다. 일반 인증에서 발견한 race도 수정합니다. 공유 atomic 게시 fence가 DB 게시부터 준비된 snapshot 설치까지를 보호하고 원격 검증 후 gateway가 캡처/현재 Arc 동일성을 검사합니다. 게시 실패는 이전 availability를 복원합니다. 제어된 HTTP/네이티브 테스트에서 대기 중인 verifier의 프로필을 회수해 사용자 헤더 없는 503을 요구합니다. 전체 네이티브 gates 904건 통과·42건 제외, 정적/문서/시나리오 검사·기존 예외/경고 아래 감사도 통과했습니다. receipt RPC·영속 signing/key 관리·분산 floor·전체 집행/성능 검증은 남아 있으며 회수 수정은 기존 서비스 인증에도 독립적으로 적용합니다.

내부 반영 갱신(2026-10-14): `0.0.3-service-fence-ec1ed5d` 이미지가 스키마 v6로 운영 중입니다. 설정·키를 보존했고, 중지 상태의 owner/delegation 백업과 이전 이미지가 남아 있습니다. 사설 DB 복사본의 최적화 mixed-auth/Lua/MFA/TOTP 검증 및 실제 콘솔·네이티브 smoke가 통과했습니다. 네이티브 검증 904 통과·42 제외이며 기존 범위 제한 RSA 예외와 rustls-pemfile 경고가 있습니다. 운영 프로필은 native-only, projection은 비활성이고 receipt 발급 RPC는 아직 활성화하지 않았습니다. 회수 경합 테스트를 위해 운영 자격증명을 회수하지 않았습니다.

## 실제 네이티브 게이트웨이 스냅샷 경계 — 2026-10-15

한강 `8430198`은 네이티브 요청 lease에 실제 활성 스냅샷을 보존합니다. 공개 설정
번호뿐 아니라 Arc 동일성으로 인증·본문 준비·원천 RPC·최종 upstream 진입·보호된
본문을 검사하며 같은 리비전의 새 스냅샷도 이전 요청을 중단합니다. SQL·설정
직렬화는 필요하지 않습니다. 기존 네이티브 리비전 검사와 마찬가지로 무관한
스냅샷 교체도 보수적으로 요청을 중단합니다.

같은 리비전 교체·준비된 본문 거부 테스트를 추가했습니다. 전체 1,284개 통과,
기존 명시적 제외 58개·엄격한 Clippy·로컬 문서 링크 922개 검사를 통과했습니다.
실제 네 프로세스 mTLS gRPC 네이티브 검사에서도 최종 경로/본문·신뢰/본문 예산
거부·영속 권한/프로필 회수·원천 장애 시 거부 요청의 backend 미전달을 확인했습니다.
소스는 main에 반영했으며 현재 운영 릴리스는 0.3.5입니다.

이것은 로컬 라우팅 소유자 검사입니다. 원격 route 관측 endpoint·서명 route claim·
permit RPC·투영 활성화·replay 소비를 추가하지 않습니다. 후속 통합에서도 실제
스냅샷 소유권을 유지해야 합니다.

## 요청별 네이티브 라우팅 참조 — 2026-10-15

한강 `2a4a95a`는 원천 관측 전에 실제 준비된 네이티브 요청을 등록하고 최종
upstream 진입에서 참조를 재검사합니다. 포착 시 스냅샷에 구축한 인덱스로 실제
route 소속과 컴파일된 scope를 확인합니다. 참조는 스냅샷 동일성·최종 절대 URI·
메서드·준비된 digest를 묶고 1초 뒤 만료되며 소유자 Drop/취소 시 제거됩니다.
새 레지스트리는 이전 참조를 조회할 수 없습니다. 전역 128개·잠금 shard 16개로
제한하고 스냅샷 메타데이터를 공유하며 본문/자격 필드를 복제하거나 SQL을 읽지
않습니다.

테스트 5개가 대상/query/메서드/digest 변경·다른 binding·같은 리비전 교체·실제
태스크 취소·만료·재시작 격리·동시 수용량 회수를 검사합니다. 전체 1,289개 통과/
기존 명시적 제외 58개·엄격한 Clippy·문서 링크 922개와 실제 네이티브/호환 네 서버
mTLS gRPC 영속 재시작 검사를 통과했습니다. 소스/로컬 검증이며 새 정적 릴리스나
K8s 적용을 주장하지 않습니다. 별도 콜드 백업 오프호스트 사본은 전송을 마치고
양쪽 전체 파일 해시가 일치합니다.

원격 route 조회에는 필수 mTLS·별도 판정 역할 인증·제한된 디코딩/deadline·설정된
소유자 주소와 원천에서 유도한 서비스/자원/행위/클라이언트 IP 문맥이 필요합니다.
호출자 URL·등급·허용 판정·단순 설정 번호를 실제 소유권으로 받아서는 안 됩니다.
이 참조는 투영을 허가하거나 receipt nonce를 소비하지 않습니다. permit RPC·
실제 투영 소유자 검사·영속 paired replay 소비·최종 전달 연결·분산 멤버십/복구
경계는 계속 구현해야 합니다.

## 네이티브 라우팅 관측 gRPC 라이브러리 — 2026-10-15

한강 `4c7d700`은 독립 생성 계약 hangang-route-grpc 0.1.0과 공용
hangang-runtime 819177c의 읽기 전용 서버 라이브러리를 추가합니다. 실제 route
runtime·신뢰한 ingress 클라이언트 IP를 보존하고 서비스/audience/자원/행위/IP를
호출자 필드가 아닌 보존된 소유자에서 가져옵니다. 질의는 네이티브 참조·정확한 요청/
최종 절대 URI 해시만 전달합니다. URI 표시를 SHA-256에 직접 흘려 임시 URI 문자열
생성이나 본문 재해시 없이 대상 해시를 계산합니다.

필수 mTLS·별도 제한된 자격 참조·중복 자격 거부·전역 수용량·512/1,024바이트
디코딩/인코딩 제한을 적용합니다. 바뀐 binding·만료/취소된 참조·교체된 스냅샷을
거부합니다. 서버 future 취소는 남아 있는 인증 연결의 서비스도 중단합니다. 설정
리비전은 진단값이며 정상 관측도 권한·투영·분산 lease가 아닙니다.

실제 소켓 검사에서 소유자 유래 scope/IP·클라이언트 인증서 누락·잘못된 서버 이름·
역할 자격 누락/오류/중복·잘못되거나 큰 요청·참조/digest 변경·취소·교체·종료를
검증했습니다. 최종 workspace/all-target은 1,294개 통과·기존 명시적 제외 58개·
엄격한 Clippy·문서 링크 928개를 통과했습니다. 재빌드한 게이트웨이의 실제 네
프로세스 네이티브 자원/영속 재시작 검사도 통과했습니다. 이 검사는 기존 품계
요청 흐름을 사용하며 품계를 통한 원격 route 조회는 검증하지 않습니다. 앞서 검사/
재빌드를 겹쳐 실행해 테스트 실행 파일이 없어지는 실패가 있었으며 비공개 로그를
보존하고 통과 근거로 쓰지 않았습니다. 최종 순차 검사는 조건 완화 없이 통과했습니다.

소스는 main에 반영했으나 새 route 서비스 릴리스/운영 배포는 아닙니다. 시작/CLI·
감독 리스너 소유권·설정된 원격 소유자 클라이언트·품계로 참조 전달·permit/투영
소유자 검사·paired replay·분산/K8s 적용을 계속 구현해야 합니다. Actions는
활성화하지 않았습니다. 이후 빌드 디렉토리 잠금 아래 오래된 증분 캐시만 제거해
31.6 GiB를 회수했고 바이너리·소스·DB·백업을 보존했습니다.

## 라우팅 관측 프로세스·감독 통합 — 2026-10-15

한강 `dfc099e`는 --route-owner-config를 추가합니다. 자격/TLS 준비는 소켓을 열지
않으므로 기존 세대가 포트를 보유해도 --check로 검사하며 관리자 자격 재사용과
선언된 주소 충돌을 거부합니다. 활성화 전에 비공개 리스너를 준비하고 게이트웨이
준비 후 시작합니다. 단독 종료가 태스크를 소유하고 예상 밖 서비스 종료는
readiness를 내린 뒤 기존 종료 절차를 따릅니다.

감독 세대는 별도의 descriptor 역할로 소켓을 전달하며 정확한 주소·단일 역할·기존
개수 제한·CLOEXEC를 검사합니다. 인계 소유권 누락/추가는 거부합니다. 후속 세대의
비공개 자원은 다시 읽지만 요청별 참조는 전달하지 않습니다. 실제 프로세스에서
단독 종료·점유 포트 검사·새 PID가 서비스하는 HUP·잘못된 교체 후보 거부와 기존
세대의 mTLS 응답 유지를 검증했습니다. 첫 실패는 테스트가 stderr만 수집해 감독
stdout 진단을 놓친 것이며 로그 통합 수집으로 수정했고 후보 허용 조건은 바꾸지
않았습니다. 실패한 실행 로그는 비공개로 보존합니다.

전체 1,298개 통과/기존 명시적 제외 58개입니다. 조건문 스타일 수정 후 엄격한
Clippy를 통과하고 최종 수명주기/FD 집중 검사·실제 네 프로세스 네이티브 자원/영속
재시작 검사도 통과했습니다. 로컬 문서 링크 942개를 확인했습니다. 소스와 영문/
한글 가이드를 main에 반영했으며 새 정적 릴리스·K8s·운영 적용은 주장하지 않습니다.

원격 품계 클라이언트/참조 전달·소유자를 검사한 서명 권한·투영/paired replay·전체
신원/provider·분산/어댑터/처리량 요구사항은 남아 있습니다. 기존 운영 릴리스와
권한은 유지합니다.

## 실제 라우팅 관측 전달·구버전 강등 거부 — 2026-10-15

품계 `7425a83`은 고정 참조형 --route-live 원천과 제한된 지연 mTLS 연결을
구성합니다. 한강/품계 시작 순환 의존성을 없애지만 핸드셰이크 전 관측은 생성하지
않습니다. 참조·최종 대상/요청 digest·서비스/audience/자원/행위·실제 클라이언트
IP를 묶고 생성자가 비공개인 관측에 클라이언트 동일성·교환 시간을 반영해 최대
1초로 제한합니다. SQL을 읽지 않으며 신원/네트워크/정책 검사 전후에 실제 소유자를
조회하고 자원 누락·소유 범위 불일치를 거부합니다.

한강 `6bdb6c3`은 품계 crate 4개의 리비전을 통일하고 소유자 리스너가 설정된 경우
실제 보존 참조를 전달합니다. 품계 route_observed 확인이 필수이며 구버전의 필드
누락을 조용히 허용하지 않습니다. 기존 비소유자 모드는 별도 명시적 경로입니다.
확인 응답이나 로컬 관측 유효성은 서명 권한/전달 lease가 아닙니다.

호패 검사 `8e1250f`는 실제 네 실행 파일의 지속 mTLS gRPC에서 최종 URI/본문·
잘못된 서버 이름/호출 자격 거부·복구·거부 시 origin 횟수 불변·실제 서명 구버전
품계 0.1.6 교체와 복구를 검증합니다. 영속 권한/프로필 회수·네트워크/원천 장애도
통과했고 비소유자 호환 모드도 별도로 통과했습니다. 품계 workspace 69개·엄격한
Clippy, 한강 1,298개/기존 명시적 제외 58개·테스트의 불필요한 Copy clone 제거 후
엄격한 Clippy·문서 링크 942개를 통과했습니다.

소스는 main에 반영했습니다. 로컬 라우팅 관측 전달 검증이며 서명 권한·투영/paired
replay·새 정적/K8s/운영 적용·전체 신원/provider/어댑터·처리량 완료는 아닙니다.
현재 클라이언트는 고정 단일 원천이고 다중 소유자 발견·멤버십·연결 풀 라우팅을
통한 일반 scale-out은 남아 있습니다. 기존 운영 정책·신원·릴리스 자산은 유지합니다.

## 네이티브 인증 변환 계획 소유자 소스 검증

호패 fd06053은 필수 mTLS 게이트웨이 리스너에 `ProjectionPlans/Observe`를
추가했습니다. 허용된 호출 자격·공유 동시 요청 제한·요청/응답 512/1024바이트
제한을 적용합니다. 네이티브 컴파일 범위·최소 AAL·리비전만 반환하며 비밀 참조나
자격을 반환하지 않습니다. 요청은 ArcSwap 메모리를 읽습니다. SQL 변경 전 조회를
차단하고 정확한 롤백만 재개하며 교체 시 회수합니다. 커밋 실패는 영속 상태를
다시 읽을 때까지 차단합니다. 소유자 테스트 5개·인증 핸들러·실제 지속 mTLS
소켓으로 검증했습니다. 라이브러리 522개(기존 제외 1개)·workspace·Clippy 통과입니다.

품계 253e67c는 고정된 지속/지연 mTLS 소유자 클라이언트와 선택적인
`--projection-live` 설정을 추가했습니다. 네이티브 인증 리소스 판정 전후에 범위·
최소 AAL·리비전 하한·상관관계·캐시 TTL 0을 검사합니다. 비공개 관측은 설정된
클라이언트와 경과 시간/시계 역행을 반영한 보수적 1초 교환 예산에 묶입니다.
권한 캐시나 원격 lease가 아닙니다. 기존 정책·신원·네트워크·라우팅·호출자 검사를
유지합니다. 악의적 응답·용량 초과를 포함한 workspace 71개와 Clippy 통과입니다.

호패 검사 9d0d702로 실제 네 서버 gRPC 최종 전달에서 라우팅/계획 소유자,
잘못된 호패 서버 이름/호출 자격의 origin 효과 없는 거부·복구·영속 권한/프로필
회수·원천 장애를 통과했습니다. 기존 라우팅 전용 모드도 별도로 통과했습니다.
로컬 소스 계획 소유자 조회와 리소스 판정 연결 검증이며 서명 허가 발급·paired
replay/투영/최종 비밀 전달·다중 소유자 epoch/발견·정적/K8s/운영 적용·처리량은
계속 필요합니다.
