# 사용자 요구사항

## 1. 배경 및 큰 그림

Microsoft Graph API를 활용하여 이메일을 관리하는 도구를 개발합니다. 이 도구는 CLI(명령줄 인터페이스)를 통해 Microsoft Graph API로부터 이메일을 가져오고, 로컬 데이터베이스에 저장하며, 이메일을 발송하는 기능을 제공합니다.

아키텍쳐 디자인으로 구성합니다.

이 도구는 다음과 같은 사용자의 요구를 충족합니다:
- Microsoft Graph API를 통한 이메일 관리
- 인증 토큰 관리 및 갱신
- 이메일 데이터의 로컬 저장 및 관리
- 사용자 친화적인 명령줄 인터페이스

## 2. 모듈 분할 기준

프로젝트는 클린 아키텍처 패턴을 기반으로 다음과 같이 계층을 분할합니다:

1. **도메인/서비스 계층**: 핵심 비즈니스 로직을 포함하는 계층 (API/CLI가 없어도 동작 가능)
2. **어댑터 계층**: 외부 요청을 처리하는 계층 (CLI, API 인터페이스)
3. **DTO/모델 계층**: 데이터 전송 객체 및 모델 정의
4. **인프라 계층**: 외부 시스템 연동 계층 (Microsoft Graph API, 데이터베이스)
5. **유틸리티 계층**: 로깅, 예외 처리 등 공통 기능 제공

각 계층은 명확한 책임을 가지며, 내부 계층은 외부 계층에 의존하지 않습니다.

모듈은 각각 독립적으로 동작하며, 모듈 간의 의존성을 최소화하여 유지보수성을 높입니다.

## 3. 언어 및 라이브러리

- **프로그래밍 언어**: Python 3.7 이상
- **주요 라이브러리**:
  - `requests`: HTTP 요청 처리
  - `msal`: Microsoft Authentication Library
  - `click`: CLI 인터페이스 구축
  - `rich`: 콘솔 출력 서식
  - `sqlite3`: 로컬 데이터베이스
  - `python-dotenv`: 환경 변수 관리

## 4. 디렉터리 구조

```
email-embedding/
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml               # 또는 setup.py, poetry 등의 설정 파일
├── docs/
│   ├── user_requirements.md
│   ├── project_description.md
│   └── ProgressAndTOdo.md
├── logs/
│   └── app.log
├── src/
│   ├── __init__.py
│   ├── services/                # 도메인/비즈니스 로직 계층
│   │   ├── __init__.py
│   │   ├── email_service.py     # 이메일 관련 비즈니스 로직
│   │   └── auth_service.py      # 인증 관련 비즈니스 로직
│   ├── cli/                     # 어댑터 계층 (CLI)
│   │   ├── __init__.py
│   │   ├── email_cli.py
│   │   ├── graphapi_cli.py
│   │   └── main.py
│   ├── api/                     # 어댑터 계층 (API)
│   │   ├── __init__.py
│   │   ├── email_api.py
│   │   └── auth_api.py
│   ├── schemas/                 # DTO/모델 계층
│   │   ├── __init__.py
│   │   ├── email.py
│   │   └── auth.py
│   ├── infra/                   # 인프라 계층
│   │   ├── __init__.py
│   │   ├── graph_gateway.py     # Graph API 연동
│   │   ├── db_repository.py     # 데이터베이스 연동
│   │   ├── config.py
│   │   ├── auth_token.py        # 토큰 관리
│   │   ├── .token_cache.json    # (gitignore 권장)
│   │   └── .delta_link.json     # (gitignore 권장)
│   ├── utils/                   # 유틸리티 계층
│   │   ├── __init__.py
│   │   ├── logging_config.py
│   │   └── exceptions.py
```

**[NOTE] 현재 프로젝트 구조는 기존의 모듈 기반 구조이며, 점진적으로 클린 아키텍처 패턴으로 전환할 예정입니다.**

## 5. 모듈별 코드 요구사항

### 5.1 Graph API 모듈

#### auth_token.py
- Microsoft Graph API 인증 처리
- 토큰 캐시 및 갱신 기능
- 인증 상태 확인 기능

**[NOTE] 인증 구현 시 주의사항:**
- **환경 변수 및 .env 파일 관리**
  - 인증 환경 변수(TENANT_ID, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)는 반드시 .env 파일에 실제 값으로 등록해야 하며, 예시 값이나 주석이 남아있으면 인증이 실패함
  - REDIRECT_URI는 Azure Portal에 등록된 값과 반드시 일치해야 하며, 누락 시 기본값이 사용되어 인증이 실패할 수 있음
  - 환경 변수 오염(예시 값이 export 되어 있는 경우) 시 unset 명령어로 기존 값을 해제한 후 인증을 시도해야 함
  - .env 파일에 REDIRECT_URI가 없으면 인증이 실패하므로 반드시 추가해야 함
  - 인증 성공 후에는 브라우저가 정상적으로 열리고, 사용자 정보가 출력되어야 함
- **인증 코드 흐름(Authorization Code Flow) 구현 시 스코프 설정 주의**:
  - `openid`, `offline_access`, `profile`과 같은 예약된 스코프는 MSAL 라이브러리에서 자동으로 추가됨
  - 이러한 예약된 스코프를 명시적으로 지정하면 에러 발생 가능: 
    `"You cannot use any scope value that is reserved."`
  - 해결책: Graph API 관련 스코프만 명시적으로 지정하고 예약된 스코프는 제외
  
- **브라우저 인증 흐름 구현 시 고려사항**:
  - 리디렉션 URI와 콜백 처리를 위한 로컬 서버 필요
  - 사용자 인터랙션 개선을 위한 브라우저 자동 실행 기능 추가 필요
  - 인증 코드 수신 후 처리 로직 필요
  
- **토큰 상태 모니터링**:
  - 토큰 자동 갱신 메커니즘 구현 필요
  - 캐시된 토큰과 메모리 내 토큰 상태 일치화 필요

**[NOTE] 인증 테스트 중 발생한 주요 오류와 해결 방법:**
- **MSAL 라이브러리 호환성 문제**:
  - 오류: `'SerializableTokenCache' object has no attribute 'has_state'`
  - 원인: MSAL 라이브러리의 최신 버전(1.32.3)에서는 `has_state()` 메서드가 제공되지 않음
  - 해결: 직렬화된 캐시 데이터를 직접 확인하여 빈 상태 여부를 판단하도록 로직 수정
  ```python
  # 수정 전 코드
  if self.token_cache.has_state():
      # 캐시 저장 로직...
  
  # 수정 후 코드
  cache_data = self.token_cache.serialize()
  if cache_data and len(cache_data) > 2:  # "{}" 이상의 내용이 있는지 확인
      # 캐시 저장 로직...
  ```
  
- **경로 처리 문제**:
  - 오류: `FileNotFoundError: [Errno 2] No such file or directory: ''`
  - 원인: 토큰 캐시 파일 경로가 비어있거나 유효하지 않음
  - 해결: 경로 유효성 검증 및 기본 경로 제공 로직 추가
  ```python
  # 토큰 캐시 파일 경로가 비어있는 경우 기본 경로 사용
  if not self.token_cache_file:
      self.token_cache_file = os.path.join(os.path.dirname(__file__), ".token_cache.json")
  ```
  
- **Path 객체 누락 문제**:
  - 오류: `NameError: name 'Path' is not defined`
  - 원인: `pathlib` 모듈에서 `Path` 클래스를 import하지 않음
  - 해결: import 문 추가
  ```python
  from pathlib import Path
  ```

#### config.py
- API 설정 관리
- `.env` 파일에서 설정 로드
- 기본 설정값 제공

#### API 수신 후 데이터 사전처리
- 수신 데이터 사전처리 후 사용
  - content가 html 인 경우 text 변환
  - 필터링 기능(보낸 사람ID, 보낸 사람), 초기에는 `block@krs.co.kr`, `Administrator`
  - 필터링 항목 추가 함수 구현(보낸 사람 이름 필터, 보낸 사람 이메일 필터)
  - 송신 메일에는 `sentDateTime` 필드가 있으나 수신 메일에는 `receivedDateTime` 필드 사용 함으로 2개 모두 갖을 수 있음

#### get_emails.py
- 이메일 검색 기능
- 송수신 메일 관련 기능
  - 기간별 수신 메일 데이터 갖어오기
  - 기간별 송신 메일 데이터 갖어오기
  - 기간별 송수신 메일 모두 갖어오기
  - 최근 데이터 갖어온 이후 데이터 갖어오기


**[NOTE] 송수신 메일 조회 시 주의사항:**
- **델타 쿼리 별도 관리**: 
  - 송신 메일과 수신 메일의 델타 링크는 별도로 관리해야 함
  - 각각 다른 폴더(sentItems vs inbox)에 대한 델타 쿼리이므로 동일한 델타 링크 사용 불가
  - `config.py`에서 각각의 델타 링크를 별도 키로 저장 필요

- **API 응답 필드 차이**:
  - 송신 메일에는 `sentDateTime` 필드가 있으나 수신 메일에는 `receivedDateTime` 필드 사용
  - 발신자/수신자 정보 구조가 다름 (from vs toRecipients)
  - 필드 접근 시 항상 키 존재 여부 검증 필요

### 5.3 CLI 모듈

#### email_cli.py
- 이메일 관련 명령어 처리
  - 기간별 수신 메일 데이터 갖어오기
  - 기간별 송신 메일 데이터 갖어오기
  - 기간별 송수신 메일 모두 갖어오기
  - 최근 데이터 갖어온 이후 데이터 갖어오기

#### graphapi_cli.py
- Graph API 관련 명령어 처리
  - 인증
  - 토큰 관리
  - API 직접 호출

#### db_cli.py
- 향후 구현

### 5.4 유틸리티 모듈

#### logging_config.py
- 로깅 설정 및 관리

#### exceptions.py
- 예외 처리 및 에러 관리


## 7. 종합 요약

이 프로젝트는 Microsoft Graph API를 활용한 이메일 관리 도구로, 이메일 조회, 검색, 발송 기능을 제공합니다. 모듈화된 구조와 명확한 인터페이스를 통해 확장성과 유지보수성을 확보합니다. CLI를 통해 사용자 친화적인 인터페이스를 제공하며, 로컬 데이터베이스를 활용하여 이메일 데이터를 효율적으로 관리합니다.
