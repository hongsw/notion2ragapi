# Notion2RAG2API

Notion 문서를 자동으로 RAG(Retrieval-Augmented Generation)로 변환하고 REST API로 질의할 수 있는 웹 서비스입니다.

## 🚀 주요 기능

- 📝 **Notion 연동**: Notion API를 통한 문서 자동 수집
- 🧠 **RAG 파이프라인**: OpenAI 임베딩 및 GPT-4를 활용한 지능형 검색
- 🔍 **벡터 검색**: Chroma DB를 이용한 고속 유사도 검색
- 🌐 **REST API**: 간단한 API로 질의 및 관리
- 🔐 **인증**: API 키 및 JWT 기반 보안
- 🐳 **Docker 지원**: 컨테이너 기반 쉬운 배포

## 📋 요구사항

- Python 3.11+
- Docker & Docker Compose (선택사항)
- Notion API 토큰
- OpenAI API 키

## 🛠️ 설치 방법

### 방법 1: Docker 사용 (권장)

1. 환경 변수 설정
```bash
cp .env.example .env
```

2. `.env` 파일 편집
```env
NOTION_TOKEN=your_notion_integration_token
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_secret_key
```

3. Docker Compose 실행
```bash
docker-compose up -d
```

### 방법 2: 로컬 설치

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 편집
```

4. 서버 실행
```bash
cd backend
python -m uvicorn app.main:app --reload --port 5000
```

## 🔧 환경 변수 설정

### 필수 설정

| 변수 | 설명 | 예시 |
|------|------|------|
| `NOTION_TOKEN` | Notion Integration 토큰 | `secret_xxx...` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-xxx...` |
| `JWT_SECRET` | JWT 암호화 키 | `your-super-secret-key` |

### 선택 설정

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PORT` | 서버 포트 | `5000` |
| `VECTOR_DB_TYPE` | 벡터 DB 타입 | `chroma` |
| `CHUNK_SIZE` | 텍스트 청크 크기 (토큰) | `500` |
| `MAX_SEARCH_RESULTS` | 검색 결과 개수 | `5` |

## 📡 API 사용법

### 인증

API 키를 헤더에 포함:
```bash
X-API-Key: your_api_key
```

### 주요 엔드포인트

#### 1. 질의하기
```bash
POST /api/v1/query
Content-Type: application/json

{
  "query": "최근 프로젝트 회고 내용 정리해줘",
  "top_k": 5,
  "temperature": 0.7
}
```

응답:
```json
{
  "answer": "프로젝트 회고 내용은...",
  "sources": [
    {
      "page_id": "xxx",
      "page_title": "프로젝트 회고",
      "text": "...",
      "score": 0.95
    }
  ],
  "query": "최근 프로젝트 회고 내용 정리해줘",
  "model_used": "gpt-4-turbo-preview"
}
```

#### 2. 인덱스 새로고침
```bash
POST /api/v1/refresh
Content-Type: application/json

{
  "page_ids": null,  // null이면 전체 페이지
  "force": false
}
```

#### 3. 상태 확인
```bash
GET /api/v1/refresh/status/{task_id}
```

#### 4. 헬스 체크
```bash
GET /health
```

## 🏗️ 프로젝트 구조

```
notion2ragapi/
├── backend/
│   ├── app/
│   │   ├── api/           # API 엔드포인트
│   │   ├── core/          # 설정 및 핵심 모듈
│   │   ├── services/      # 비즈니스 로직
│   │   ├── models/        # 데이터 모델
│   │   └── utils/         # 유틸리티
│   └── tests/             # 테스트
├── frontend/              # React 프론트엔드 (개발 예정)
├── docker-compose.yml     # Docker 설정
├── Dockerfile            # Docker 이미지
├── requirements.txt      # Python 의존성
└── .env.example         # 환경 변수 템플릿
```

## 🔄 개발 워크플로우

### Notion 설정

1. [Notion Integrations](https://www.notion.so/my-integrations)에서 새 통합 생성
2. 필요한 권한 부여 (Read content)
3. 워크스페이스 또는 페이지에 통합 연결
4. Integration 토큰을 `.env`에 설정

### 데이터 인덱싱

1. 서버 시작
2. `/api/v1/refresh` 엔드포인트 호출
3. 인덱싱 상태 확인 (`/api/v1/refresh/status/{task_id}`)
4. 완료 후 질의 시작

## 🧪 테스트

```bash
# 단위 테스트
pytest backend/tests/

# 커버리지 확인
pytest --cov=backend/app backend/tests/
```

## 🐛 문제 해결

### 일반적인 문제

1. **Notion API 오류**
   - Integration 토큰 확인
   - 페이지 권한 확인

2. **OpenAI API 오류**
   - API 키 확인
   - 사용량 한도 확인

3. **벡터 DB 오류**
   - 디스크 공간 확인
   - 권한 확인

## 📚 API 문서

서버 실행 후:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 🙏 감사의 말

- [Notion API](https://developers.notion.com/)
- [OpenAI](https://openai.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [ChromaDB](https://www.trychroma.com/)

## 📞 지원

문제가 있으시면 [Issues](https://github.com/yourusername/notion2ragapi/issues)에 등록해주세요.