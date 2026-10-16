# 구현 순서와 완료 기준

[English](../ROADMAP.md) · [목차](README.md)

주 작업은 실제 Hangang 메뉴에 Guard 통합 → Hopae 관리 위임과 메뉴 →
Hopae 네이티브 프로토콜과 Hangang 로그인·로그아웃 지원 → 검증·호환 릴리즈입니다.
도메인만 연결하거나 메뉴 자리만 만들었다고 완료 처리하지 않습니다.
운영 데이터 평면을 디버그 바이너리로 교체해 시연하지 않습니다.

설계 서브태스크는 카탈로그/정보등급 스키마 → 분류 컴파일러 → 통합 판단 엔진입니다.
exporter/Prometheus/ClickHouse 설계는 병행하고 단말·워크로드는 환경과 증거 요구를 결정한 뒤 진행합니다.

필요 산출물: 플러그인 계약/회수 테스트, Hopae 위임 ADR와 grant/CSRF 호환 테스트,
HTTP/native 공통검증 코퍼스, 네이티브 인증 진입점/복귀주소·로그아웃 범위 테스트,
카탈로그/정책/번들 스키마와 부정 예제, 분류 충돌/한도/성능,
exporter 유실·재전송·개인정보·저장 장애 시험, 통합정책 판정표와 게시/롤백 감사입니다.

10k/100k QPS는 실제 조건과 오류·지연·자원·회수 지연을 포함해 검증합니다.
상태는 계획 → 설계 → 시제품 → 보안검토 → 검증 → 릴리즈 → 운영관찰로 구분합니다.

인가 모델·Kubernetes 패키지 트랙(제안, [ADR 0021](0021-pumgye-authorization-model-revision.md)·[ADR 0022](0022-kubernetes-native-world-package.md)):
P0은 품계 정책 v2(주체·그룹·템플릿·바인딩, deny, zone 참조, clearance 상한, 유효 기간, trace 동치 explain,
v1→v2 변환기·shadow), 호패 그룹·멤버십 projection·주체 생명주기 피드·오프라인 JWKS 워크로드 검증과 tombstone,
수문장 `NetworkZone`/`NetworkControl`, `world.hangang.dev` v1alpha1 CRD와 서명 스냅샷·제한 staleness·빠른 회수를 갖춘
`hangang-world-controller`, 클라이언트 IP를 보존하는 한강 Gateway API·`ProtectionPolicy`, cert-manager mTLS,
digest 고정 서명 이미지의 Helm/OCI 차트입니다. 게이트는 새로 검증한 백업 이후 지정 원격 k3s에서 차트로 설치한
기능 인수이며 기능 게이트 통과 전 부하 시험은 하지 않습니다.
P1은 HA(PostgreSQL, N≥2, PDB), 업그레이드/롤백, v1beta1·변환, CNI 정책 생성, SPIFFE SVID, 콘솔·판정 이벤트(ADR 0019/0020),
백업/복구 훈련, Gateway API 적합성입니다. P2는 JIT·접근 검토, 다중 클러스터, 동서 L7, SAR authorizer 재설계,
10k/100k 전체 경로 부하 검증입니다.
