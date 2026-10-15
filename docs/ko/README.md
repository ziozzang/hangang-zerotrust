# 설계 목차

[English](../README.md) · [프로젝트](../../README.ko.md)

- [전체 구조](ARCHITECTURE.md)
- [카탈로그·정보등급](CATALOG.md)
- [분류 엔진](CLASSIFICATION.md)
- [통합 판단 엔진](DECISIONS.md)
- [네이티브 인증](IDENTITY.md)
- [공통 콘솔](CONSOLE.md)
- [고속 프로토콜](PROTOCOLS.md)
- [로깅·모니터링](OBSERVABILITY.md)
- [단말·워크로드](DEVICES.md)
- [위협 모델](THREAT_MODEL.md)
- [구현 순서](ROADMAP.md)


[Sillok·Jikji 보안 자동화 설계](AUTOMATION.md)

[관측·온톨로지·펜테스트 피드백 루프](FEEDBACK_LOOP.md)

[스냅샷 백본과 스케일아웃 멤버십](0013-snapshot-membership-scaleout.md) — 도메인 스냅샷·lease·합류/드레인/제거·Hangang 구독.

[Kubernetes·IAM 원천 설계](0015-kubernetes-iam-authority.md) — 네 모듈 원천 연동·RBAC·워크로드 신원.

[판정 코어·메타데이터 어댑터](0016-decision-core-metadata-adapters.md) — 타입 자원·DB 백본·선택적 플러그인.

[권한 소유자 기준 시간 관측 초안](0018-authority-time-observations.md) — 교차 호스트 시계·집행 하한·replay 보존 상한.

[Workload K3s 검증 준비](WORKLOAD_WORLD_QUALIFICATION.md) — 선택적 네이티브 실행 소스와 순수 테스트이며 실제 실행은 미검증·최종 artifact 승인 대기입니다.
