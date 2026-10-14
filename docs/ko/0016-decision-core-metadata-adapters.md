# ADR 0016: 도메인 판정 코어·메타데이터 백본·플러그인 어댑터

[English](../adr/0016-decision-core-metadata-adapters.md)

상태: 채택한 방향입니다. 범용 메타 테이블, Kubernetes의 역방향 판정 위임과
DBMS 집행 어댑터는 미구현입니다. 현재 품계 서비스 매트릭스, 호패 인증과
수문장 네트워크 판정이 기존 구현 기준입니다.

## 판정 소유권과 저장

호패·품계·수문장은 다른 시스템의 정책을 가져오는 역할을 넘어 판정 코어입니다.
한강·Kubernetes·DBMS 등 집행 클라이언트가 인증된 어댑터로 코어에 질의합니다.
백엔드 DB는 영속 메타데이터 원천이며 각 코어가 검증·컴파일한 메모리 뷰를
게시합니다. 저장 원천과 판정 권위는 구별합니다. Kubernetes 원천 모드를
선택해도 도메인 판정 소유권을 Kubernetes RBAC로 대체하지 않습니다.

기본 경로는 DB 메타데이터 → 백그라운드 검증·컴파일 → 불변 메모리 스냅샷 →
판정 → 집행입니다. 실록은 선택적 온톨로지 연결기이며 필수 저장소나 요청 중
동기 판단 의존성이 아닙니다. 분석·LLM·자동화가 소유자 검증 없이 권한 테이블에
직접 쓰지 않습니다. 도메인별 단일 작성자를 유지하고 업무 테이블 다중 쓰기를
도입하지 않습니다. 메타데이터의 자격은 비밀값 대신 참조로 표현합니다.

| 소유자 | 논리 메타 관계 | 판정 |
| --- | --- | --- |
| 호패 | 신원·프로바이더·자격 참조·바인딩·세션·인증 수준 | 검증된 신원과 제한된 근거 |
| 품계 | 주체·자원·행위·역할·할당·등급·조건·원천 바인딩 | 자원·행위·문맥의 권한 |
| 수문장 | 네트워크 prefix·네트워크 신원·위험 사실·규칙·범위·유효기간 | 네트워크 허용과 위험 근거 |
| 한강 | 라우트·집행 참조·어댑터 바인딩 | 검증한 코어 판정 집행 |

이는 요청마다 범용 그래프를 탐색하는 구조가 아니라 관계를 가진 결정적 모델입니다.
하나의 공유 물리 SQL 스키마를 지정하지 않습니다. 각 백엔드 구현 전에 migration,
외부 참조, tenant/도메인 소유권과 트랜잭션 revision/outbox를 정의합니다. 요청 실행기
밖에서 일관된 commit을 읽고 delta 또는 전체 재구축을 적용한 완전한 후보만
원자적으로 교체합니다. 부분·실패 후보는 권한이 아닙니다. 재접속·알림 누락·복제본
시작에는 epoch/revision 재조정과 제한된 신선도가 필요합니다.

## 자원 추상화와 어댑터

품계 자원은 서비스/라우트 ID에 한정하지 않습니다. API 행위, Kubernetes 객체와
하위 자원, DB·schema·table 등 명시적으로 지원하는 타입을 카탈로그에 바인딩합니다.
자원 생애 식별자, tenant, 행위 어휘, 등급과 요구 근거는 소유자가 정의합니다.
이름만으로 객체 재생성 후 신원을 유지하지 않습니다. 현재 HTTP 전용 draft
카탈로그 바인딩과 서비스 중심 런타임은 버전을 올려 확장해야 합니다.

어댑터는 검증된 플랫폼 문맥을 제한된 타입 요청으로 변환해 코어를 질의하고
응답을 집행합니다. 같은 프로세스는 불변 스냅샷의 순수 코어를 직접 호출할 수
있으며 분산 연결은 인증된 pooled 바이너리 전송을 사용합니다. 지원 자원·행위·
의무, 신뢰 문맥 원천, peer 신원, revision, 능력과 실패 모드를 선언합니다.
미지원 매핑·불신 속성·집행 불가능한 의무는 거부합니다. 플러그인이 클라이언트의
역할·등급·IP 주장에 권위를 부여하지 않습니다. ABI·버전·로딩 제한·격리·수명주기는
별도 계약이 필요합니다.

임의 자원을 추측한 서비스 ID로 바꾸거나 기존 프로토콜에 맞추려고 IP를 만들지
않습니다. 원래 클라이언트 네트워크 문맥이 없으면 근거 부재로 표시합니다.
필수 근거 정책은 거부하고 다른 범위는 다른 근거를 명시적으로 선택해야 합니다.
행·열 필터와 마스킹은 타입 의무와 집행 능력이 필요하며 boolean allow만으로
적용했다고 주장하지 않습니다.

## Kubernetes의 판정 질의

호패의 TokenReview 인증 webhook 어댑터와 품계의 SubjectAccessReview 인가
webhook 어댑터를 검토합니다. 수문장은 적용 가능한 네트워크 근거를 제공합니다.
Admission·CNI는 별도 연결 지점이며 읽기 권한 집행을 대신하지 않습니다.
기존 호패의 외부 TokenReview 조회와 품계 RBAC 수집은 역방향 webhook 구현이 아닙니다.

앞선 RBAC Allow가 뒤의 webhook을 우회할 수 있어 보호 범위의 authorizer 순서와
명시적 실패 거부가 집행 계약에 포함됩니다. API 서버 캐시는 짧게 또는 비활성화해
회수 요구를 지킵니다. webhook은 원래 클라이언트 IP를 자동으로 받지 않습니다.
API 서버 peer IP를 대신 쓰거나 unsigned user.extra를 신뢰하지 않습니다. 호패의
토큰 검증이 API 서버 webhook으로 다시 호출되는 루프도 방지합니다. 기존 클러스터
플래그 변경 전에 제어면 bootstrap·복구를 별도로 검증해야 합니다.

근거: [Kubernetes 인가](https://kubernetes.io/docs/reference/access-authn-authz/authorization/),
[인가 webhook](https://kubernetes.io/docs/reference/access-authn-authz/webhook/),
[토큰 인증](https://kubernetes.io/docs/reference/access-authn-authz/authentication/).

## PostgreSQL 및 DBMS 연결

PostgreSQL은 메타데이터 백본이며 별도로 집행 대상이 될 수 있습니다. 호패의
접속 인증에는 OAuth validator, 품계의 객체·행위 권한에는 executor/utility hook,
테이블·행·열 의무에는 GRANT/RLS 또는 검증한 확장을 검토합니다. 수문장 접속
근거와 DB 역할은 구별합니다. 프로토콜 proxy도 어댑터 선택지이나 모든 SQL
실행을 가로챈 증명이 되지는 않습니다.

행마다 원격 코어를 호출하지 않습니다. 수용한 필터를 DB의 plan/policy로
컴파일하고 적절한 statement/transaction 경계에서 판정합니다. prepared statement,
역할 변경, pooling, 함수·view·DDL·COPY와 긴 트랜잭션 중 회수를 검증합니다.
PostgreSQL superuser/BYPASSRLS/소유자 동작도 집행 범위에 포함해야 합니다.
DB 자체가 거부한 권한을 어댑터가 조용히 넓히지 않습니다. 이 ADR은 PostgreSQL
플러그인이나 실제 DB 집행 구현을 제공하지 않습니다.

근거: [OAuth validator](https://www.postgresql.org/docs/18/oauth-validator-design.html),
[RLS](https://www.postgresql.org/docs/18/ddl-rowsecurity.html),
[executor 권한 hook](https://github.com/postgres/postgres/blob/master/src/include/executor/executor.h).
지원 DBMS major 버전을 고정·검증하며 hook ABI가 고정이라고 가정하지 않습니다.

## 추가 gRPC 전송

gRPC는 HOP1/PPG1/HGD1·동일 프로세스 호출과 함께 같은 도메인 코어와 스냅샷을
사용하는 타입 전송입니다. 이 ADR에서 구현된 것은 아닙니다. 인증·인가·네트워크
근거의 버전별 protobuf 서비스를 정의하고 제한된 메시지, 명시적 사용 불가·거부·
허용, 신뢰 호출자·근거 바인딩, 최소 revision과 만료를 포함합니다. 미지정·기본
필드가 권한이 되지 않으며 관리·정책 쓰기는 분리합니다.

HTTP/2 채널 재사용, mTLS, 메서드별 호출 권한, 강제 deadline·취소, 동시 stream과
메시지·압축 해제 제한을 적용합니다. 요청 DB 조회나 별도 정책 엔진을 추가하지
않습니다. 재시도는 검증한 멱등 질의에 원래 deadline 안에서만 적용하고 장애 시
재시도 폭증이나 오래된 grant를 만들지 않습니다. 같은 스냅샷의 네이티브/gRPC
결과를 거부·근거 부재까지 비교하고 framing·어댑터 부하를 별도로 측정합니다.

Kubernetes Pod는 Service로 gRPC를 호출할 수 있으나 API 서버의 인증·인가
webhook은 HTTP/JSON TokenReview/SubjectAccessReview이므로 어댑터가 필요합니다.
Envoy ext_authz는 헤더·문맥 신뢰와 실패 거부를 명시한 별도 어댑터 제안이며
실제 호환 검증 없이 자체 protobuf API를 Envoy 호환이라고 표시하지 않습니다.

근거: [gRPC 성능](https://grpc.io/docs/guides/performance/),
[deadline](https://grpc.io/docs/guides/deadlines/),
[Envoy 외부 인가](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/ext_authz/v3/ext_authz.proto.html).

## 성능과 완료 기준

요청 중 DB·온톨로지·분석 조회, 정책 컴파일, 범용 그래프 탐색, 코어의 JSON/SQL
파싱을 하지 않습니다. 컴파일된 ID·bitset·제한된 prefix/index 조회, 불변 스냅샷
읽기와 기존 pooled 바이너리 mTLS를 유지합니다. 변환은 제한하고 관리 쓰기를
요청 경로에 넣지 않습니다. 할당·복사를 줄여도 revision·만료·장애 거부는 유지합니다.
메타데이터 캐시는 원천 신선도로 검증하고 재사용 가능한 판단은 근거·회수 기한으로
제한합니다. 거의 없는 부하는 최적화 목표이며 스키마나 microbenchmark의 증명이
아닙니다. 현재는 기능 검증이 우선입니다.

타입 자원·어댑터 계약, DB commit 및 스냅샷 복구, 실제 Kubernetes 역방향 판정,
실제 DBMS 허용·거부·객체 재생성·원천 장애·회수가 완료 기준입니다. 어댑터 부하,
할당, 코어 지연, pooled RPC와 전체 요청 지연을 원래 처리량 목표 아래 별도로
측정합니다. HTTP/네이티브 검증으로 Kubernetes API나 PostgreSQL 집행 검증을
대신하지 않습니다.
