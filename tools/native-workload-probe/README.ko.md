# 네이티브 Workload 인증 검증 도구

고정 Git 버전의 공개 호패 SDK로 mTLS Workload 발급·독립 관측·소비형 refresh를
검사한다. 리소스 권한이나 gateway 전달을 허가하는 도구가 아니다. 빌드만으로 실제
원천 검증이 완료된 것은 아니다. 자세한 인터페이스는 [영문 문서](README.md)를 따른다.

비공개 설정에는 고정 endpoint·TLS 파일·공개 pin·scope·revision floor·클록 가정과
요청 바인딩을 넣는다. 실제 자격은 OWNED_RECEIPT_CALLER와 OWNED_RECEIPT_CREDENTIAL
환경변수로만 전달한다. Bearer만 허용한다. 기본 fixture scope는 orders/orders-api,
authority는 world1이다.

실행 파일에 비공개 설정 경로를 주고 표준입력 allow/deny로 기대 결과를 지정한다.
성공한 SDK의 subject_ref/kind3/AAL0를 실제 Kubernetes 신원과 교차 확인한 뒤 품계
소유 API에 권한을 게시한다. deny는 SDK Issue 거부이며 어느 원천이 거부했는지까지
입증하지 않는다. 실제 TokenReview·품계·재사용 방지·최종 전송 검증을 따로 수행한다.
