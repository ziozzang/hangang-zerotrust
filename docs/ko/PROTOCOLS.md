# 네이티브 런타임 고속 프로토콜

[English](../PROTOCOLS.md) · [목차](README.md)

Guard와 Hopae는 별도 런타임이며 Hangang이 인증된 지속 연결 풀을 사용합니다.
서비스 인증·버전·메시지 타입·요청 ID·크기·기한·수용량·취소·종료를 명시합니다.
원격은 인증된 전송을 사용하며 같은 호스트의 루프백이라고 아무 프로세스를 신뢰하지 않습니다.
연결을 인증한 뒤에도 각 요청의 현재 권한을 검증합니다.

Guard는 현재 24바이트 IP 프레임과 HTTP 관리/신호 경로를 유지합니다.
Hopae는 앱·호스트·메서드·경로·클라이언트 문맥·쿠키/토큰 등을 검증하므로 같은 크기 프레임에 넣을 수 없습니다.
고정 헤더와 제한된 가변 페이로드로 설계하고 정확한 바이너리 레이아웃은 ADR로 확정합니다.
초기 JSON 페이로드로 HTTP와 의미를 맞춘 뒤 측정 결과에 따라 타입 코덱을 최적화할 수 있습니다.

프로바이더 독립 계약 추출 → 공통 verify 엔진의 HTTP/native 골든 사례 → 인증된 프레임/취소 →
Hangang 연결 풀/네이티브 로그인·로그아웃 → 회수/장애/파서 검증 → 최적화 순서로 갑니다.
고속 경로가 앱 바인딩·신원 검증·step-up·쿠키 처리·회수 절차를 생략하면 안 됩니다.

10k/100k QPS는 검증 목표입니다. 로컬 warm 검증과 외부 프로바이더 왕복을 구분하고
전체 게이트웨이 경로의 지연·오류·CPU/RSS·회수 지연을 실제로 보고해야 합니다.

구현된 HOP1은 [Hopae 계약](https://github.com/ziozzang/hopae/blob/main/docs/HANGANG_NATIVE.md)과
[Hangang 계약](https://github.com/ziozzang/hangang/blob/main/docs/CONSOLE_PLUGINS.md)에 정의합니다.
16바이트 magic/u64-ID/u32-length 프레임과 제한된 헤더/응답을 사용하며 앞선 임시 프레임 설계를 대체합니다.
연결 인증 뒤 매 요청에서도 기존 라우터가 caller·세션을 확인합니다. 전체 identity 처리량은 별도 검증입니다.
