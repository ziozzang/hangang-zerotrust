# H3 대기 계획: Human 전용 정책과 네이티브 권한

상태: 읽기 전용 체크리스트이며 H2의 검증된 주체 의미 확정 전 구현하지 않습니다.
[영문 상세/정확한 소스 위치](../reviews/2026-10-16-human-pum-h3-plan.md).
Pum435기준이며 e253의 core/server/proto는 동일합니다. H1해시는 순수 메타데이터,
H0세션 캡처는 아직 공개 Human영수증이 아닙니다.

1. H2에서 안정된 주체 네임스페이스·issuer/realm/provider 의미·삭제 규칙과
   실제 opaque관측/서명 벡터를 확정합니다. 이메일·표시명·클라이언트 realm이나
   Workload주체를 Human으로 바꾸지 않습니다.
2. 같은 Service/CompiledView에 빈 경우 직렬화 생략하는 human_users를 추가하고
   기존65536총할당 제한에 포함합니다. users/workload_users와 양방향 fallback은
   금지합니다. KubernetesApi컨텍스트에서는 Human할당·평가 모두 금지합니다.
3. 사용자별 할당 역할의 minimum_aal을 사용하고 네트워크/리소스 요구치와 max로
   결합합니다. 전역 서비스 floor로 모든 사용자를 올리지 않습니다. 초기 Human은
   실제 검증된 AAL1/2만 허용하며 기존 요구3은 만족 불가로 유지합니다.
4. H2이후 전용 privateSDK관측 소유자에서만 인증 정보를 받습니다. 숫자 생성자,
   서명만으로 권한 생성, UTC수명 복원, 헤더기반 승격을 금지합니다.
5. 같은 View와 실제 Sum/라우트/정확한 AAL계획을 사용하고 콜백 이전 원래 수명에
   고정합니다. 서명 후에도 auth/정책/라우트/계획/시간 검증을 반복합니다.
   전체 증명 보존 수명과 더 짧은 입장 가능 수명은 구별합니다.
6. 이후 별도 RPC/명시적 활성화/제한된 인증 ingress와 contract4를 구현하되
   SAME paired ledger를 사용합니다. Root는 고정 라우트 종류와 사전/최종 주체를
   연결해야 하며 Human전체체인은 별도 검증합니다.

필수 게이트: 충돌하도록 주입한 원시 라벨은 종류별 네임스페이스 검증에서 거부하고,
같은 기반 신원 라벨을 종류별로 독립 정규화한 주체에 서로 다른 역할을 할당합니다.
legacy users가 두 정규 주체를 허용해도 typed맵의 fallback은 금지합니다.
유효한 Human문자열이 Workload파서도 통과해야 한다고 요구하지 않습니다.
삭제 후 fallback금지, 사용자별
AAL1/2차이, AAL0/3거부, scope/class/resource/action/network요구, API컨텍스트거부,
기존 직렬화/Service/Workload보존, 실제 logout/revoke/disable/factor/provider/material
철회와 콜백/서명 중 변경, v2본문·헤더·목적지변조, 원래 BOOTTIME만료/오류,
전체 회귀와 공개SDK→Pum→Hop원장→Root 실제 backendcounter입니다.
순수 코어 테스트나 가상 서명만으로 Human운영 완료를 주장하지 않습니다.
로컬계정·복구·모든 공급자MFA·원천 스트리밍·DB follower·성능은 전체 목표에 남습니다.
