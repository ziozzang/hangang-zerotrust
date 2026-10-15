# 소유한 네이티브 Human 런타임 fixture

외부 production Hop 실행파일과 소유한 OIDC 또는 TLS OpenLDAP 원천을 실행하고 실제 포털 로그인, 애플리케이션 handoff, TOTP 등록·step-up, 로그아웃을 사용합니다. SQL이나 비공개 생성자로 네이티브 primary/session/proof/SDK Observation을 만들지 않습니다. 소비자는 실제 mTLS Human RPC에 공개 SDK로 접속해야 합니다.

Linux, Python3 `cryptography`, OpenSSL 및 Human 원천/RPC/scope 지원이 포함된 정확한 Hop 바이너리가 필요합니다. 해당 소스 기준은 `b08e105666de99f2ae957cff16ca9f3c75d3f7c5`입니다. 표시 버전0.0.10만으로 지원 여부를 판단하지 말고 실제 소스·바이너리 SHA를 검증하세요. test-hooks 없이 빌드하며 운영 DB·설정·토큰·디렉터리를 넣지 않습니다. LDAP는 해당 Hop checkout에서 `docker build -t hopae/owned-openldap:bookworm tests/fixtures/ldap`로 만든 로컬 소유 이미지가 필요하며 도구가 이미지를 pull하지 않습니다. 고유 container 이름과 loopback port를 사용하는 fixture이지 운영 격리 권장안은 아닙니다.

```sh
fixture_root="$(mktemp -d)"
python3 tools/test-support/native-human-runtime/runtime_fixture.py \
  --binary "$OWNED_HOPAE_BINARY" --provider oidc \
  --directory "$fixture_root/runtime" --ready "$fixture_root/ready.json"
```

새 `--directory`는0700으로 생성합니다. LDAP는 `--provider ldap`, 필수 StartTLS는 `--ldap-starttls`로 선택합니다. 외부 소유 디렉터리 주입이 필요하면 `OWNED_LDAP_CONFIG`, `OWNED_LDAP_BIND_KEY`, `OWNED_LDAP_USER_PASSWORD`를 이 프로세스에만 전달하고 값을 기록하지 않습니다.

실제 AAL1 로그인과 handoff 이후에만0600 ready JSON을 원자적으로 게시합니다. endpoint/server_name, CA/인증서/키 경로, caller_file, 공개 서명키, 고정 issuer/authority/floor, 정확한 scope 및 비공개 cookie 경로가 포함됩니다. 소비자는 실제 공개 SDK Observation에서 확인한 subject로 Pum `human_users` grant를 게시해야 합니다. ready 메타데이터로 Observation/subject를 제조하지 않습니다.

고정 scope는 orders/orders-api, app, owned-route revision11, destination0x12×32, header policy13 및 빈 bound header 집합입니다. x-owned-secret은 예약합니다. SDK 실제 요청은 GET /data와 body `body`이며 신원 검증 URL은 https://app.example.test/data, IP192.0.2.10, UA 없음입니다. ready의 destination은32개 byte 배열입니다.

stdin JSON 명령과 stdout의 안전한 제어 응답을 사용합니다.

- `{"op":"login","aal":1}` 또는2: 실제 새 로그인으로 cookie-1/2를 갱신합니다. AAL2는 실제 TOTP 등록·step-up을 거칩니다. 재사용 counter 회피를 위해 최대30초 다음 counter를 기다릴 수 있어 제어 명령은65초를 허용합니다. 네이티브 증명의 원래1초 예산은 변경하지 않습니다.
- `{"op":"revoke","aal":1}` 또는2: 해당 브라우저의 현재 세션을 실제 포털에서 로그아웃합니다. 복구는 종료 세션 부활이 아니라 새 로그인입니다.
- `{"op":"shutdown"}`: 정확히 소유한 Hop child 종료를 기다리고 소유한 LDAP container만 제거합니다.

stdout에는 ok/op 및 필요한 aal/cookie_file 경로만 나옵니다. 쿠키·토큰·키·TOTP seed·증명·header/context payload는 출력하지 않습니다. 진단 파일은 등록 데이터를 포함할 수 있으므로0700 디렉터리 안0600으로 보관합니다. SIGTERM과 부모 PID 소실은 정리 경로를 실행하며, 소비자는 종료 요청/SIGTERM 후 기다려야 합니다. SIGKILL 정리는 보장하지 않습니다. 증거 디렉터리는 보존합니다.

```sh
python3 -m unittest discover -s tools/test-support/native-human-runtime \
  -p test_runtime_fixture.py -v
```

결정적 시험3개는 첫 ready 게시 전 비가시성, 교체 중 기존 완전 JSON 유지, 실패 시 기존 데이터 보존과 임시 파일 제거를 검증합니다.0600 임시 파일의 flush/fsync 후 원자적 교체로 ready.exists/read-EOF 경합을 해결하며 인증 재시도나 예산 완화는 하지 않습니다.

별도 실제 시험은 소유한 OIDC·LDAPS·필수 StartTLS의 로그인/TOTP→공개 Human SDK→실제 Pum Authority/DB CAS까지 검증했습니다. 그 시험의 network/route/plan은 인증된 fixture peer였습니다. 이 도구만으로 전체 Human paired projection/Root/backend, 외부 운영 IdP, 분산 원자 revocation 또는 처리량 검증을 주장하지 않습니다. 자세한 주 계약은 [영문 안내](README.md)를 따릅니다.

## 공개 SDK → 네이티브 Pum 소비자 재현

Pum 공개 소스 `f6fb7d9a7e92b615d3c2525999b55a66e7a491ac`가 포함된 checkout에서 이 저장소 helper와 검증한 Hop 바이너리의 절대 경로를 지정합니다.

```sh
OWNED_HUMAN_RUNTIME_FIXTURE=/absolute/zerotrust/tools/test-support/native-human-runtime/runtime_fixture.py \
OWNED_HOPAE_BINARY=/absolute/qualified/hopae \
OWNED_HUMAN_PROVIDER=oidc \
cargo test --locked -p pumgye-server --features observed-authentication \
  --test human_observed_permit actual_native_hop_sdk_to_pum_authority_human_permit \
  -- --ignored --test-threads=1
```

LDAP는 `OWNED_HUMAN_PROVIDER=ldap`, 필수 StartTLS는 추가로 `OWNED_HUMAN_LDAP_STARTTLS=1`을 지정해 각각 별도 기능 시험으로 실행합니다. 인증 재시도가 아닙니다. 소비자는 비공개 증거를 보존하고 실제 SDK subject 확인 후 grant를 게시하며 AAL/plan/정책 CAS와 원래 증명 예산이 남은 상태의 로그아웃 거부를 검사합니다. 종료 세션 부활이나 Human projection/Root 출력을 검증했다고 주장하지 않습니다.
