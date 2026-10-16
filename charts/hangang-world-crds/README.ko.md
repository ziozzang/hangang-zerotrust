# hangang-world-crds Helm 차트

[English](README.md) · [설치 안내](../../docs/ko/HELM_INSTALL.md)

`world.hangang.dev` API 그룹의 CustomResourceDefinition과 ADR 0022의 집계 ClusterRole입니다. Helm은 차트의 `crds/` 디렉터리를 업그레이드하지 않으므로 [`hangang-world`](../hangang-world)와 분리했습니다. 여기서 CRD는 일반 템플릿이므로 `helm upgrade`가 갱신하며, 두 차트는 같은 버전으로 함께 움직입니다. 이 차트를 먼저 설치하거나 업그레이드하십시오.

| 객체 | 비고 |
| --- | --- |
| `protectionpolicies.world.hangang.dev` (v1alpha1) | 구조적 스키마, CEL 규칙, status 하위 리소스. Hangang `deploy/kubernetes/crds`와 같은 정의 |
| `world-admin` | World 객체 전체 제어, `admin`에 집계 |
| `world-editor` | World 객체 생성·변경(status 제외), `edit`에 집계 |
| `world-viewer` | World 객체와 status 읽기, `view`에 집계 |

| 키 | 기본값 | 의미 |
| --- | --- | --- |
| `keep` | `true` | CRD에 `helm.sh/resource-policy: keep`, 제거해도 World 객체를 지우지 않음 |
| `protectionPolicy.enabled` | `true` | ProtectionPolicy CRD 설치 |
| `rbac.aggregatedRoles` | `true` | 집계 역할 설치 |

Hangang 저장소의 kustomize `deploy/kubernetes/crds`와 이 역할들을 함께 설치하지 말고 한 가지 원천만 쓰십시오.
