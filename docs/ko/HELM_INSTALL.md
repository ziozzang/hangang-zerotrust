# Helm으로 Hangang World 설치하기

[English](../HELM_INSTALL.md) · [설계 목차](README.md) · [차트 참조](../../charts/hangang-world/README.ko.md)

이 안내는 통합 Hangang World 패키지(ADR 0022 P0 패키징)를 설치합니다. `hangang-world` 차트로 Hangang, Hopae, Pumgye, Sumunjang을, `hangang-world-crds` 차트로 `world.hangang.dev` CRD를 설치합니다. 차트는 오프라인으로 검증했습니다(`helm lint`, 여러 프로필의 `helm template`, Kubernetes·cert-manager·Prometheus Operator 스키마 검증, 렌더 테스트). 로컬에서 빌드한 이미지로 일회용 로컬 k3d 클러스터에 설치해 기능도 검증했습니다([검증 기록](#검증-기록--일회용-로컬-클러스터-2026-10-17)). 운영 또는 레지스트리 기반 설치는 아직 없습니다. [운영 설치를 아직 막는 것](#운영-설치를-아직-막는-것)을 참조하십시오.

## 사전 조건

- Kubernetes 1.27 이상, NetworkPolicy를 강제하는 CNI(없으면 정책은 효과가 없습니다).
- `tls.mode: certManager`에는 cert-manager 1.12 이상(`existingSecrets`에는 미리 준비한 TLS Secret).
- `network.enforcement: Required`를 쓰는 `ProtectionPolicy`가 있다면 `externalTrafficPolicy: Local`을 지원하는 로드 밸런서 또는 PROXY protocol v2를 보내는 로드 밸런서.
- 신뢰하는 레지스트리에 게시하고 **digest로** 참조하는 구성 요소 이미지.
- 선택: `monitoring.serviceMonitor`용 Prometheus Operator, 복제본이 둘 이상인 Hopae용 PostgreSQL.

## 설치

1. 네임스페이스와 자격 증명 Secret을 만듭니다. 32바이트 이상의 임의 값을 쓰고 버전 관리에 넣지 마십시오.

   ```sh
   kubectl create namespace hangang-world
   kubectl -n hangang-world create secret generic hangang-world-credentials \
     --from-literal=hangang-admin-token="$(openssl rand -hex 32)" \
     --from-literal=hopae-gateway-key="$(openssl rand -hex 32)" \
     --from-literal=guard-collector-token="$(openssl rand -hex 32)" \
     --from-literal=guard-admin-token="$(openssl rand -hex 32)" \
     --from-literal=pumgye-decision-token="$(openssl rand -hex 32)" \
     --from-literal=pumgye-admin-token="$(openssl rand -hex 32)"
   ```

2. CRD 차트를 설치합니다(클러스터 범위, 클러스터당 한 번).

   ```sh
   helm upgrade --install world-crds charts/hangang-world-crds
   ```

3. 이미지 digest, Hopae 포털과 애플리케이션, 클라이언트 주소 모드를 담은 values 파일을 작성합니다. `charts/hangang-world/ci/minimal-values.yaml`에서 시작하고 비밀 값은 절대 넣지 마십시오.

4. 패키지를 설치합니다.

   ```sh
   helm upgrade --install world charts/hangang-world -n hangang-world -f my-values.yaml
   helm test world -n hangang-world
   ```

5. 경로를 보호합니다. `requireProtection: true`(기본값)이면 클래스 `hangang`의 Ingress는 `ProtectionPolicy`가 적용될 때만 게시됩니다.

   ```sh
   kubectl -n shop apply -f protection-policy.yaml
   kubectl -n shop get protectionpolicies
   ```

## 클라이언트 주소 모드 선택

| 모드 | 사용 상황 | 요구 사항 |
| --- | --- | --- |
| `serviceLocal` | 클라우드 또는 MetalLB 로드 밸런서 | `service.type`이 LoadBalancer 또는 NodePort, 트래픽은 준비된 게이트웨이 Pod가 있는 노드에만 전달 |
| `proxyProtocol` | PROXY v2를 보내는 L4 로드 밸런서 | `proxyProtocolFrom`에는 로드 밸런서 출발지 CIDR만 넣고 kubelet 프로브 출발지는 제외 |
| `hostNetwork` | 베어메탈 에지 노드 | 게이트웨이 Pod가 호스트 포트에 바인딩, host-network Pod에는 NetworkPolicy가 적용되지 않음 |
| `none` | 신원만 쓰는 정책 | `network.enforcement: Required` 정책은 보류 |

## 인증서

`tls.mode: certManager`는 구성 요소마다 서버·클라이언트 인증을 겸하는 인증서 하나를 발급하며, Service DNS 이름(`<release>-hangang-world-<component>.<namespace>.svc[.cluster.local]`)과 ServiceAccount의 SPIFFE URI SAN을 넣습니다. `issuerRef.name`이 비어 있으면 차트가 네임스페이스에 사설 CA를 부트스트랩합니다. 운영 설치에서는 `ca.crt`를 채우는 PKI의 Issuer 또는 ClusterIssuer를 `issuerRef`로 지정하십시오(CA·Vault 발급자는 채우고, ACME 발급자는 채우지 않아 내부 mTLS에 적합하지 않습니다). `tls.mode: existingSecrets`에서는 구성 요소마다 같은 SAN과 용도를 가진 `tls.crt`, `tls.key`, `ca.crt`의 `kubernetes.io/tls` Secret을 하나씩 준비합니다.

## 확장과 고가용성

- Hangang은 컨트롤러 모드에서 무상태입니다. `hangang.replicas`를 늘리면 PodDisruptionBudget과 토폴로지 분산이 자동으로 추가됩니다.
- Hopae는 SQLite 단일 복제본으로 유지됩니다. PostgreSQL 저장소가 릴리스되지 않았고, 차트는 SQLite 복제본을 둘 이상 두는 것을 거부합니다.
- Pumgye와 Sumunjang은 이번 릴리스에서 단일 기록자이며 스키마가 복제본을 하나로 제한합니다. 상태는 삭제 후에도 남는 PVC에 있습니다.

## 업그레이드와 되돌리기

Hangang World는 N-1 호환성을 따릅니다(ADR 0022 결정 6).

1. 모든 상태 PVC(Hopae, Pumgye, Sumunjang)를 충돌 일관 스냅숏으로 백업하거나, 구성 요소를 0으로 줄인 뒤 볼륨을 복사합니다. SQLite 스키마 마이그레이션은 앞으로만 진행됩니다.
2. `hangang-world-crds`를 먼저 업그레이드합니다. 제공 중인 버전 안의 CRD 변경은 추가만 하므로 실행 중인 컨트롤러는 계속 동작합니다.
3. 같은 버전의 `hangang-world`로 업그레이드합니다. 무상태 Deployment는 `maxUnavailable: 0`으로 롤링되고, 단일 기록자는 `Recreate`를 쓰므로 잠시 API를 쓸 수 없으며 그동안 게이트웨이는 보호된 트래픽에 대해 실패 시 닫힙니다.
4. 준비 상태와 `kubectl get protectionpolicies`를 확인하고, `helm test`가 통과해야 합니다.

같은 minor 계열 안에서 N-1로의 `helm rollback`을 지원합니다. 이미 데이터베이스를 마이그레이션한 구성 요소는 그 데이터베이스로 이전 버전을 실행할 수 없으므로, 마이그레이션을 넘어 되돌릴 때는 1단계의 PVC 백업을 먼저 복원하십시오. 실행 중인 컨트롤러가 요구하는 버전보다 CRD 차트를 낮추지 마십시오. minor 버전을 건너뛰는 업그레이드는 지원하지 않습니다.

## 제거

`helm uninstall world`는 워크로드를 지우고 PVC는 남깁니다(`helm.sh/resource-policy: keep`). `helm uninstall world-crds`는 CRD를, 따라서 모든 World 객체를 남깁니다. 클러스터의 모든 ProtectionPolicy를 지울 의도일 때만 명시적으로 삭제하십시오.

## 운영 설치를 아직 막는 것

- **이미지.** 어떤 구성 요소 이미지도 아직 레지스트리에 게시되지 않았습니다. 기본 저장소(`ghcr.io/ziozzang/…`)는 서명된 릴리스가 올라가기 전까지 자리표시자입니다. `tools/package_component.py`는 scratch 이미지를 로컬에서만 빌드합니다.
- **서명과 출처.** cosign 서명, SBOM, SLSA 증명이 없으므로 승인 단계 검증(policy-controller, Kyverno)을 아직 강제할 수 없습니다.
- **Hangang 버전.** ProtectionPolicy 지원(Hangang PR #21)이 digest가 가리키는 릴리스 이미지에 들어 있어야 합니다.
- **Hopae PostgreSQL.** Hopae의 PostgreSQL 저장소는 계획(Hopae ADR-0002, M2)되어 있으나 릴리스되지 않았습니다(Hopae 0.0.10은 `store.url_env`를 거부). 그 기능이 나올 때까지 차트는 `hopae.storage.backend: postgresql`을 거부하므로 Hopae는 SQLite 단일 복제본으로 실행됩니다.
- **차트 배포.** 차트는 아직 패키징·서명되거나 OCI 레지스트리에 올라가지 않았습니다.
- **실제 검증.** 로컬·원격 실행은 보호된 체인, 철회, 10분 API 중단, 인증서 회전, 노드 drain을 다룹니다. 남은 결함: Hopae/Pumgye/Sumunjang의 인증서 무중단 재로드 없음, Hangang의 API 중단 시 실패 시 닫힘 한도 없음, Hopae 선언형 철회의 롤아웃 의존.

## Hopae 인증 프로필(설정 권위 모드)

`hopae.authentication.source`의 기본값은 `config`입니다. values의 서비스 인증 프로필(`hopae.config.authentication_gateway`)과 자격 증명 projection 계획이 권위를 가집니다. 롤아웃할 때마다 Hopae의 CAS 게시(감사 행, `authentication.reconciled` 이벤트)로 저장소를 values에 맞추며, 잘못된 파일은 시작을 멈추고 저장소를 그대로 두고, 콘솔/API 편집은 `409 config_authoritative`로 거부됩니다. 설정 권위 프로필을 지원하는 Hopae 빌드(Hopae PR #13)가 필요합니다. `store`는 기존 동작으로, values는 빈 저장소만 부트스트랩하고 이후 변경은 Hopae 소유자 API로 합니다.

`store`에서 `config`로 옮기기: 현재 프로필을 내보내고(관리 리스너의 `GET /v1/authentication/profiles`), `hopae.config.authentication_gateway`에 넣은 뒤(환경 변수 참조만, 키 값은 절대 넣지 않음), Hopae PVC를 백업하고 `hopae.authentication.source: config`로 `helm upgrade`합니다. 첫 시작에서 파일이 다음 리비전으로 게시되며, values에 없는 키나 프로필은 그 시점에 제거됩니다. 되돌리려면 `store`로 설정하면 되고, 저장소는 마지막으로 맞춘 문서를 유지합니다.

## Hopae 관리와 Pumgye v2 소유자 입력

`hopae.admin.enabled`는 ClusterIP 전용 `<release>-hangang-world-hopae-admin` Service 뒤에 상호 TLS를 쓰는 Hopae 관리 리스너(8702)를 엽니다. 서버 인증서는 콘솔 호스트용으로 발급하고, 클라이언트는 각자의 World 구성 요소 인증서를 제시합니다. NetworkPolicy는 Hangang 콘솔 브로커와 Pumgye만 허용합니다. 콘솔 origin(`admin.public_url`)의 기본값은 이 Service이므로 클러스터 내부 호출자가 콘솔 호스트를 지정하게 되며, 서명된 Hangang 콘솔 위임 키는 `hopae.admin.delegation.keySecret`에서 가져옵니다.

Pumgye 정책 모델 v2는 경로 범위 읽기 전용 서비스 자격 증명(Hopae `docs/SERVICE_CREDENTIALS.md`)으로 Hopae의 서명된 멤버십 projection과 주체 수명 주기를 읽습니다. Hopae Pod 안에서 Pumgye의 SPIFFE ID에 고정해 발급하고 Secret에 저장한 뒤 `pumgye.hopaeOwner`를 켭니다.

```sh
kubectl -n hangang-world exec deploy/world-hangang-world-hopae -- \
  hopae admin service-credentials create pumgye-v2 --preset pumgye-v2 \
  --client-san spiffe://cluster.local/ns/hangang-world/sa/world-hangang-world-pumgye \
  --config /config/hopae.json > pumgye-hopae.token
kubectl -n hangang-world create secret generic pumgye-hopae-service-credential \
  --from-file=hopae-service-token=pumgye-hopae.token
```

오프라인 검증(Hopae `60b3a60`과 PR #10 `b318922`, Pumgye `775e6b9`): 두 Hopae 버전 모두 렌더링한 관리 설정을 받아들이며, `admin.service_audience`는 PR #10 빌드가 필요합니다(그 전에는 `unknown key`). PR #10 빌드로 관리 리스너를 실행하고, 발급한 자격 증명과 렌더링한 `--hopae-owner` 파일로 Pumgye를 시작하자 mTLS 연결, SPIFFE 고정, 토큰은 받아들여졌고 Hopae는 모든 호출을 `service_audience_mismatch`로 거부했습니다. 원인은 Pumgye 소유자 클라이언트가 아직 `X-Hopae-Audience`를 보내지 않는 데 있습니다. 이 경로의 Pumgye 쪽 선행 조건이며, 나오기 전까지 Pumgye는 `max_staleness_secs`가 지나면 소유자 입력에 대해 실패 시 닫힙니다. Hangang 콘솔 플러그인 바인딩(플러그인 자산과 `--admin-plugins`)은 아직 패키지에 포함하지 않았습니다.

## 검증 기록 — 일회용 로컬 클러스터 (2026-10-17)

소스 리비전: Hangang `a8e15e6`(ProtectionPolicy, PR #21), Hopae `60b3a60`
(`integrate/identity-platform`, 0.0.10으로 보고), Pumgye `775e6b9`
(`feat/model-v2-p0`), Sumunjang `321eb6d`(`feat/console-api-gaps`). 각각 정적 debug
바이너리로 빌드해 로컬에서 `FROM scratch`(UID 65532) 이미지로 만들었고, 레지스트리에는
올리지 않았습니다.

**실제 바이너리로 설정 사전 점검.** 차트가 렌더링한 파일을 각 구성 요소에 넣었습니다.
Hangang은 API에 접속하기 전에 생성된 보호 설정을 읽고 검증했습니다(minimal과 HA
프로필, PROXY v2 포함). `hopae --check`는 생성된 설정을 받아들였고(`config ok`),
`sumunjang --check`는 부트스트랩 정책과 TLS 배치를 받아들였으며, Pumgye는 생성된
부트스트랩 정책과 mTLS 파일로 시작해 `/-/ready`에 200을 응답했습니다. 차트에서 고친
점: Hopae 0.0.10은 `store.url_env`를 거부하므로 `hopae.storage.backend: postgresql`은
이제 렌더링 단계에서 실패하고 HA 프로필은 Hopae를 SQLite 단일 복제본으로 둡니다. 신원
프로필은 이제 `x-hopae-service-id`를 요청하고, Hopae의 500 ms 검증 예산을 쓰며, Hopae
세션 쿠키를 업스트림에서 제거합니다.

**클러스터 실행.** 일회용 k3d 클러스터 `hangang-world-qual`(k3s v1.31.4, 전용 Docker
네트워크, 전용 kubeconfig 파일, kube-router NetworkPolicy 강제), cert-manager v1.15.3,
`hangang-world-crds`와 `hangang-world`를 `certManager` 부트스트랩 CA, `kubernetesTls`,
`serviceLocal` 클라이언트 주소, `requireProtection: true`, 네트워크 강제 `Required`로
설치했습니다. Ingress `orders`(ProtectionPolicy: Hopae 서비스 API 키, Pumgye
`db:orders` GET→select, POST→update) 뒤에 busybox 백엔드를, 정책이 없는 Ingress
`bare`를 두었습니다.

| 점검 | 결과 |
| --- | --- |
| ProtectionPolicy 상태 | `Accepted`, `ResolvedRefs`, `Programmed`, `ClientAddressPreserved` 모두 `True` |
| 서비스 키로 GET(Hopae → Sumunjang → Pumgye) | 200, 백엔드 도달 |
| 자격 증명 없음 / 알 수 없는 키 | 401, 백엔드 미도달 |
| POST(Pumgye가 허용하지 않은 동작) | 403, 백엔드 미도달 |
| Sumunjang에서 클라이언트 IP 차단 후 해제 | 403, 이후 200 |
| Pumgye, Sumunjang, Hopae를 각각 0으로 축소 | 실패 시 닫힘 503, 전달 없음, 복구 후 200 |
| 정책 없는 Ingress | 보류(경로·인증서 없음), `ProtectionRequired`로 보고 |
| ProtectionPolicy 삭제 후 다시 적용 | Ingress 보류, 이후 다시 200 |
| 일반 Pod에서 Hopae, Pumgye, Sumunjang으로의 NetworkPolicy | 거부 |
| `helm test` | 성공 |
| 게이트웨이(복제본 2개) `kubectl rollout restart` 중 요청 60건 | 60/60 성공 |
| `helm upgrade`(모든 Pod 교체) 중 요청 120건 | 115 성공, 단일 Hopae Pod 재생성 중 503 5건 |
| 이전 리비전으로 `helm rollback` 중 요청 120건 | 116 성공, 같은 원인으로 503 4건 |

관찰: 이미지는 digest로 참조해야 합니다. 레지스트리가 없는 클러스터에서는 가져온
이미지에 containerd의 `repo@digest` 참조가 필요했으며, 레지스트리에서 받으면 이 참조는
자동으로 생깁니다. Hopae 인증 프로필은 빈 데이터베이스에만 설정에서 부트스트랩되므로,
나중에 values로 바꾸면 적용되지 않습니다(저장된 문서를 바꿀 때까지 Hopae가 시작을
거부했습니다). Hopae 소유자 API로 변경하십시오. 단일 기록자를 재시작하면 설계대로 몇 초
동안 보호된 트래픽이 실패 시 닫힙니다. 이후 클러스터, 빌드·다운로드한 모든 이미지와
빌드 디렉터리를 제거했습니다.

## 검증 기록 — 원격 k3s 게이트 (2026-10-17)

ADR 0022의 남은 게이트를 소유자 승인 아래 사용자 지정 원격 k3s 테스트 클러스터(노드 2개, k3s v1.37.1)에서 실행했습니다. 먼저 새 콜드 백업을 만들고 원격·오프호스트 사본의 크기, 전체 SHA-256, 아카이브 목록이 일치함을 확인했습니다. 이미지: Hangang `a8e15e6`(PR #21), Hopae `integrate/identity-platform` + #10 + #13 로컬 병합, Pumgye `00f0d00`, Sumunjang `321eb6d` 정적 빌드를 레지스트리 없이 두 노드에 적재했습니다. cert-manager v1.15.3을 임시로 설치했고, CRD 차트는 `rbac.aggregatedRoles=false`로 실행했습니다.

| 게이트 | 결과 |
| --- | --- |
| Pumgye 권한 철회/복원 20회, 70–90 ms 프로브 | 커밋 후 첫 거부/허용 p50 0.03초, 최대 0.05초, 0.2초 이후 불일치 표본 없음 |
| 클라이언트에 대한 Sumunjang 차단/해제 20회 | p50 0.02초, 최대 0.05초, 거부된 요청은 백엔드에 도달하지 않음 |
| `authentication.source: config`에서 Hopae 키 철회(values 변경 + 롤아웃) | `helm upgrade` 시작 4.8초 후 첫 401, 단일 Hopae Pod 재생성 중 503(실패 시 닫힘), 복원 3.7초. 실시간 철회 경로가 아닌 롤아웃이며 2초 목표를 넘음 |
| API 서버 600초 일시 정지 | 데이터 평면 8005/8005 요청 처리, 60초 staleness 이후 게이트웨이 not ready, API 복귀 7초 후 다시 authoritative, API 복귀 직후 약 0.2초 동안 4건 실패, 노드 5초 내 Ready, 기존 Pod 무변화 |
| 모든 구성 요소 인증서의 cert-manager 강제 갱신 | 새 인증서가 Pod 볼륨에 반영됨, Hopae(8703), Pumgye(9084/9087), Sumunjang(9080/9082)은 5분 넘게 이전 인증서 제공, 트래픽 2443/2443 정상, 새 인증서 제공에는 rollout restart 필요 |
| 게이트웨이 PDB를 둔 두 번째 노드 drain | PDB가 축출 1회 거부, 410/410 요청 정상, 게이트웨이 재배치 후 uncordon |
| `helm test` | 성공 |

구성 요소별 결함: **Hangang**은 API 중단 동안 마지막 정상 설정으로 무기한 서비스하며(준비 상태는 60초 후 철회), ADR 0022의 제한된 staleness를 넘으면 실패 시 닫히도록 하지 않습니다. API 복귀 시 요청 4건이 실패했고, 클라이언트 인증서 재로드는 관찰할 수 없었습니다. **Hopae**, **Pumgye**, **Sumunjang**은 재시작 없이 회전된 인증서를 다시 읽지 않습니다. **Hopae**의 선언형 철회는 롤아웃에 묶이며, #10+#13 병합 트리는 충돌 해소와 이벤트 개수 테스트(46→47, 52→53) 갱신이 필요합니다. cert-manager cainjector는 API 복귀 직후 잠시 CrashLoop 후 자동 복구됐습니다. 만든 객체, 이미지, 네임스페이스는 모두 제거했고, 노드, CRD, RBAC, webhook, IngressClass, PV 목록, HTTP 점검이 실행 전 기준선과 같으며 기존 Pod의 UID와 재시작 수가 유지됐습니다.


## 검증

```sh
python3 tools/helm/build_world_schema.py
python3 -m unittest tools/test_helm_charts.py
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py
```
