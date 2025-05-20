# 프로젝트 설명 (Project Description)

## 프로젝트 개요

이 프로젝트는 Microsoft Graph API를 활용하여 이메일을 관리하는 CLI(명령줄 인터페이스) 도구입니다. 사용자는 이 도구를 통해 Microsoft 계정의 이메일을 조회, 검색, 발송할 수 있으며, 이메일 데이터를 필터링하고 관리할 수 있습니다.

## 아키텍처 설계

### 클린 아키텍처 개요

이 프로젝트는 클린 아키텍처 패턴을 따르고 있으며, 아래와 같은 계층 구조로 설계되어 있습니다:

1. **도메인/서비스 계층**: 핵심 비즈니스 로직을 포함하는 계층
2. **어댑터 계층**: 외부 요청을 처리하는 계층 (CLI 인터페이스)
3. **DTO/모델 계층**: 데이터 전송 객체 및 모델 정의
4. **인프라 계층**: 외부 시스템 연동 계층 (Microsoft Graph API)
5. **유틸리티 계층**: 로깅, 예외 처리 등 공통 기능 제공

### 의존성 규칙

클린 아키텍처에서 가장 중요한 원칙은 의존성 규칙입니다. 내부 계층은 외부 계층에 의존하지 않아야 합니다.

- 서비스 계층은 인프라 계층의 구현 세부사항에 의존하지 않고, 인터페이스를 통해 통신합니다.
- DTO/모델 계층은 다른 계층에 의존하지 않으며, 다른 모든 계층에서 사용될 수 있습니다.
- 어댑터 계층은 서비스 계층에 의존하지만, 서비스 계층은 어댑터 계층에 의존하지 않습니다.

## 주요 컴포넌트

### 1. 서비스 계층 (services/)

#### 1.1 AuthService

`AuthService` 클래스는 Microsoft Graph API 인증 관련 비즈니스 로직을 담당합니다.

```
class AuthService:
    - authenticate_code_flow(): 인증 코드 흐름으로 인증
    - authenticate_device_flow(): 디바이스 코드 흐름으로 인증
    - authenticate_client_credentials(): 클라이언트 자격 증명 흐름으로 인증
    - get_auth_status(): 인증 상태 조회
    - logout(): 로그아웃
    - get_user_info(): 사용자 정보 조회
```

#### 1.2 EmailService

`EmailService` 클래스는 이메일 관련 비즈니스 로직을 담당합니다.

```
class EmailService:
    # 본문 제외 이메일 조회 함수
    - get_inbox_emails(): 받은 편지함 이메일 목록 조회 (본문 제외)
    - get_sent_emails(): 보낸 편지함 이메일 목록 조회 (본문 제외)
    - get_all_emails(): 모든 이메일 목록 조회 (본문 제외)
    - search_emails(): 이메일 검색 (본문 제외)
    - get_delta_emails(): 델타 쿼리로 변경된 이메일 목록 조회 (본문 제외)
    
    # 본문 포함 이메일 조회 함수
    - get_inbox_emails_with_body(): 받은 편지함 이메일 조회 (본문 포함)
    - get_sent_emails_with_body(): 보낸 편지함 이메일 조회 (본문 포함)
    - get_all_emails_with_body(): 모든 이메일 조회 (본문 포함)
    - search_emails_with_body(): 이메일 검색 (본문 포함)
    - get_delta_emails_with_body(): 델타 쿼리로 변경된 이메일 조회 (본문 포함)
    
    # 이메일 관리 함수
    - get_email(): 특정 이메일 조회
    - mark_as_read(): 이메일 읽음으로 표시
    - send_email(): 이메일 발송
    
    # 필터 관리 함수
    - add_filter_sender(): 필터링할 발신자 추가
    - remove_filter_sender(): 필터링할 발신자 제거
    - get_filter_senders(): 필터링할 발신자 목록 조회
```

### 2. 어댑터 계층 (cli/)

#### 2.1 main.py

CLI 애플리케이션의 메인 엔트리 포인트입니다. 다른 CLI 모듈을 통합하고 기본 명령어를 제공합니다.

```
- cli(): 메인 CLI 그룹
- config_command(): 설정 정보 관리
- show_info(): 애플리케이션 정보 표시
```

#### 2.2 graphapi_cli.py

Graph API 관련 CLI 명령어를 처리합니다.

```
- graph_cli(): Graph API 명령어 그룹
- login(): 로그인
- logout(): 로그아웃
- status(): 인증 상태 확인
- me(): 사용자 정보 조회
- call_api(): API 직접 호출
```

#### 2.3 email_cli.py

이메일 관련 CLI 명령어를 처리합니다.

```
- email_cli(): 이메일 명령어 그룹
- inbox(): 받은 편지함 조회
- sent(): 보낸 편지함 조회
- delta(): 변경된 이메일 조회
- date_search(): 특정 날짜 범위의 이메일 조회 (본문 포함)
- search(): 키워드로 이메일 검색
- view(): 특정 이메일 상세 조회
- mark_read(): 이메일 읽음으로 표시
- send(): 이메일 발송
- filter(): 발신자 필터 관리 (list, add, remove)
```

### 3. DTO/모델 계층 (schemas/)

#### 3.1 auth.py

인증 관련 데이터 클래스를 정의합니다.

```
- TokenCredential: 토큰 자격 증명
- UserInfo: 사용자 정보
- AuthStatus: 인증 상태
- AuthResult: 인증 결과
```

#### 3.2 email.py

이메일 관련 데이터 클래스를 정의합니다.

```
- EmailParticipant: 이메일 참여자 (발신자, 수신자)
- EmailFilter: 이메일 필터링 옵션
- EmailProcessingOptions: 이메일 처리 옵션
- EmailDto: 이메일 데이터 전송 객체
```

### 4. 인프라 계층 (infra/)

#### 4.1 config.py

애플리케이션 설정을 관리합니다.

```
class Config:
    - API_BASE_URL: API 기본 URL
    - API_VERSION: API 버전
    - CLIENT_ID: 클라이언트 ID
    - CLIENT_SECRET: 클라이언트 시크릿
    - TENANT_ID: 테넌트 ID
    - REDIRECT_URI: 리디렉션 URI
    - SCOPES: 권한 범위
    - DEFAULT_DAYS: 기본 조회 기간
    - DEFAULT_LIMIT: 기본 조회 개수
    - get_filter_senders(): 필터링할 발신자 목록 조회
```

#### 4.2 auth_token.py

Microsoft Graph API 인증 토큰을 관리합니다.

```
class AuthTokenManager:
    - get_auth_url(): 인증 URL 조회
    - get_token(): 토큰 조회 (필요시 갱신)
    - get_token_from_code(): 인증 코드로 토큰 획득
    - authenticate_code_flow(): 인증 코드 흐름으로 인증
    - authenticate_device_flow(): 디바이스 코드 흐름으로 인증
    - authenticate_client_credentials(): 클라이언트 자격 증명 흐름으로 인증
    - is_authenticated(): 인증 여부 확인
    - get_auth_status(): 인증 상태 조회
    - get_user_info(): 사용자 정보 조회
    - logout(): 로그아웃
    - _get_token_silent(): 토큰 갱신 시도
    - _save_cache(): 토큰 캐시 저장
    - _load_cache(): 토큰 캐시 로드
```

#### 4.3 graph_gateway.py

Microsoft Graph API와 통신합니다.

```
class GraphApiGateway:
    - get_me(): 사용자 정보 조회
    - get_messages(): 메시지 조회
    - get_message(): 단일 메시지 조회
    - get_delta_messages(): 델타 쿼리로 변경된 메시지 조회
    - mark_as_read(): 메시지를 읽음으로 표시
    - send_message(): 메시지 발송
    - search_messages(): 메시지 검색
    - _make_request(): API 요청 수행
    - _build_message_url(): 메시지 URL 생성
    - _process_message_response(): 메시지 응답 처리
    - _save_delta_link(): 델타 링크 저장
    - _load_delta_link(): 델타 링크 로드
```

### 5. 유틸리티 계층 (utils/)

#### 5.1 logging_config.py

로깅 설정을 관리합니다.

```
class LoggerFactory:
    - initialize(): 로깅 시스템 초기화
    - get_logger(): 로거 인스턴스 조회
    - set_log_level(): 로그 레벨 설정
    - _get_formatter(): 로그 포맷터 생성
    - _get_log_level(): 로그 레벨 변환
```

#### 5.2 exceptions.py

사용자 정의 예외를 정의합니다.

```
- BaseError: 기본 예외 클래스
- ConfigurationError: 설정 오류 예외
- TokenCacheError: 토큰 캐시 오류 예외
- DeltaLinkError: 델타 링크 오류 예외
- AuthenticationError: 인증 오류 예외
- GraphApiError: Graph API 오류 예외
- EmailProcessingError: 이메일 처리 오류 예외
- CommandError: 명령 오류 예외
```

## 데이터 흐름

1. **사용자 명령 입력**: 사용자가 CLI 명령을 입력합니다.
2. **어댑터 계층**: CLI 모듈이 명령을 파싱하고 서비스 계층 메소드를 호출합니다.
3. **서비스 계층**: 비즈니스 로직을 수행하고 인프라 계층에 접근합니다.
4. **인프라 계층**: 외부 시스템(Microsoft Graph API)과 통신하고 결과를 반환합니다.
5. **모델 계층**: 데이터는 DTO/모델을 통해 계층 간에 전달됩니다.
6. **결과 반환**: 처리된 결과가 사용자에게 보여집니다.

## 주요 프로세스

### 인증 프로세스

1. 사용자가 `graph login` 명령을 실행합니다.
2. CLI 모듈은 선택한 인증 흐름에 따라 `AuthService` 메소드를 호출합니다.
3. `AuthService`는 `AuthTokenManager`를 통해 인증을 수행합니다.
4. 인증 코드 흐름의 경우:
   - 인증 URL을 생성하고 브라우저를 엽니다.
   - 사용자가 로그인하고 권한을 부여합니다.
   - 리디렉션 URI로 인증 코드가 전달됩니다.
   - 인증 코드로 토큰을 획득합니다.
5. 토큰은 로컬 캐시 파일에 저장됩니다.
6. 인증 결과는 `AuthResult` 객체로 반환됩니다.

### 이메일 조회 프로세스

1. 사용자가 `email inbox` 명령을 실행합니다.
2. CLI 모듈은 `EmailService.get_inbox_messages()` 메소드를 호출합니다.
3. `EmailService`는 `GraphApiGateway`를 통해 메시지를 요청합니다.
4. `GraphApiGateway`는 `AuthTokenManager`로부터 토큰을 획득하고 API 요청을 수행합니다.
5. 응답 데이터는 `EmailDto` 객체 목록으로 변환됩니다.
6. 처리 옵션에 따라 필터링 및 HTML-텍스트 변환이 적용됩니다.
7. 처리된 이메일 목록이 CLI에서 표시됩니다.

### 델타 쿼리 프로세스

1. 사용자가 `email delta` 명령을 실행합니다.
2. CLI 모듈은 `EmailService.get_delta_messages()` 메소드를 호출합니다.
3. `EmailService`는 `GraphApiGateway`를 통해 델타 쿼리를 요청합니다.
4. `GraphApiGateway`는 저장된 델타 링크가 있으면 사용하고, 없으면 새 델타 쿼리를 시작합니다.
5. API 응답에서 새 델타 링크를 추출하고 저장합니다.
6. 변경된 메시지는 `EmailDto` 객체 목록으로 반환됩니다.
7. 처리된 변경 사항이 CLI에서 표시됩니다.

## 설정 및 환경 변수

애플리케이션 설정은 다음과 같이 관리됩니다:

1. `.env` 파일: 환경 변수 저장
2. `Config` 클래스: 설정 관리 및 접근 제공
3. 환경 변수에는 API 인증 정보, 기본 설정, 로깅 설정 등이 포함됩니다.

## 확장성 및 유지보수성

이 프로젝트는 다음과 같은 방식으로 확장성과 유지보수성을 확보합니다:

1. **계층화된 아키텍처**: 각 계층의 책임이 명확하게 분리되어 있어 변경 및 확장이 용이합니다.
2. **인터페이스 기반 설계**: 구현 세부사항보다 인터페이스에 의존하여 구성 요소를 쉽게 변경할 수 있습니다.
3. **단일 책임 원칙**: 각 클래스는 단일 책임을 가지고 있어 유지보수가 용이합니다.
4. **모듈화**: 독립적인 모듈로 구성되어 있어 각 모듈을 독립적으로 개발하고 테스트할 수 있습니다.

## 향후 개선 사항

### 단기 개선 사항
- 로컬 데이터베이스 연동 구현
- 이메일 첨부 파일 처리 기능
- 일정 및 작업 관리 기능

### 중장기 개선 사항
- 웹 인터페이스 추가
- 이메일 분석 및 통계 기능
- 자동화된 이메일 규칙 및 필터링 기능
