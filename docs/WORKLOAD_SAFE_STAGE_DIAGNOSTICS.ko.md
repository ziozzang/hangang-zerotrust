# 검증 전용 Workload 단계 진단

보호 HTTP 응답의 비200 body는 proxy의 고정 byte와 정확히 같을 때만 고정 enum으로 분류합니다. 알 수 없는 내용은 길이·SHA256만 남깁니다. 응답 status·시간·실패 코드는 후속 backend counter 읽기 전에 기록합니다. 200 body는 진단에 포함하지 않으며 응답 전 timeout은 응답 증거 없음으로 남습니다.

검증 tap의 pooled channel·admission·호출자 검사·1초 deadline은 그대로입니다. generic Verify에만 RAII 진단을 추가해 누적 ingress/admitted/upstream완료/cancelled 수, 제한된 시간, 고정 단계·tonicCode·reply status enum을 기록합니다. 미지 status는 other이며 요청ID·인증값·subject·응답 header/body·Status.message/details는 기록하지 않습니다. future drop 취소는 대기 중 단계를 나타내며 upstream 실행/중단을 증명하지 않습니다. 프로세스별4096 event 제한 이후 로그가 없다는 이유로 호출이 없었다고 판단할 수 없습니다. 권한 capability나 proof 예산을 변경하지 않습니다.

비밀 포함 오류/응답·미지 status·admission 거부·대기 future 취소를 단위 검증합니다. 실제 클러스터 복원/전체 경로 통과를 뜻하지 않습니다. 기존 run1/run2 실패는 유지하며 새 SDK 연결의 성공으로 기존 Root/tap 연결 복원을 주장하거나 복원 assertion을 변경하지 않습니다.

Drop에서도 진단 쓰기 오류를 무시하며 record는4096byte 미만으로 제한합니다. 검증 전용 동기 로그에는 I/O 비용이 있으며 처리량 검증을 주장하지 않습니다.

진단 tap 동결 source640a3dd487d81d908e8caedfeeb830e15357df9d, rawSHA256775a14a97c3842a9161911e4f2168195d6e19d2dc62faaaf419d513da6740806로 runner 전용 pin을 갱신합니다. 기존 held public SDK probe source/hash는 그대로이며 실제 클러스터 통과를 뜻하지 않습니다. 이전 자산은 보존합니다.

replay parser는 Verify 단계의 정확한 keyset·enum·범위 제한 정수(bool 거부)를 검증한 뒤 진단으로만 저장하고 pair 수에서 제외합니다. 알 수 없거나 잘못된 event는 계속 실패합니다. run3는 첫 Project 전에 혼합 event 호환 누락으로 실패했으며 제품 실패나 replay 통과를 뜻하지 않습니다. 이번 Python 수정은 동결 tap640 바이트를 변경하지 않습니다.
