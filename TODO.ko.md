# 구현 과제

[English](TODO.md) · [구현 순서](docs/ko/ROADMAP.md)

주 작업: 운영 Hangang 콘솔의 실제 Guard 메뉴, 플러그인 권한/회수/감사 검증,
Hopae 관리 위임과 사용자/세션/이벤트 메뉴, HTTP 의미와 같은 고속 verify 프로토콜,
Hangang 네이티브 로그인·로그아웃, 호환 컴포넌트 검증·릴리즈입니다. Hangang/Guard는 서명 자산, Hopae는 체크섬 자산을 게시했습니다.

Hangang 통합 권한과 명시적 계정 매핑을 통한 SSO 로그인은 [ADR 0009](docs/ko/ADR_0009.md)에 기록했습니다.

설계 서브태스크: 전체 구조·소유권 도표와 영어/한국어 문서, 카탈로그·분류·통합 판단·exporter 제안을 구성했습니다.
등급·테넌트/객체 증거·하향 승인, 프로토콜과 위임/회수 보장, 실제 엔진/exporter 구현은 남아 있습니다.
단말/워크로드는 환경 조사 후 ADR로 결정합니다. 문서가 작성되었다고 런타임 구현을 완료 처리하지 않습니다.

## 온톨로지 및 자동 보안 강화
- [x] Sillok/Jikji 선택과 펜테스트→Guard→Hangang 대응 설계 기록.
- [ ] Sillok 버전·작업량 제한 어댑터, 출처·테넌트 격리.
- [ ] Jikji 자동·반자동 도구/승인 통합.
- [ ] 제한된 펜테스트 작업과 취약점 근거 계약.
- [ ] Guard 대응·Hangang 라우팅 패치 CAS/멱등 어댑터.
- [ ] 영속 복구·카나리 검증·충돌 안전 롤백.
- [ ] 공격적 검증과 일반 요청 성능 격리.

## 관측 / 온톨로지 / 펜테스트 피드백
- [x] 관측→대응→검증→재사용 루프 영어·한국어 설계 기록.
- [ ] 제한된 로그/트레이스/메트릭·펜테스트 근거의 출처 기반 상관 분석.
- [ ] Sillok 사실/가설/정책/적용 상태/결과 구분과 근거 철회.
- [ ] Jikji case 수명주기·근거 검색·제한된 결과 재사용.
- [ ] 사전 기준에 따른 적용 후 재펜테스트·정상 트래픽 회귀 검증.
- [ ] 피드백 증폭·허위 성공·테넌트 혼합 공격적 검증.

- [x] Hearim 지능·판단 백엔드 선정 및 다이어그램 갱신.
- [ ] 제한된 Jikji/Hearim 어댑터·출처·장애 처리·보정 검증.

## 통합 구현 근거 — 2026-10-12

Hangang/Hopae/Guard PR #1을 모두 머지했습니다. Native 메뉴·host 인증·위임 및 HOP1 지속 연결을 구현하고
기존 provider/session/grant/CSRF/fence를 유지합니다. 영어 TODO에 테스트 수와 근거를 기록했습니다.
운영 콘솔 활성화·플랫폼 릴리즈 검증·Hopae 전체 처리량 측정은 별도 완료 항목입니다.

- [x] 운영 HTTPS 두 메뉴·익명 거부·네이티브 진입 리다이렉트·로그아웃 정리·Guard 서명 updater 확인.
- [x] 네이티브 플랫폼 검증·게시 완료: Hangang 5개, Guard 4개, Hopae 4개 대상.

2026-10-13 게시·배포: [Hangang v0.3.1](https://github.com/ziozzang/hangang/releases/tag/v0.3.1), [Guard v0.3.1](https://github.com/ziozzang/hangang-guard/releases/tag/v0.3.1), [Hopae v0.0.2](https://github.com/ziozzang/hopae/releases/tag/v0.0.2). 배포 전 Hangang/Guard 서명과 Hopae 체크섬을 검증했습니다. Guard 감독형 서명 자동 업데이트는 활성화했습니다. Hopae 서명 자동 updater는 구현하지 않았습니다.

- [ ] Hopae 전체 세션 처리량 측정; 전송 검증을 100k QPS 근거로 사용하지 않음.

## 통합 콘솔·SSO 근거 — 2026-10-13

[Hangang #4](https://github.com/ziozzang/hangang/pull/4)와
[Hopae #2](https://github.com/ziozzang/hopae/pull/2)를 머지했습니다. 검토·테스트한 Linux
빌드와 고정 Hopae UI 0.1.2를 운영에 적용했습니다. 기존 릴리즈 이후 기능 배포이며,
새 크로스플랫폼 서명 릴리즈를 게시한 것은 아닙니다. 현재 단일 Hopae 관리자를 기존
활성 Hangang 관리자에 명시적으로 연결했으며 계정/grant를 생성·변경하지 않았습니다.

Hangang 관리자 API 89개·private lease/native SSO·실제 broker 검증,
Hopae unit 384개·시나리오 359개(명시적 제외 40개), strict Clippy·문서/경계/게시 검사,
브라우저 버튼 위치·복귀·viewer 역할/복구·플러그인 권한 검증을 통과했습니다.
운영 HTTPS에서 ID/PW+SSO 버튼, Hangang 로그인만으로 Hopae 상태/사용자 조회,
추가 로그인 제거, 로그아웃 정리, 익명/origin/쿠키/lease 우회 거부,
네이티브 provider 진입 리다이렉트를 확인했습니다. 실제 Google 로그인은 운영자의
프로바이더 인증 동작이 필요하며 자동 로그인 검증에는 소유한 mock provider/session을 사용합니다.
