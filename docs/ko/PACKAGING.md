# 구성요소 이미지 패키징

[English](../PACKAGING.md)

`tools/package_component.py`는 미리 기능 검증한 한강·호패·수문장·품계의 정적 ELF
파일을 패키징합니다. 먼저 선택한 소스 리비전을 빌드·검증해야 합니다. 전체 Git
리비전을 요구하고 동적 로더 파일은 거부합니다. 실행 파일과 Dockerfile만 있는
비공개 임시 디렉토리에서 빌드하며 설정·DB·공급자 자격·TLS 파일은 배포 때 따로
제공합니다. 소스 트리를 이미지에 복사하지 않습니다.

scratch와 UID/GID 65532를 사용합니다. 읽기 전용·네트워크 없음·capability 없음·
no-new-privileges 조건에서 --version 시작을 확인하고 이미지 ID와 크기를 보고합니다.
소스 라벨은 호출자가 선언한 리비전이며 암호학적 출처 증명이나 소스와 바이너리의
일치 증명은 아닙니다. 버전 시작 검사도 기능 검증을 대신하지 않습니다.

```sh
python3 tools/package_component.py --component hangang --binary /qualified/hangang --revision 0125779c1f807330544c466e8450aee10c7195ee
```

로컬 이미지 생성은 레지스트리 게시·서명 릴리즈·Pod 배포·K8s 원천 어댑터·한강 월드
통합 패키지의 완료가 아닙니다. 실제 클러스터에서 네 독립 서비스·mTLS Service DNS·
요청 집행·관리자 위임·영속/재시작·장애 거부를 검증해야 합니다.
