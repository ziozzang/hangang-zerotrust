# 실제 소유 Service/browser 검증

현재 Rootf45 실제 browser helper와 기존039 ADM04 검사를 결합한 도구입니다. API 응답을 가로채 만들어 주거나 browser clock을 바꾸지 않습니다. 최신 ZT runner의 소유권·UID·백업 경계를 유지합니다.

양쪽 검토된 plugin package와 전체 observed Service 인자에 `--browser-probe <이디렉터리>/world_admin_browser.mjs --host-navigation --plugin-locale --pumgye-responsive`를 사용합니다. WorkloadUI로 세지 않으며 --workload와 결합하지 않습니다. host navigation은 실제 컴파일 UI의 권한 소유자 순서·ENKO 메뉴·품계 section주소/이력·검색·미설치 경로 거부를 검사합니다. locale은 실제 Hop profile/Sum 진단 초안 DOM 동일성·미저장 값·번역·추가 원천 호출 없음·native read-only 제어 유지를 확인합니다. 값을 복원하며 이 locale 단계는 원천 policy/profile을 게시하지 않습니다.

기존 전체 browser 단계의 계정·grant·CRD block·profile CAS/재시작/복구 작업은 승인된 소유 fixture 안에서만 수행합니다. 클러스터 실행은 부모 담당입니다. Node/Playwright/Chromium이 필요하며 독립 checkout의 disposable node_modules 연결은 ignored 처리하고 커밋하지 않습니다. gateway는 /ui를 내장하므로 sidecar가 필요 없습니다. 독립 hangang-console proxy/SSO는 별도 게이트입니다.

로컬 Node contract/Python fake 테스트는 helper 불변식/CLI만 검사하며 실제 통과로 세지 않습니다. 실제 실행 시에만 live PASS를 출력합니다. in-flight publish/권한 철회·취소 locale race와 실제 Workload policy UI는 별도 후속 fixture입니다. mocked API 테스트로 이 게이트를 대체하지 않습니다.

Sum의 정상5초 polling과 locale 유발 요청을 혼동하지 않도록 mount 완료 뒤 일반 host 탐색으로 패널을 숨겨 pause하고, 숨겨진 cached DOM의 locale 반영을 확인한 뒤 다시 표시합니다. 가상 clock/네트워크 가로채기는 없습니다.
