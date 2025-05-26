# Insurance ARS Manager Backend

손해보험 콜센터 ARS 시나리오 관리 및 Voice Cloning TTS 시스템의 백엔드 API 서버입니다.

## 기술 스택

- **Python**: 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy + Alembic
- **Package Manager**: uv
- **Authentication**: JWT
- **Testing**: pytest + httpx

## 프로젝트 구조

```
insurance-ars-backend/
├── app/                    # 메인 애플리케이션
│   ├── api/               # API 라우터
│   ├── core/              # 핵심 설정 (config, security, exceptions)
│   ├── db/                # 데이터베이스 설정
│   ├── models/            # SQLAlchemy 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   └── utils/             # 유틸리티
├── alembic/               # 데이터베이스 마이그레이션
├── scripts/               # 관리 스크립트
├── tests/                 # 테스트
└── docker/                # Docker 설정
```

## 개발 환경 설정

### 1. 프로젝트 클론 및 의존성 설치

```bash
git clone <repository-url>
cd insurance-ars-backend

# uv 설치 (아직 안 했다면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 환경에 맞게 설정
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 및 Redis 실행 (Docker)
docker-compose up -d

# 데이터베이스 마이그레이션
alembic upgrade head

# 초기 데이터 설정
uv run python scripts/init_db.py
```

### 4. 개발 서버 실행

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 URL에서 접근 가능합니다:
- API 문서: http://localhost:8000/api/v1/docs
- 헬스체크: http://localhost:8000/health

## 주요 명령어

### 데이터베이스 관리

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 관리자 계정 생성
uv run python scripts/create_admin.py
```

### 코드 품질 관리

```bash
# 코드 포매팅
uv run black app/ tests/
uv run isort app/ tests/

# 타입 체킹
uv run mypy app/

# 테스트 실행
uv run pytest

# 커버리지 포함 테스트
uv run pytest --cov=app --cov-report=html
```

### Docker 사용

```bash
# 개발 환경 실행
docker-compose -f docker/docker-compose.dev.yml up

# 운영 환경 빌드
docker build -f docker/Dockerfile.prod -t ars-manager:latest .
```

## API 문서

API 문서는 개발 서버 실행 후 `/api/v1/docs`에서 확인할 수 있습니다.

주요 엔드포인트:
- `POST /api/v1/auth/login` - 사용자 로그인
- `GET /api/v1/scenarios` - 시나리오 목록 조회
- `POST /api/v1/tts/generate` - TTS 생성
- `GET /api/v1/voice-actors` - 성우 목록 조회

## 환경 변수

주요 환경 변수:

```env
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/insurance_ars

# 보안
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 환경
ENVIRONMENT=development
DEBUG=true

# 파일 저장
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=50MB
```

## 개발 가이드

### 새 API 엔드포인트 추가

1. `app/schemas/`에 Pydantic 스키마 정의
2. `app/services/`에 비즈니스 로직 구현
3. `app/api/v1/endpoints/`에 FastAPI 라우터 추가
4. `tests/`에 테스트 코드 작성

### 새 데이터베이스 모델 추가

1. `app/models/`에 SQLAlchemy 모델 정의
2. `alembic revision --autogenerate -m "Add model"`로 마이그레이션 생성
3. `alembic upgrade head`로 마이그레이션 적용

## 배포

### 스테이징 환경

```bash
# 환경 변수 설정
export ENVIRONMENT=staging

# 마이그레이션 적용
alembic upgrade head

# 서버 실행
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 운영 환경

```bash
# Docker 이미지 빌드
docker build -f docker/Dockerfile.prod -t ars-manager:latest .

# 컨테이너 실행
docker run -d \
  --name ars-manager \
  -p 8000:8000 \
  --env-file .env.prod \
  ars-manager:latest
```

## 문제 해결

### 일반적인 문제들

1. **데이터베이스 연결 오류**
   - PostgreSQL이 실행 중인지 확인
   - 환경 변수 DATABASE_URL 확인

2. **마이그레이션 오류**
   - `alembic current`로 현재 상태 확인
   - 필요시 `alembic downgrade`로 롤백 후 재시도

3. **테스트 실패**
   - 테스트 데이터베이스 설정 확인
   - `pytest -v`로 상세 오류 확인

## 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

This project is licensed under the MIT License.
"""