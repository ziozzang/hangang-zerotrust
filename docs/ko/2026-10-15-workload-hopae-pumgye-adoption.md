# 호패0.0.10·품계0.1.8 반영 — 2026-10-15

두 Linux amd64 musl 릴리즈를 공개하고 내부에 반영했다. 호패 release target은
b9b2a9a, runtime build는848dc835이며 외부 plugin/generator만 다르다. 품계 target은
8a37f25, runtime은adaf985이며 문서/패키징 도구만 다르다. Rust/lock 소스는 각각
동일하다. 이후 main의 Human provider-owner schema7과 Kubernetes API 문맥/매핑
선행 작업은 이번 릴리즈·운영 반영에 포함하지 않는다.

각5개 자산의 draft·public 다운로드가 준비한 바이트와 일치하고 pinned Ed25519·
버전/target/URL/hash/size·정적 raw·archive 내용을 확인했다. 익명 raw 다운로드200과
정확한 태그 target도 확인했다.

- [호패 릴리즈](https://github.com/ziozzang/hopae/releases/tag/v0.0.10)
- [품계 릴리즈](https://github.com/ziozzang/pumgye/releases/tag/v0.1.8)
- [실제 K3s 검증·보존한 실패](2026-10-15-workload-native-qualification.md)

품계는 비공개 바이너리/unit/env/SQLite/정책 백업과 DB clone preflight 후 교체했다.
정책을 유지했고 실제 mTLS 관리·native unknown-service 거절·추가 재시작을 통과했다.
첫 시도는 GitHub raw 다운로드의 실행 권한 누락으로 서비스 변경 전 실패했다. 서명된
바이트를 바꾸지 않고 mode755를 설정한 새 실행이 통과했으며 기존 실패를 보존한다.

호패는 읽기 전용 설정 검증과 SQLite/state/image/config/env 백업 후 반영했다. 사용자·
신원·세션·grant·MFA·provider/app·영속 profile을 보존했다. 실제 HTTP/HOP1 mTLS
만료/잘못된 credential 거절과 추가 컨테이너 재시작, 공개 서명 raw와 실행 파일 SHA
일치를 확인했다.

새 운영 관리자 브라우저에서19메뉴와 호패·수문장·품계3화면이 오류 없이 열렸고
사초·관리자 UI는200이다. 한강0.3.9·수문장0.3.6은 유지 중이며 외부 plugin 교체와
한강0.3.10 보안 검증은 후속이다. 기존 운영 경로에 Workload 강제를 자동 활성화하지
않았다. 이는 구성요소 반영이며 Human/K8s webhook/DBMS/처리량·전체 목표 완료가 아니다.
