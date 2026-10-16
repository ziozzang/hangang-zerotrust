# Helm으로 Hangang World 설치하기

[English](../HELM_INSTALL.md) · [설계 목차](README.md) · [차트 참조](../../charts/hangang-world/README.ko.md)

이 안내는 통합 Hangang World 패키지(ADR 0022 P0 패키징)를 설치합니다. `hangang-world` 차트로 Hangang, Hopae, Pumgye, Sumunjang을, `hangang-world-crds` 차트로 `world.hangang.dev` CRD를 설치합니다. 차트는 오프라인으로 검증했습니다(`helm lint`, 여러 프로필의 `helm template`, Kubernetes·cert-manager·Prometheus Operator 스키마 검증, 렌더 테스트). 아직 클러스터에 **설치해 보지는 않았습니다**. [운영 설치를 아직 막는 것](#운영-설치를-아직-막는-것)을 참조하십시오.

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
- Hopae는 `hopae.storage.backend: postgresql`, `global.ha.backend: postgresql`, 연결 URL을 가진 Secret이 있을 때 늘어납니다. 차트는 SQLite 복제본을 둘 이상 두는 것을 거부합니다.
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
- **Hopae PostgreSQL.** Hopae의 PostgreSQL 저장소는 계획(Hopae ADR-0002, M2)되어 있으나 릴리스되지 않았습니다. HA 프로필은 문서에 정의된 설정을 렌더링하며, 그 기능이 나오기 전까지 Hopae 설정 검사에서 실패합니다.
- **차트 배포.** 차트는 아직 패키징·서명되거나 OCI 레지스트리에 올라가지 않았습니다.
- **실제 검증.** ADR 0022 기능 게이트(보호된 요청 체인, 철회 SLO, API 중단, 인증서 회전)를 차트로 실행하지 않았습니다. 인증서 회전에는 각 구성 요소가 재시작 없이 파일을 다시 읽는 기능이 필요합니다.

## 검증

```sh
python3 tools/helm/build_world_schema.py
python3 -m unittest tools/test_helm_charts.py
WORLD_KUBECONFORM=1 python3 -m unittest tools/test_helm_charts.py
```
