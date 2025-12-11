아래는 **Notion → RAG → API**를 **가장 간단하게 설치 후 바로 동작**하도록 하는 **스펙 기반 PRD**다.
`.env`에 인증키만 넣으면 웹에서 설정/운영 가능한 제품 수준 스펙이다.

---

# 📌 PRD: Notion2RAG2API

## 1) 제품 개요

Notion 문서를 자동으로 RAG로 변환하고, **REST API/GraphQL**로 질의할 수 있는 웹 서비스.
사용자는 **Notion 인증 + API 키**만 넣으면 바로 RAG API 서버가 구동됨.

---

## 2) 핵심 기능

### **A. Notion 연동**

* Notion 공식 API로 워크스페이스/페이지 읽기
* 페이지/블록 전체 텍스트 수집
* 자동 페이지 변경 감지

### **B. RAG 파이프라인**

* 텍스트를 **임베딩 생성**
* 임베딩을 **벡터 DB에 인덱싱**
* 유사도 기반 검색 + LLM 질의 응답

### **C. API**

* `/query` 엔드포인트: 자연어 질의
* `/refresh` 엔드포인트: Notion 재인덱싱
* API 키 기반 인증

### **D. Web UI**

* 대시보드: 연결된 Notion 페이지 목록
* 검색 UI + 질의 히스토리
* 설정: API 키, 모델 설정

---

## 3) 아키텍처

```
Notion API
    ↓
Notion2RAG2API Server
├── Fetch & Parser
│     └─ Notion Block → Plain Text
├── Embedding Worker
│     └─ 임베딩 생성
├── Vector Store
│     └─ Chroma / Qdrant
├── API Layer
│     └─ REST API
├── UI
      └─ React 대시보드
```

---

## 4) 스펙

### 4.1. 환경변수 (`.env`)

```
NOTION_TOKEN=secret_xxx
NOTION_DB_ID=xxx
OPENAI_API_KEY=sk-xxx
VECTOR_DB_TYPE=chroma | qdrant
PORT=5000
JWT_SECRET=xxx
```

### 4.2. 데이터 플로우

1. **Notion Fetcher**

```
GET https://api.notion.com/v1/blocks/{block_id}/children
```

→ 페이지/하위 블록 재귀 수집

2. **Text Normalization**

* heading, bullets, toggle 풀어서 plain text
* metadata: page_id, heading hierarchy

3. **Chunk**

* 250–500 tokens 단위로 분절

4. **Embedding**

* 모델: `text-embedding-3-small` (OpenAI)

5. **Vector DB**

* 인덱싱: `id`, `text`, `metadata`, `embedding`

### 4.3. API Endpoints

#### **POST /api/v1/query**

Request

```json
{
  "query": "최근 프로젝트 회고 정리해줘"
}
```

Response

```json
{
  "answer": "...",
  "sources": [
    {"page_id":"...", "text":"..."}
  ]
}
```

#### **POST /api/v1/refresh**

* Notion 데이터 리프레시
* Re-embedding/인덱싱 재실행

Response

```json
{ "status": "ok" }
```

### 4.4. Auth

* API key 또는 JWT
* UI용 로그인/관리

---

## 5) UI 기능

### **대시보드**

* 연결된 Notion
* 페이지 목록 & 상태
* 임베딩 통계

### **Search**

* 자연어 질의
* 답변 + 관련 문서/문단 소스

### **설정**

* `.env` 미리보기
* 모델/벡터DB 선택

---

## 6) 벡터 DB 옵션

| 옵션                  | 특징           | 비용    |
| ------------------- | ------------ | ----- |
| **Chroma (local)**  | 파일 기반, 빠른 세팅 | 무료    |
| **Qdrant (docker)** | 고성능, 확장용     | 무료/도커 |
| **Pinecone**        | SaaS 벡터      | 유료    |

기본: **Chroma** (초기 무료)

---

## 7) 스테이지별 요구

### **Alpha**

* Notion Fetch + Embedding
* Vector DB local
* Basic API `/query`, `/refresh`

### **Beta**

* Web UI
* 모델 선택
* Pagination/History

### **GA**

* OAuth Notion Connect
* 사용자별 워크스페이스
* RBAC
* 로그/통계

---

## 8) 성공 기준 (MVP)

✅ Notion 페이지에서 텍스트 자동 수집
✅ 질의 시 답변 + 소스 리턴
✅ 인증키만 넣으면 설치 후 실행
✅ API 안정성 99%+

---

## 9) 제한/리스크

* Notion API Rate-limit 처리
* 노션 변경 시 스키마 대응
* 대용량 페이지 성능

---

## 10) 배포 설정

```
docker build -t notion2rag2api .
docker run -d --env-file .env -p 5000:5000 notion2rag2api
```

---

원하면 **OpenAPI spec**, **DB 스키마**, **백엔드 엔드포인트 코드 템플릿**까지 바로 만들어줄게.
