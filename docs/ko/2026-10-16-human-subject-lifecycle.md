# H2a: source 소유 Human subject와 authority lifecycle

상태: **구현 제안이며 제품 코드/Human RPC 활성화가 아닙니다.**
[English normative contract](../reviews/2026-10-16-human-subject-lifecycle.md).
ZT 기준 c62cf69ccca3c8cc537e3233a0d7da1faf63e8d3, Hop 확인 기준
eefc358be73c71646abb53e5f6651698fe362392. Cargo·cluster·운영 검사를 하지 않았습니다.
앞선 wire 설계의 임시 s_48 Human 제안을 정교화하며 Service/Workload s_48 및 기존
strict session receipt는 바꾸지 않습니다.

## 실제 소스 사실

- identity/types.rs:5, lib.rs:11의 UserId는 String newtype이며 new는 임의 문자열을
  받습니다. u_26 주석이 validation/capability를 뜻하지 않습니다.
- 실제 directory.rs:128-181은 crypto/mod.rs:261의128 random bits로 u_+26 Crockford
  문자열을 같은 SQLite writer transaction에서 만듭니다. live PK만으로 과거 삭제 ID
  재사용을 막지는 못합니다.
- schema2 users에는 user_id immutable/history guard가 없습니다. identities는
  (provider_id,subject)→user_id FK입니다. production hard-delete/reinsert API는
  발견하지 못했지만 그 부재만으로 영구 no-reuse를 주장하지 않습니다. admin.rs:483의
  disable은 authz_version을 올리고 session을 종료합니다. enable은 다른 사람 생성이 아닙니다.
- identity/service.rs:145-248과 linking.rs:55-107은 실제 provider assertion과
  authoritative verified-email 명시 opt-in을 사용합니다. 같은 email만으로는 기본적으로
  LinkRequired입니다. 실제 link_identity caller는 AutoLinked apply입니다. LinkRequired는
  pending transaction을 만들지만 이번 검사에서 manual join 완료 caller는 찾지 못했습니다.
  완료된 authorized flow 검증은 별도 gate이며 subject helper가 이를 대신하지 않습니다.
- H0 human.rs:52,108,379,387 및 sqlite/human_owner.rs:65는 실제 HandleView/current
  user/session/provider/material/factor를 보존합니다. receipt_issuer.rs:482의 기존
  SessionSeal signer를 새 observed source로 간주하지 않습니다. receipt issuer_ref는
  실제 서버 설정/key registry 소유이며 caller assertion이 아닙니다.

## Canonical subject 제안

```text
LP32(x) = u32be(byte_length(x)) || x
preimage = ASCII("hopae:native-human-subject:v1") || 0x00
        || LP32(fixed_receipt_issuer_ref_ASCII)
        || LP32(durable_authority_realm_raw32)
        || LP32(exact_native_user_id_UTF8)
subject = "human1:" || lowercase_hex(SHA256(preimage))
```

출력은 정확히71 ASCII 바이트이며 human1:+64 lowercase hex만 받습니다. issuer_ref는
기존1..128 ASCII identifier의 정확한 바이트/대소문자입니다. realm은 authoritative
Store에 한 번 저장하는 nonzero32바이트 **공개 namespace**이며 표시 형식은64 lowercase
hex입니다. caller/operator 자유 문자열 realm이나 secret key가 아닙니다. user ID는
실제 current Store row의 nonempty<=256 UTF8바이트이며 NUL/C1 포함 Unicode control(char::is_control)을 거부하는 새 Human
qualification 제안입니다. UserId::new가 검사했다고 가정하지 않고, 그 밖의 legacy ID는
일반 동작을 유지하되 Human proof를 거부합니다. trim/casefold/Unicode 정규화는 없습니다.

이것은 안정적인 native **계정 principal**이지 현실의 동일인 증명이 아닙니다. 여러
provider identity는 실제 native 정책에 따라 같은 계정에 authorized join된 경우만
같은 subject가 됩니다. 같은 email/name/groups/provider-sub 문자열의 다른 계정은 다른
subject입니다. hash는 공개 pseudonymization이며 암호화·익명성·인증이 아닙니다.

signing key/epoch, caller/mTLS key, material key, provider/material/config revision,
factor enrollment/counter, AAL, user authz revision, session cred_gen, process/BOOTTIME
nonce는 preimage에 넣지 않습니다. 이들은 current 자격과 signed context를 바꾸며 durable
권한 좌표를 바꾸지 않습니다. user/session revision은 owner별이며 다른 사용자 사이
전역 floor로 쓰지 않습니다. AAL은 실제 qualified native factor에서만 나옵니다.

## Parent 승인 storage foundation과 후속 경계

schema10 구현은 별도로 진행 중이며 이 문서가 통과한 소스라고 주장하지 않습니다.

1. human_authority_realm(singleton1, realm TEXT64lowerhex)는 atomic migration 안의 SQLite
   lower(hex(randomblob(32)))로 한 번 생성하며 exact size/nonzero/lowercase를 검사합니다.
   subject LP32 입력은 canonical TEXT를 decode한 raw32바이트입니다. 공개 namespace
   유일성 데이터이며 secret·key·외부 fencing 증거가 아닙니다. immutable/anti-REPLACE
   guard가 UPDATE/중복 singleton INSERT/DELETE를 거부합니다. 기존 realm을 재생성하지
   않고 issuer를 저장하거나 ordinary 시작의 필수 값으로 만들지 않습니다.
2. human_user_ids(user_id PRIMARY KEY)는 FK cascade 없는 append-only 예약
   집합입니다. 기존 live ID를 migration에서 채우고 users AFTER INSERT가 같은 transaction에
   예약합니다. BEFORE INSERT는 이미 예약한 ID의 INSERT/REPLACE/UPSERT 재사용을 모두
   거부하며 BEFORE UPDATE OF user_id는 ID 변경을 막습니다. DELETE 뒤에도 예약은
   영구 유지하며 실제 user row의 존재가 liveness입니다. ledger 삭제/키 변경/교체는
   거부하고 실패는 user·예약 모두 rollback합니다. FK로 막힌 삭제에 partial retirement는 없습니다.

Directory만이 아니라 모든 insert/import/test-hook 경로를 포함해야 하며 hard-delete API를
새로 만들 필요는 없습니다. 기존 임의 UserId는 그대로 보존합니다. native random ID가
과거 예약과 충돌하면 기존 grant에 연결하지 않고 원자 거부합니다. 예약을 capacity 이유로
지우거나 ordinary 계정 수에 임의 새 상한을 넣지 않습니다. Store/disk failure는 거부하며
장기 growth policy는 별도 검토합니다.

재시작 시 실제 schema/guard/reservation을 검증하고 누락 guard를 몰래 복구하지 않습니다.
live ID backfill은 identity infrastructure이며 legacy primary/factor proof backfill이
아닙니다. 설치 전 삭제 이력은 알 수 없고 human1 proof/grant는 아직 없으므로 이전
raw-user/s_48 grant를 자동 변환하지 않습니다. privileged SQL의 guard 삭제/전체 DB 복사까지
방지하는 tamper-proof storage라는 주장은 하지 않습니다.

realm storage는 receipt_issuer/Service profile 활성화를 요구하지 않습니다. 기존 H0
joined current transaction에서 읽고 Current equality에 exact realm을 포함합니다.
issuer binding/canonical derivation은 후속 H2 owner 단계입니다. 실제 Human issuer가
설정됐을 때만 fixed issuer_ref+opened Store+realm을 준비합니다. 미설정 ordinary OIDC/H0는
유지하고 독립 realm cache나 caller realm constructor를 만들지 않습니다.

초기 버전은 realm 교체 API가 없습니다. issuer-ref 변경은 signing key rotation과 다른
identity namespace/policy migration이며 subject가 달라집니다. 같은 issuer/realm/user를
복구하면 같은 계정 좌표가 나오지만 옛 issued proof가 살아나지는 않습니다. 새 realm은
명시 cutover/regrant/retirement 설계가 필요하며 config A→B→A로 저장 realm을 덮어쓰지 않습니다.
표시 label은 realm 바이트와 별개입니다.

## 실제 API와 검증 순서

private PreparedHumanAuthority만 실제 Store realm+고정 native issuer에서 준비하며
opened Store/정확한 row를 유지합니다. CurrentHumanUser는 실제 H0 joined current의
live user·예약·정확한 handle/session/원래 owner facts에서 나옵니다. 이 둘로만 private
HumanSubject를 계산하며 caller UserId/realm/Identity 생성자는 자격이 없습니다. 공개
human1 parser나 fixture hash는 문법/데이터만 검증하고 native evidence·clock·AAL·grant를
반환하지 않습니다.

authority/예약 검사도 기존 bounded transaction 안에 추가합니다. paired writer 아래
새 async SQL 호출을 넣지 말고 후속 connection-scoped checker가 같은 비교를 사용합니다.
namespace만 있다고 legacy primary/factor/session이 qualified가 되지 않습니다. 원래
BOOTTIME·source record/current owner 검사는 sign/observe/final output까지 남습니다.
Pum human_users는 별도 human1 parser/typed evaluator만 사용하며 users/workload_users
fallback이 없습니다. Admin selector는 authorized Hop lookup으로 실제 subject를 얻고
client email/realm을 publication으로 승격하지 않습니다. SDK는 signed opaque subject와
source/current report를 검증하지 사용자가 계산한 hash로 grant를 만들지 않습니다.

| 동작 | subject/current 기대 |
|---|---|
| 같은 Store restart·signing/caller key rotation | 같은 subject, proof/key/current 검사는 별도 |
| provider/CA/material/key 변경·ABA 뒤 실제 재인증 | 같은 계정 subject, 옛 primary/capture는 거부 |
| email/name/groups·disable/enable | subject 유지, authz/session 회수 적용·enable로 session 부활 금지 |
| 실제 authorized identity join | 같은 native account에 연결된 경우만 같은 subject |
| 삭제 뒤 같은 email/name/provider 재등록 | 새 user ID/subject, 옛 예약 ID는 영구 재사용 불가 |
| user_id 변경·REPLACE/UPSERT 재사용·ledger 삭제/교체 | rollback, grant 상속/부분 변경 없음 |
| 다른 issuer/새 authority realm | 다른 subject, 현재 source-policy/proof fence 적용 |
| caller human1/UserId/realm/AAL DTO | 문법/데이터일 뿐 native source 아님 |

영문 literal vector는 Python hashlib/struct로 계산한 설계값이며 production encoder 통과
주장이 아닙니다. base expected는
human1:0489407b9305f47f90756344cdc79c83eddc7b5e292ac82fa88f74c5edbbca9d입니다.
영문 표에 user/realm/issuer 변경·UTF8 precomposed/decomposed 구분·정확한 base preimage가
있습니다. SHA/LP32 독립 vector 뒤 실제 SQLite create/noop/reopen/rollback/FK실패/
delete-recreate/REPLACE/UPSERT/guard corruption, 실제 OIDC/LDAP 및 허용한 linking/TOTP
H0에서 source-derived subject, legacy 미자격/cross-Store 거부를 검사해야 합니다. 같은 hash
인자 self-equality로 key/provider lifecycle 검증을 대신하지 않습니다. 기존 Service/Workload/
v1/ordinary 회귀도 필요하며 이 설계는 그 테스트를 실행했다고 하지 않습니다.

## Restore·replica·외부 provider 한계

realm은 정상 백업/복원에서 유지되고 같은 authoritative dataset의 계정 grant 좌표가
보존됩니다. 그러나 최신 데이터임을 증명하지 않으며 옛 snapshot에는 tombstone/authz/replay가
빠질 수 있습니다. cold restore는 issuer runtime을 재시작해 process proof domain을 바꾸고
권위 있는 user/replay 이력 보존·review된 fencing 절차를 따라야 합니다. retirement 전
snapshot 복구는 옛 데이터를 살릴 수 있고 임의 rollback을 random realm으로 숨기지 않습니다.
같은 live realm/key/DB를 독립 clone하면 외부 fenced incarnation/linearizable authority 없이
구분할 수 없습니다. 모든 restart의 grant 무효화나 자동 realm rotation은 해결책이 아닙니다.

현재는 single-Store source이며 replicated identity backbone 검증이 아닙니다. 후속
backbone은 하나의 realm·ID 이력·단조 current publication·membership fence를 보존해야
합니다. 독립 새 Store는 같은 issuer/user 문자열이라도 새 realm을 갖습니다. 외부 OIDC
issuer/sub와 LDAP immutable subject 신뢰는 실제 adapter/material owner 책임이며 같은
email이 모든 issuer의 동일인을 뜻하지 않습니다. Google forced reauth·원격 계정/directory
회수·자체 password/복구·완전 Human RPC/SDK/Pum/Root 목표는 계속 남습니다.
