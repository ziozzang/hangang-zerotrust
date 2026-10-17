# hangang-world Helm 차트

[English](README.md) · [설치 안내](../../docs/ko/HELM_INSTALL.md) · [ADR 0022](../../docs/adr/0022-kubernetes-native-world-package.md)

릴리스 하나로 Hangang World의 네 구성 요소를 통합 제로 트러스트 패키지로 설치합니다.

| 구성 요소 | 역할 | 워크로드 | 포트(Service) |
| --- | --- | --- | --- |
| Hangang | Ingress 컨트롤러이자 강제 게이트웨이, `ProtectionPolicy`를 경로에 컴파일 | Deployment, 무상태, N개 복제본 | 공개 `http`/`https`, 선택적 `admin` 9000(TLS, 지표) |
| Hopae | 신원, 세션, 네이티브 게이트웨이 검증 | Deployment: SQLite 단일 복제본, 또는 외부 PostgreSQL 위의 여러 복제본 | `portal` 8700, `grpc` 8703(mTLS) |
| Pumgye | 인가 결정 | Deployment, 단일 기록자(SQLite) | `management` 9084, `ppg1` 9085, `grpc` 9087(mTLS) |
| Sumunjang | 네트워크 승인(IP/위험) | Deployment, 단일 기록자(SQLite) | `management` 9080, `binary-mtls` 9081, `grpc-mtls` 9082 |

CRD(`world.hangang.dev`)와 집계 역할 `world-admin`/`world-editor`/`world-viewer`는 별도의 [`hangang-world-crds`](../hangang-world-crds) 차트에 있습니다. 같은 버전으로 먼저 설치하십시오.

## 차트가 보장하는 것

- **엄격한 값 검증.** `values.schema.json`은 알 수 없는 키, 잘못된 CIDR·이름·기간, 동작할 수 없는 조합을 거부합니다(필드 간 규칙은 `templates/validate.yaml`). 스키마는 `tools/helm/build_world_schema.py`가 생성합니다.
- **digest로 고정한 이미지.** 활성화한 모든 구성 요소는 `image.digest`(`sha256:…`)가 필요하며, 태그는 참고용입니다.
- **강화된 Pod.** UID/GID 65532, `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, 모든 capability 제거, `RuntimeDefault` seccomp, service link 없음, ServiceAccount 토큰은 Kubernetes API를 호출하는 유일한 구성 요소인 Hangang에만 마운트합니다.
- **values에 비밀 값 없음.** API 자격 증명, PostgreSQL URL, 공급자 비밀은 미리 만든 Secret을 참조하며, 차트는 `Secret`을 렌더링하지 않습니다.
- **어디서나 상호 TLS.** 구성 요소마다 Service DNS 이름과 SPIFFE ID `spiffe://<trustDomain>/ns/<namespace>/sa/<serviceAccount>`를 가진 인증서 하나(서버·클라이언트 인증 겸용)를 cert-manager(부트스트랩 사설 CA 또는 사용자 Issuer/ClusterIssuer)로 발급하거나, 직접 준비한 Secret을 씁니다.
- **최소 권한 RBAC.** Hangang은 Service, Ingress, ProtectionPolicy에 `get/list/watch`, `protectionpolicies/status`에 `patch`를 받습니다. Secret은 `kubernetesTls`일 때만, `ingresses/status`는 `publishAddress`일 때만이며, `watchScope: Cluster`가 아니면 네임스페이스 Role입니다.
- **NetworkPolicy.** 모든 World Pod의 수신을 기본 차단하고, 아키텍처가 실제로 하는 호출만 허용합니다. 누구나(또는 `networkPolicy.publicFrom`) → Hangang, Hangang → Hopae·Pumgye·Sumunjang, Pumgye → Sumunjang, 지표 수집 피어 → Hangang admin.
- **실패 시 닫히는 보호.** `hangang.protection.enabled`이면 유효한 `ProtectionPolicy`가 없는 Ingress를 보류하고, Sumunjang 승인은 실패 시 거부하는 요청별 query 모드로 동작합니다.
- **네트워크 조건 정책을 위한 클라이언트 주소 보존**: `serviceLocal`(`externalTrafficPolicy: Local`), `proxyProtocol`(신뢰 CIDR에서만 PROXY v2), `hostNetwork`, `none`(이때 해당 정책은 보류).
- **가용성.** 무상태 구성 요소는 `maxUnavailable: 0` 롤링 업데이트, 단일 기록자는 `Recreate`, 게이트웨이는 토폴로지 분산, 복제본이 둘 이상이면 PodDisruptionBudget, 준비 상태는 컨트롤러 권한과 연동합니다.
- **보존되는 상태.** PVC에는 `helm.sh/resource-policy: keep`이 붙고, `existingClaim`으로 복원한 볼륨을 채택합니다.
- **운영.** 선택적 `ServiceMonitor`(HTTPS, Secret의 bearer 토큰), `helm test` 연결 점검, CRD나 클라이언트 주소 보존이 없으면 경고하는 `NOTES.txt`.

## 값

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `credentials.existingSecret` | `""`(필수) | `hangang-admin-token`, `hopae-gateway-key`, `guard-collector-token`, `guard-admin-token`, `pumgye-decision-token`, `pumgye-admin-token`을 가진 Secret(키 이름은 `credentials.keys`에서 변경) |
| `<component>.enabled` | `true` | 구성 요소 설치 여부 |
| `<component>.image.repository` / `.tag` / `.digest` | GHCR 경로 / 버전 / `""` | 활성화 시 digest 필수 |
| `<component>.resources`, `nodeSelector`, `tolerations`, `affinity`, `priorityClassName`, `podAnnotations`, `podLabels` | `values.yaml` 참조 | 배치와 크기 |
| `tls.mode` | `certManager` | `certManager` 또는 `existingSecrets` |
| `tls.certManager.issuerRef.name` | `""` | 비우면 사설 CA를 부트스트랩, 운영에서는 Issuer/ClusterIssuer 지정(`ca.crt`를 채워야 함) |
| `tls.certManager.duration` / `renewBefore` | `720h` / `240h` | 인증서 수명과 갱신 시점 |
| `tls.existingSecrets.<component>` | `""` | `tls.crt`, `tls.key`, `ca.crt`를 가진 직접 준비한 `kubernetes.io/tls` Secret |
| `global.trustDomain` | `cluster.local` | SPIFFE 신뢰 도메인 |
| `global.ha.backend` | `none` | `postgresql`이면 공유 저장소(Hopae) 사용 |
| `global.ha.postgresql.existingSecret` / `urlKey` / `caSecret` | `""` / `url` / `""` | 연결 URL과 서버 CA를 가진 Secret |
| `hangang.replicas` | `2` | 게이트웨이 복제본(무상태) |
| `hangang.watchScope` | `Namespace` | `Namespace`(Role) 또는 `Cluster`(ClusterRole) |
| `hangang.ingressClass.name` / `create` / `default` | `hangang` / `true` / `false` | 컨트롤러 `hangang.dev/ingress-controller`의 IngressClass |
| `hangang.publishAddress` | `""` | 승인된 Ingress 상태에 기록할 주소 |
| `hangang.kubernetesTls` | `false` | Ingress TLS Secret으로 TLS 종료 |
| `hangang.protection.enabled` / `requireProtection` | `true` / `true` | ProtectionPolicy 조정, 보호되지 않은 Ingress 보류 |
| `hangang.protection.identityProfiles` | `default` | 테넌트가 참조할 수 있는 프로필, 차트가 클러스터 내부 Hopae 엔드포인트를 연결 |
| `hangang.protection.pumgyeServices` | `{}` | 선택적 서비스 → 네임스페이스 허용 목록 |
| `hangang.guard.enabled` / `timeoutMs` | `true` / `100` | 게이트웨이의 Sumunjang 승인 |
| `hangang.service.type` / `port` / `nodePort` | `LoadBalancer` / `80` / `null` | 공개 Service |
| `hangang.clientAddress.mode` / `proxyProtocolFrom` | `serviceLocal` / `[]` | 클라이언트 주소 보존 |
| `hangang.admin.exposeMetrics` | `false` | 지표 수집을 위해 관리 API(TLS)를 Pod 네트워크에 노출 |
| `hangang.maxStalenessSeconds` | `300` | ADR 0022 제한된 오래됨: 넘으면 보호 경로는 503(`kubernetes-authority-stale`), 공개 경로는 마지막 정상 상태 유지 |
| `hangang.readiness` | `snapshot` | `snapshot`: 활성화된 스냅샷을 제공하는 동안 준비, `fresh`: 감시가 오래되면 준비되지 않음 |
| `<component>.tlsReloadSeconds` | `10` | 인증서/키/CA 내용 폴링, 교체 자료를 재시작 없이 사용(Pumgye 1–3600, 나머지는 0이면 끔) |
| `hopae.authentication.reloadIntervalMs` | `1000` | `config` 모드에서 프로필과 projection 계획 실시간 반영(0이면 끔, 200–60000), 이 키는 Pod를 다시 띄우지 않음 |
| `hopae.storage.backend` | `sqlite` | `sqlite`(1개 복제본, PVC) 또는 `postgresql`(복제본 > 1, RollingUpdate, PDB, `global.ha.postgresql` URL·CA Secret) |
| `hopae.portalIngress.*` | 비활성 | 로그인 경로용 명시적 공개 ProtectionPolicy(`access: Public`)를 가진 포털 Ingress |
| `hopae.storage.postgresql.*` / `migration.*` | 16 / 5000 / 2000 ms, 꺼짐 | 풀과 시간 제한, pre-upgrade SQLite → PostgreSQL 복사 Job |
| `hopae.authentication.source` | `config` | `config`: values가 인증 프로필을 소유하고 롤아웃마다 Hopae 저장소를 맞춤(Hopae PR #13), `store`: values는 빈 저장소만 부트스트랩 |
| `hopae.config` | portal/apps/providers | Hopae 설정, `listen`·`state_dir`·`store`·`gateway`·`authentication`·`reload`는 차트 소유 |
| `hopae.extraSecretEnv` | `[]` | Secret에서 가져오는 환경 변수(공급자 클라이언트 비밀) |
| `hopae.admin.enabled` | `false` | 상호 TLS를 쓰는 Hopae 관리 리스너 8702, ClusterIP 전용 `-admin` Service, 별도 서버 인증서(BYO면 `tls.existingSecrets.hopaeAdmin`), NetworkPolicy는 Hangang과 Pumgye만 허용 |
| `hopae.admin.publicUrl` / `untrustedPeers` / `serviceAudience` | 클러스터 내부 관리 Service / `as_client` / `""` | 호출자가 지정해야 하는 콘솔 origin, `service_audience`는 서비스 자격 증명을 지원하는 Hopae(PR #10) 필요 |
| `hopae.admin.delegation.keySecret` | `""` / `hopae-console-delegation-key` | 서명된 Hangang 콘솔 위임 키를 가진 Secret |
| `pumgye.hopaeOwner.enabled` / `tokenSecret` / `projection` / `lifecycle` | `false` | 이 구성 요소의 인증서와 경로 범위 `hsc1` 서비스 자격 증명으로 Hopae 관리 리스너를 읽는 Pumgye v2 소유자 입력(`--hopae-owner`) |
| `pumgye.bootstrapPolicy` / `sumunjang.bootstrapPolicy` | 최소 | 데이터베이스가 비어 있을 때만 사용 |
| `<component>.persistence.size` / `storageClassName` / `existingClaim` | `1Gi` / `""` / `""` | 상태 볼륨 |
| `networkPolicy.enabled` / `publicFrom` / `metricsFrom` | `true` / `[]` / `[]` | NetworkPolicy |
| `monitoring.serviceMonitor.*` | 비활성 | Hangang(관리 bearer), Pumgye·Sumunjang·Hopae(상호 TLS + 읽기 전용 지표 bearer) ServiceMonitor |
| `monitoring.serviceMonitor.clientCertificate.existingSecret` | `""` | 상호 TLS 리스너용 수집 클라이언트 인증서, cert-manager면 차트가 발급 |
| `credentials.keys.pumgyeMetricsToken` / `guardMetricsToken` | `pumgye-metrics-token` / `guard-metrics-token` | ServiceMonitor를 켰을 때 읽는 읽기 전용 수집 자격 증명 |
| `hopae.metrics.enabled` / `tokenSecret` | `false` | `hsc1` `metrics` 서비스 자격 증명으로 관리 리스너를 수집하는 Hopae ServiceMonitor |
| `hopae.consoleOperators.*` | 비활성 | Hopae `console_operators`(패스키 운영자, 서명된 단언) |
| `operatorAssurance.seedSecret` / `keyId` / `publicKey` / `nextKey` | `""` | Ed25519 운영자 단언: Hopae용 시드 Secret, 콘솔이 고정하는 공개 키 |
| `hangang.console.*` | 비활성 | 관리 API에 TLS로 접속하는 콘솔 어댑터 사이드카: `sso`, `sso.operatorPolicy`, `disableLocalLogin`, `operatorAudit`, `auditLog`, `plugins` |
| `monitoring.prometheusRule.*` | 비활성 | 권장 경보(TLS 재적재 실패, 인증서 만료, 오래됨, 체크포인트 나이, projection 신선도, 결정 가용성) |
| `tests.enabled` / `tests.image` | `true` / busybox | `helm test` Pod(`sh`, `nc`, `wget` 필요, digest 필수) |

CI가 쓰는 프로필은 [`ci/`](ci)에 있습니다. `minimal`, `ha`(PROXY v2 뒤 게이트웨이 3개, ClusterIssuer, ServiceMonitor, 클러스터 범위), `byo-certs`, 그리고 `admin`(Hopae 관리 리스너와 Pumgye 소유자)입니다. 일회용 로컬 클러스터 검증 결과는 [설치 안내](../../docs/ko/HELM_INSTALL.md#검증-기록--일회용-로컬-클러스터-2026-10-17)를 참조하십시오.

## 확장과 HA

Hangang은 컨트롤러 모드에서 무상태이므로 자유롭게 늘릴 수 있습니다. Hopae는 SQLite 단일 복제본으로, 또는 외부 PostgreSQL 위의 여러 복제본(`storage.backend: postgresql`, Hopae PR #16)으로 실행합니다. Pumgye와 Sumunjang은 이번 릴리스에서 단일 기록자이며(스키마가 `replicas`를 1로 제한), ADR 0022에 따라 서명된 스냅숏 배포가 생기면 무상태 스냅숏 복제본이 됩니다. 차트는 두 Pod가 데이터베이스 하나를 공유하게 두는 대신 SQLite에서 `replicas > 1`을 거부합니다.

## 업그레이드와 되돌리기

`hangang-world-crds`를 먼저, 그다음 같은 버전의 `hangang-world`를 업그레이드합니다. 같은 minor 계열 안에서 N-1 → N 업그레이드와 N-1로의 `helm rollback`을 지원합니다. 백업과 순서 규칙은 [설치 안내](../../docs/ko/HELM_INSTALL.md#업그레이드와-되돌리기)를 참조하십시오.

## 검증

```sh
python3 -m unittest tools/test_helm_charts.py          # helm lint/template, invariants, refused values
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py   # plus schema validation (network)
```
