# Microsoft Graph API 이메일 관리 도구

Microsoft Graph API를 활용하여 이메일을 관리하는 CLI(명령줄 인터페이스) 도구입니다. 이 도구를 사용하여 이메일을 조회, 검색, 발송하고 로컬에서 관리할 수 있습니다.

## 주요 기능

- Microsoft Graph API를 통한 이메일 관리
- 인증 토큰 관리 및 갱신
- 수신함/송신함 이메일 조회
- 이메일 검색 및 필터링
- 이메일 발송
- 사용자 친화적인 명령줄 인터페이스

## 설치 방법

### 요구 사항

- Python 3.7 이상
- pip (Python 패키지 관리자)

### 설치 단계

1. 저장소 복제

```bash
git clone https://github.com/yourusername/graph_api.git
cd graph_api
```

2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate     # Windows
```

3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

## 설정 방법

1. `.env.example` 파일을 `.env`로 복사

```bash
cp .env.example .env
```

2. `.env` 파일 수정

Microsoft Azure Active Directory에서 앱을 등록하고 필요한 정보를 `.env` 파일에 추가합니다.

```
TENANT_ID=your_tenant_id_here
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
```

3. Azure 앱 등록 방법

Microsoft Graph API를 사용하기 위해서는 Azure Active Directory에 애플리케이션을 등록해야 합니다.

- [Azure Portal](https://portal.azure.com/)에 로그인
- "앱 등록" 메뉴로 이동
- "새 등록" 클릭
- 앱 이름 입력 및 지원되는 계정 유형 선택
- 리디렉션 URI 설정 (웹: `http://localhost:8000/redirect`)
- 앱 등록 완료 후 애플리케이션(클라이언트) ID 및 디렉터리(테넌트) ID 기록
- "인증서 및 비밀" 메뉴에서 클라이언트 시크릿 생성
- "API 권한" 메뉴에서 필요한 Microsoft Graph 권한 추가
  - `Mail.Read`
  - `Mail.ReadWrite`
  - `Mail.Send`
  - `User.Read`

## 사용 방법

### 인증

Microsoft Graph API를 사용하기 전에 인증이 필요합니다.

```bash
# 브라우저 인증 (기본)
python -m src.cli.main graphapi auth

# 디바이스 코드 인증
python -m src.cli.main graphapi auth --method device

# 클라이언트 자격 증명 인증 (서비스 계정)
python -m src.cli.main graphapi auth --method client
```

### 인증 상태 확인

```bash
python -m src.cli.main graphapi status
```

### 이메일 조회

```bash
# 수신함 이메일 조회 (기본: 최근 7일, 50개)
python -m src.cli.main email inbox

# 특정 기간 조회
python -m src.cli.main email inbox --days 30

# 결과 수 제한
python -m src.cli.main email inbox --limit 100

# 본문 미리보기 표시
python -m src.cli.main email inbox --show-body

# 결과를 JSON 파일로 저장
python -m src.cli.main email inbox --output emails.json

# 송신함 이메일 조회
python -m src.cli.main email sent
```

### 델타 쿼리 (최근 변경 이메일)

```bash
# 수신함 델타 쿼리
python -m src.cli.main email delta

# 송신함 델타 쿼리
python -m src.cli.main email delta --folder sentItems
```

### 이메일 검색

```bash
# 전체 이메일에서 검색
python -m src.cli.main email search "검색어"

# 특정 폴더에서 검색
python -m src.cli.main email search "검색어" --folder inbox

# 결과를 JSON 파일로 저장
python -m src.cli.main email search "검색어" --output search_results.json
```

### 특정 이메일 조회

```bash
# 이메일 상세 조회
python -m src.cli.main email view "메시지ID"

# 첨부 파일 정보 포함 조회
python -m src.cli.main email view "메시지ID" --include-attachments
```

### 이메일 읽음 표시

```bash
python -m src.cli.main email mark_read "메시지ID"
```

### 이메일 발송

```bash
python -m src.cli.main email send \
  --subject "제목" \
  --body "본문 내용" \
  --to recipient@example.com \
  --cc cc@example.com \
  --bcc bcc@example.com
```

HTML 본문 발송:

```bash
python -m src.cli.main email send \
  --subject "HTML 이메일" \
  --body "<h1>HTML 제목</h1><p>내용</p>" \
  --to recipient@example.com \
  --body-type html
```

### 필터 관리

```bash
# 필터 목록 조회
python -m src.cli.main email filter list

# 필터 추가
python -m src.cli.main email filter add "example@domain.com"

# 필터 제거
python -m src.cli.main email filter remove "example@domain.com"
```

## 프로젝트 구조

프로젝트는 클린 아키텍처 패턴을 기반으로 계층을 분할합니다:

```
email-embedding/
├── src/
│   ├── services/                # 도메인/비즈니스 로직 계층
│   │   ├── email_service.py     # 이메일 관련 비즈니스 로직
│   │   └── auth_service.py      # 인증 관련 비즈니스 로직
│   ├── cli/                     # 어댑터 계층 (CLI)
│   │   ├── email_cli.py
│   │   ├── graphapi_cli.py
│   │   └── main.py
│   ├── schemas/                 # DTO/모델 계층
│   │   ├── email.py
│   │   └── auth.py
│   ├── infra/                   # 인프라 계층
│   │   ├── graph_gateway.py     # Graph API 연동
│   │   ├── config.py
│   │   └── auth_token.py        # 토큰 관리
│   └── utils/                   # 유틸리티 계층
│       ├── logging_config.py
│       └── exceptions.py
```

## 문제 해결

### 인증 관련 문제

- 인증 오류가 발생하면 `graphapi logout` 명령어로 로그아웃 후 다시 인증을 시도하세요.
- 액세스 토큰이 만료된 경우, 자동으로 갱신을 시도합니다. 갱신이 실패하면 다시 인증하세요.

### 델타 쿼리 문제

- 델타 쿼리가 작동하지 않으면 `.delta_link.json` 파일을 삭제하고 다시 시도하세요.

### 로그 확인

로그 파일은 `logs/app.log`에 저장됩니다. 문제 해결을 위해 로그를 확인하세요.

```bash
tail -f logs/app.log
```

## 기여 방법

1. 저장소를 포크합니다.
2. 새 브랜치를 생성합니다.
3. 변경 사항을 커밋합니다.
4. 브랜치를 푸시합니다.
5. Pull Request를 제출합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 감사의 말

- Microsoft Graph API 팀
- 이 프로젝트에 기여한 모든 분들
