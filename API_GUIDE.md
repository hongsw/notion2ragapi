# Notion2RAG2API - API 사용법 가이드

## 개요

Notion2RAG2API는 Notion 문서를 RAG(Retrieval-Augmented Generation) 시스템으로 변환하여 자연어 질의응답을 제공하는 REST API 서비스입니다.

## 서버 정보

- **Base URL**: `http://localhost:8001`
- **API Version**: v1.0.0
- **Documentation**: `http://localhost:8001/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8001/redoc` (ReDoc)

## 인증

모든 API 요청은 API 키 인증이 필요합니다.

**Header**: `X-API-Key: your-api-key-for-external-access`

## API 엔드포인트

### 1. 헬스 체크

**GET** `/health`

서비스의 상태를 확인합니다.

#### 응답 예시
```json
{
  "status": "healthy",
  "service": "Notion2RAG2API",
  "version": "0.1.0"
}
```

### 2. 루트 정보

**GET** `/`

서비스 기본 정보를 제공합니다.

#### 응답 예시
```json
{
  "name": "Notion2RAG2API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

### 3. RAG 쿼리

**POST** `/api/v1/query`

Notion 문서에서 관련 정보를 검색하고 GPT-4를 사용해 답변을 생성합니다.

#### 요청 본문
```json
{
  "query": "Flutter와 전자정부 프레임워크에 대해 설명해주세요",
  "top_k": 3,
  "temperature": 0.7
}
```

#### 요청 파라미터
- `query` (string, required): 자연어 질문 (최대 1000자)
- `top_k` (integer, optional): 검색할 문서 수 (기본값: 5, 범위: 1-20)
- `temperature` (float, optional): LLM 온도 설정 (기본값: 0.7, 범위: 0-2)

#### 응답 예시
```json
{
  "answer": "Flutter는 전자정부 5.0 표준 프레임워크로 공식 채택되었습니다...",
  "sources": [
    {
      "page_id": "2c6af259-fd05-801e-a963-c4e034d0678e",
      "text": "전자정부 5.0 표준(Flutter) 전환에 따른...",
      "score": 0.4796282649040222,
      "metadata": {}
    }
  ],
  "query": "Flutter와 전자정부 프레임워크에 대해 설명해주세요",
  "model_used": "gpt-4-turbo-preview"
}
```

#### 응답 필드
- `answer`: GPT-4가 생성한 답변
- `sources`: 검색된 관련 문서들
  - `page_id`: Notion 페이지 ID
  - `text`: 관련 텍스트 조각
  - `score`: 유사도 점수 (높을수록 관련성 높음)
  - `metadata`: 추가 메타데이터
- `query`: 원본 질문
- `model_used`: 사용된 LLM 모델

### 4. 데이터 새로고침

**POST** `/api/v1/refresh`

Notion에서 최신 데이터를 가져와 벡터 데이터베이스를 업데이트합니다.

#### 요청 본문 (선택적)
```json
{
  "page_ids": ["page-id-1", "page-id-2"],
  "force": false
}
```

#### 요청 파라미터
- `page_ids` (array, optional): 특정 페이지 ID들. 없으면 모든 페이지 새로고침
- `force` (boolean, optional): 변경되지 않은 내용도 강제 새로고침 (기본값: false)

#### 응답 예시
```json
{
  "status": "accepted",
  "message": "Refresh task has been queued",
  "task_id": "refresh_1765418233.803095",
  "started_at": "2025-12-11T10:57:13.803135"
}
```

## 에러 응답

### 인증 오류 (401)
```json
{
  "detail": "Invalid API key"
}
```

### 요청 오류 (400)
```json
{
  "detail": "Query must be between 1 and 1000 characters"
}
```

### 서버 오류 (500)
```json
{
  "detail": "Failed to process query: <error_message>"
}
```

## 사용 예시

### cURL 예시

#### 1. 헬스 체크
```bash
curl -X GET "http://localhost:8001/health" \
  -H "accept: application/json"
```

#### 2. RAG 쿼리
```bash
curl -X POST "http://localhost:8001/api/v1/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-for-external-access" \
  -d '{
    "query": "Flutter와 전자정부 프레임워크에 대해 설명해주세요",
    "top_k": 3,
    "temperature": 0.7
  }'
```

#### 3. 데이터 새로고침
```bash
curl -X POST "http://localhost:8001/api/v1/refresh" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-for-external-access" \
  -d '{
    "force": true
  }'
```

### Python 예시

```python
import requests

# API 설정
base_url = "http://localhost:8001"
api_key = "your-api-key-for-external-access"
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# 쿼리 요청
def query_api(question):
    response = requests.post(
        f"{base_url}/api/v1/query",
        json={
            "query": question,
            "top_k": 3,
            "temperature": 0.7
        },
        headers=headers
    )
    return response.json()

# 사용 예시
result = query_api("Flutter와 전자정부 프레임워크에 대해 설명해주세요")
print("답변:", result["answer"])
print("관련 문서 수:", len(result["sources"]))
```

### JavaScript 예시

```javascript
const baseUrl = 'http://localhost:8001';
const apiKey = 'your-api-key-for-external-access';

async function queryAPI(question) {
  const response = await fetch(`${baseUrl}/api/v1/query`, {
    method: 'POST',
    headers: {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: question,
      top_k: 3,
      temperature: 0.7
    })
  });

  return await response.json();
}

// 사용 예시
queryAPI('Flutter와 전자정부 프레임워크에 대해 설명해주세요')
  .then(result => {
    console.log('답변:', result.answer);
    console.log('관련 문서 수:', result.sources.length);
  });
```

## 설정

### 환경 변수

주요 설정은 `.env` 파일에서 관리됩니다:

```bash
# Notion API
NOTION_TOKEN=your-notion-token
NOTION_DB_ID=your-database-id

# OpenAI API
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
OPENAI_MODEL_CHAT=gpt-4-turbo-preview

# 서버 설정
PORT=8001
API_KEY=your-api-key-for-external-access

# 쿼리 설정
MAX_SEARCH_RESULTS=5
TEMPERATURE=0.7
MAX_TOKENS=1500
```

### 데이터 구조

#### 벡터 데이터베이스
- **FAISS**: Python 3.14 호환성을 위해 사용
- **인덱스 파일**: `./chroma_db/faiss_index.bin`
- **문서 메타데이터**: `./chroma_db/documents.json`

#### 텍스트 청킹
- **청크 크기**: 500 토큰 (설정 가능)
- **오버랩**: 50 토큰 (설정 가능)
- **임베딩**: OpenAI text-embedding-3-small 모델

## 제한사항

- **쿼리 길이**: 최대 1000자
- **검색 결과**: 최대 20개 문서
- **API 키**: 필수 인증
- **언어**: 한국어 및 영어 지원

## 성능 최적화

1. **배치 처리**: 여러 문서 동시 처리
2. **캐싱**: 벡터 인덱스 영구 저장
3. **비동기**: FastAPI 비동기 처리
4. **병렬화**: 임베딩 생성 배치 처리

## 문제 해결

### 일반적인 오류

1. **"FAISS index is empty"**: `/api/v1/refresh` 엔드포인트로 데이터 인덱싱
2. **"Invalid API key"**: 환경변수 `API_KEY` 확인
3. **OpenAI API 오류**: `OPENAI_API_KEY` 유효성 확인
4. **Notion API 오류**: `NOTION_TOKEN` 권한 확인

### 로그 확인

```bash
# 서버 로그 실시간 확인
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 버전 정보

- **Current**: v1.0.0
- **Python**: 3.14+
- **FastAPI**: 0.104.1+
- **OpenAI**: 1.6.1+

## 라이센스

이 프로젝트는 MIT 라이센스 하에 제공됩니다.