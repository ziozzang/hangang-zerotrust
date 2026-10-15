# Hop 오프라인 상태 준비와 스키마10 롤백

`tools/hopae_state_rollout.py`는 비공개 오프라인 증거와 별도 상태 복사본을
준비합니다. Docker/systemd 중지, 바이너리 배포, 마운트 교체, Human 인증 활성화는
수행하지 않습니다. 먼저 단일 Hop 소유자를 중지하고 provider/admin CLI 작업도
배제해야 합니다. 기존 `state_dir/hopae.lock`의 Linux `flock`은 실제 Hop 잠금과
동일합니다. 잠금 획득은 로컬 관측이며 분산 fencing이나 복제 방지가 아닙니다.

기본 DB는 `state_dir/hopae.db`이며 `store.path`도 구성 상태 디렉터리 내부여야
합니다. 이 상대경로를 전달한 호스트 볼륨으로 대응합니다. 외부 DB, 심볼릭·하드 링크,
특수 파일, 1GiB 초과 파일, 10000개 초과 항목은 거부합니다. 상태 파일 전체를
복사하며 SQLite는 커밋된 WAL을 포함하는 backup API와 무결성 검사로 독립된
DELETE-journal DB를 만듭니다. 원본 DB/WAL과 일반 파일의 해시·크기·inode/device·
소유권·권한을 완료 전에 재확인합니다. 백업 자체가 변경할 수 있는 SQLite SHM
reader mark 내용은 업무 데이터가 아니므로 해시에서 제외하되 메타데이터는 검사합니다.
WAL/SHM을 DB 백업 대신 사용하지 않습니다. 빈 디렉터리도 보존합니다. 백업 해시는
복사에 따른 inode 변경에 의존하지 않습니다.

## 준비

아래는 운영에 실행한 명령이 아닌 템플릿입니다. 원본 밖의 새 비공개 경로를 사용하고
구성·환경·키·증명·비공개 로그 내용을 출력하지 마십시오.

```sh
umask 077
python3 tools/hopae_state_rollout.py prepare \
  --state-dir /private/host-volume/state \
  --config /private/hopae.json \
  --private-file /private/service.env \
  --private-file /private/external-tls-key.pem \
  --output /private/backup-before-0011
```

상태 전체와 정확한 구성 파일을 보존합니다. 반복 가능한 `--private-file`로 외부
TLS, TOTP 암호화, 세션/receipt 서명, 전용 Human material 키, 호출자 신원을 복구하는
동반 파일을 모두 명시해야 합니다. 환경값은 자동 수집하거나 출력하지 않습니다.
비공개 manifest가 번호별 복사본과 원래 경로를 연결합니다. 파일 밖의 비밀은 기존
secret manager 복구 절차가 필요합니다. 간접 참조를 자동 추론할 수 없으므로 운영자가
마이그레이션 전 목록을 검증해야 합니다. 디렉터리는0700, 파일은0600입니다.
표준출력에는 작업명·성공 또는 고정 거부 코드만 표시합니다. 준비 실패 시 자신이 만든
부분 출력만 제거하고 기존 경로를 덮어쓰지 않습니다.

관리자가 manifest와 파일을 함께 변조하는 경우를 암호학적으로 방어하지 않습니다.
기존 신뢰된 백업 체계로 digest와 외부 사본을 보호하십시오. 임의 네트워크 파일시스템의
SQLite·잠금 동작은 검증 범위 밖입니다.

## 오프라인 후보 검증

```sh
python3 tools/hopae_state_rollout.py shadow \
  --backup /private/backup-before-0011 \
  --candidate /private/exact-frozen-hopae \
  --sha256 EXACT_64_LOWER_HEX_BINARY_SHA \
  --output /private/shadow-0011
```

Linux `unshare --user --map-root-user --net`가 필요하며 실패 시 거부합니다.
해시가 일치하는 후보로 고정된 `--config <비공개 구성> --check`와
`--config <비공개 구성> providers import`만 각각60초 한도로 외부 통신이 없는
새 네트워크 네임스페이스에서 실행합니다. 임의 명령·셸·서버·운영 리스너는 없습니다.
상태와 DB 경로만 별도 복제본으로 바꿉니다. 원래 백업은 보존합니다. 필요한 승인된
서비스 환경은 값을 출력하지 않고 상속으로 제공하십시오. 다른 구성 참조는 유지되며
동반 파일 복사본은 복구 자료이지 임의 경로의 자동 재매핑이 아닙니다.

실제 Hop provider-import는 `Store::open`을 사용해 마이그레이션하고 DB 소유
provider import 규칙을 적용하므로 SHADOW provider 행을 변경할 수 있습니다.
읽기 전용 명령이 아닙니다. 성공 조건은 무결성과 schema_migrations MAX(version)==10
입니다.0600 로그에 provider 식별자가 포함될 수 있어 공개하면 안 됩니다.
이 검증은 오프라인 구성 검사와 실제 저장소 마이그레이션만 증명합니다. 모든 serving
Registry/material 준비, 로그인, 서비스 건강성까지 증명하지 않으며 별도 격리된
serving·인증·정확한 아티팩트 검증이 필요합니다.

## 상태를 포함한 롤백 준비

구버전 바이너리가 스키마10을 열어서는 안 됩니다. 새 소유자를 중지하고 CLI 쓰기를
배제합니다. 배포 감독자는 새 트래픽·변경을 받기 전 합의된 가역 경계에서 정지 상태
seal을 보존해야 합니다.

```sh
python3 tools/hopae_state_rollout.py seal \
  --state-dir /private/host-volume/state --output /private/stopped-state-seal.json
python3 tools/hopae_state_rollout.py restore \
  --backup /private/backup-before-0011 \
  --current-state-dir /private/host-volume/state \
  --current-seal /private/stopped-state-seal.json \
  --output /private/prepared-old-state
```

복원은 현재 소유자 잠금과 정확한 seal 목록을 전후 검사하고 별도의 구상태·구성·동반
파일 디렉터리만 준비합니다. 현재 상태·구성을 덮어쓰거나 구버전을 실행하지 않습니다.
데이터 변경·새 세션/회수·실행 중 소유자·변조·기존 목적지는 거부합니다. 나중에 새로
만든 seal은 이전 쓰기가 없었다는 증거가 아닙니다. 감독자는 올바른 이전 seal을
보존하고 중간 변경을 조정해야 하며 재seal로 거부를 우회하면 안 됩니다. 새 쓰기를
승인한 뒤 과거 백업으로 복원하면 그 쓰기가 사라지므로 안전한 운영 조정 없이
자동 롤백해서는 안 됩니다.

Docker 중지·마운트 전환, 원래 UID/GID/권한, 외부 동반 파일 복원과 구이미지 기동은
후속 배포 도구 범위입니다. 마이그레이션 디렉터리를 격리 보존하고 구상태·정확한 구성·
키 전체를 한 운영 단위로 복구한 뒤 소유자 하나만 기동하고 일반 인증을 확인합니다.
DB 병합·realm만 복사·tombstone/replay 삭제·복제본 동시 실행은 금지합니다.
임의 VM/DB live clone과 rollback 변조는 외부 fencing 없이는 지원하지 않습니다.

## 검증

```sh
python3 -m unittest discover -s tools -p test_hopae_state_rollout.py
HOPAE_ROLLOUT_OLD_BINARY=/private/exact-old-hopae \
HOPAE_ROLLOUT_CANDIDATE=/private/exact-new-hopae \
python3 -m unittest discover -s tools -p test_hopae_state_rollout.py
```

선택 native 사례는 변경하지 않는 구바이너리를 새 fixture에 복사해 실제 구스키마를
만들고 실제 후보로 shadow만 네트워크 격리 마이그레이션하여 스키마10과 구상태 복원
준비를 확인합니다. 두 바이너리 경로가 없으면 명시적으로 skip합니다. SQLite 사례는
WAL, 실제 다른 프로세스의 잠금, 원본 변경, 목적지·변조·링크 거부, 권한, 복사 가능한
백업 해시, seal 롤백과 오류 비밀 비노출을 검증합니다. 모의 후보는 호출/실패 처리만
검사하며 실제 native 마이그레이션·serving 검증을 대체하지 않습니다.

SQLite 백업은128페이지 단계 사이에10초 단조 시계 한도를 확인하며 busy timeout100ms와 poll50ms를 사용합니다. 실제 잠금 충돌 거부를 별도로 검사하며 동시 CLI 작업을 허용하는 의미가 아닙니다.
