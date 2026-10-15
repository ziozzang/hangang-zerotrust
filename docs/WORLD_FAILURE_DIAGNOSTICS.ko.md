# 소유한 world 실패 진단

실제 runner는 정리 전에 생성한 namespace UID 및 Pod UID, phase, 제한된 컨테이너 state/lastState·재시작 수·image ID를 보존합니다. 캡처한 Pod UID를 재확인한 뒤 컨테이너별 현재/이전 로그를 제한된 길이로 읽고, 알려진 fixture 토큰·개인키·JWT를 가립니다. Secret/config/env 객체는 읽지 않습니다. Pod 교체나 로그 소실은 증거 없음으로 남습니다. 로그 API에 UID 전제조건이 없으므로 마지막 확인 이후 교체 경쟁은 남으며, 로그를 권한 증거로 사용하지 않습니다.

정리는 port-forward·namespace·생성 CRD 각각을 시도하고 실패 후에도 기존 node UID/Ready와 Pod UID/phase를 비교합니다. 정리나 증거 저장 실패가 최초 예외를 덮지 않습니다. 정상 검증 뒤 정리/기준선 검사가 실패하면 실행은 실패합니다. 기준선 비교는 단일 시점 검사이며 데이터·컨테이너 건강 불변을 증명하지 않습니다. 합성 Retain PV는 기존 의미를 유지합니다. 로그 캡처는 최선 노력이며 전체 이력이 아닙니다.

진단만 변경하며 보호 요청 재시도, assertion·selector·proof 예산·기존 작업 timeout은 변경하지 않습니다. 순수 오류 주입 테스트는 예외 우선순위·정리 계속·UID 거부·이전 로그·비밀 가림·기준선 실패를 검증합니다. 실제 클러스터 통과를 뜻하지 않습니다.

로그 읽기 후 namespace 또는 Pod UID가 달라지면 내용을 저장하지 않습니다. 일반 namespace 삭제에도 원자적 UID/resourceVersion 전제조건을 적용하며, 앞선 종료 실패에도 모든 소유 port-forward 프로세스의 정리를 시도합니다.
