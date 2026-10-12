# Hangang Zero Trust

[English](README.md) · [설계 목차](docs/ko/README.md)

Hangang·Hopae·Guard를 기반으로 전체 제로트러스트 구조와 계약을 설계하는 저장소입니다.

- Hangang: 요청 집행, 리소스 접근 제어, 공통 관리 콘솔, 네이티브 로그인·로그아웃 진입점.
- Hopae: 사용자·세션·외부 인증 프로바이더. Google/OIDC 처리는 Hopae에 유지합니다.
- Guard: IP/CIDR/ASN 제어와 네트워크 위험.
- 카탈로그·분류 엔진: API·리소스·데이터의 정보등급과 정책 속성.
- 통합 판단 엔진: 신원·네트워크·리소스·확인 가능한 단말/워크로드 근거를 결합합니다.
- 관측 exporter: Prometheus 지표, ClickHouse 이벤트 분석.

현재는 **설계 문서와 계약 예제**입니다. 전체 구현 완료나 운영 검증을 의미하지 않습니다.
단말·워크로드는 추가 고민이 필요한 항목으로 남깁니다.

문서는 영어가 기준이며 한국어 번역을 함께 관리합니다.
