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

## 추가 gRPC 어댑터 방향

[ADR 0016](0016-decision-core-metadata-adapters.md)은 같은 판정 코어를 사용하는
버전별 타입 전송으로 gRPC를 추가 제안합니다. 채널 재사용·제한된 메시지와
deadline·mTLS·네이티브/gRPC 의미 일치가 필수입니다. Kubernetes API 서버
webhook은 HTTP/JSON 변환을, Envoy ext_authz는 별도 호환 검증을 요구합니다.
이 설계 수정만으로 gRPC 서버나 플러그인을 제공하지는 않습니다.

## 검증된 네이티브 판정 원천 관측

추가 gRPC 전송은 구현되어 있으며 소유권과 반영 근거는
[ADR 0017](0017-shared-server-runtime.md)에 기록합니다. 품계의 타입화된
AuthenticatedResourceAuthorization/Decide는 JSON 문맥 바이트 대신 호패의
공용 protobuf receipt 문맥을 사용합니다. 실제 호패·수문장 원천에 질의한 뒤
TTL 0 자원 판정을 반환합니다. 유지하는 로컬 테스트에서 실제 한강 클라이언트를
세 서버의 지속 mTLS 연결에 연결해 인증/네트워크 회수·복원·장애·신뢰 거부를
검증했습니다.

한강 연결 계층은 라우트 소유 자원/메서드 범위·IP·최종 요청 digest·불투명한
검증 서비스 receipt를 받습니다. 이 endpoint의 신원·AAL·네트워크 판정은
질의자가 지정하지 않습니다. 직접 호패 검증 클라이언트는 정확한 receipt를
소유 원천에 재확인합니다. 두 결과는 관측이며 서명 권한/변환 permit이 아닙니다.
새 타입 클라이언트 경로는 미릴리스이며 운영 게이트웨이 전달에는 미연결입니다.

전달 연결은 backend URI 합성 이후의 최종 origin-form target·변환된 본문에
바인딩하고 라우트/설정 소유권을 유지하며 서비스 자격을 소비하고 upstream 효과
이전에 오래된 원천을 거부해야 합니다. 캐시 응답과 재시도도 같은 인증 계약이
필요하며 변환 전의 기존 auth-proxy 검사는 최종 요청 바인딩을 대신할 수 없습니다.
정적 패키징·새 타입 endpoint의 Kubernetes 검증·서명 permit/변환/재사용 방지
검증은 후속 작업입니다.
