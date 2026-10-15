# 네이티브 권한 후속 작업 — 2026-10-15

[English](../reviews/2026-10-15-native-authority-followup.md)

## 운영 콘솔 패키지

수문장 [console-plugin-v0.1.4](https://github.com/ziozzang/sumunjang/releases/tag/console-plugin-v0.1.4)는 `d314d873a27d52d4a5fec981182f8118daeaf1f3`을 대상으로 한다. 초안·공개 파일3개의 바이트 일치를 확인했고 최신 서버 릴리즈는 v0.3.6을 유지했다. 호패 UI0.1.6은 공개 v0.0.10의 패키지와 일치한다. 운영 한강0.3.10에 두 불변 패키지와 manifest 해시를 설치했다. 백엔드 연결·프로세스 인자/unit/환경·코어 바이너리·정책/프로필 문서는 유지했고 비공개 registry 백업·사전 검사를 수행했다.

첫 설치는 검증기가 systemd의 동적 실행 시각/PID까지 비교해 기존 registry로 복구했다. 고정 unit 정의와 실제 실행 인자를 비교하도록 수정한 별도 재시도가 통과했으며 실패 기록도 보존했다.

운영 브라우저에서 두 패키지의 EN/KO 실제 문구 변경·DOM root 유지·앞/뒤 탐색·390px 화면 가로 넘침 없음·페이지 오류 없음·플러그인 API GET 전용·로그아웃 정리를 확인했다. 소유한 관리자 세션 검사이며 모든 외부 인증 로그인이나 앞선 사용자별 SSO 증상을 검증한 것은 아니다.

비공개 근거: `/tmp/console-plugin-014-016-final-handoff.json`, `/tmp/console-plugin-014-016-upgrade-result.json`, `/tmp/console-plugin-014-016-browser-result.json`, `/tmp/sumunjang-plugin-014-publication/release-roundtrip.json`. 브라우저 산출물도 비공개이며 자격증명·배포 설정은 문서에 넣지 않는다.

## 운영 버전과 구분하는 병합 소스

호패 `bc64e41`은 실제 OTP 성공과 정확한 원래 인증 근거를 같은 트랜잭션에 기록하며 과거 세션의 근거를 소급 생성하지 않는다. 최종 전체1,071 통과·기존42개 제외·strict Clippy·독립 검토를 완료했다. 처음의 기존 Workload SDK 거부는 원인 미확정으로 보존했고 개별·직렬·최종2스레드 통과가 원인을 설명하지 않는다. schema8 소스는 운영0.0.10에 포함되지 않으며 Human 관측 권한 자체가 아니다.

품계 `e28d483`은 내부 v1 SAR 해석기를 추가했다. 원본 바이트 크기·깊이·모든 위치의 중복 키를 검사하고 기존 코어로 정확하게 신원/속성을 전달한다. 미지원 입력은 명시적 거부이며 응답은 입력을 반사하지 않는 상수다. 기본116/전체125·양쪽 strict Clippy와 같은 코어 권한 철회를 검사했다. fixture는 공개 Go 스키마에서 구성했으며 실제 API-server 요청 캡처가 아니다. 리스너·호출자 인증·클러스터 선택·풀링 정책·최종 전송 신선도 보장은 아직 활성화하지 않았다.

다음 경계는 실제 컴파일 provider 소유권과 Engine/Human 원천·시계 연결, 그리고 같은 네이티브 뷰·최종 응답 경계·재사용 연결을 갖춘 인증 SAR 서버다. 나머지 인증·수명주기/복구·메모리 복제·장기 회수·실측 성능도 남아 있어 전체 목표는 진행 중이다.
