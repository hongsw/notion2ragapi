# Railway 환경 변수 설정 가이드

Railway 배포를 위해 필요한 환경 변수들을 설정하는 방법입니다.

## 🔧 필수 환경 변수

Railway 프로젝트의 **Variables** 탭에서 다음 환경 변수들을 설정하세요:

### 1. Notion API 설정
```bash
NOTION_TOKEN=ntn_your_actual_notion_token_here
NOTION_DB_ID=your_notion_database_id_optional
NOTION_PAGE_ID=your_notion_page_id_optional
```

### 2. OpenAI API 설정
```bash
OPENAI_API_KEY=sk-proj-your_actual_openai_key_here
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
OPENAI_MODEL_CHAT=gpt-4-turbo-preview
```

### 3. 서버 및 인증 설정
```bash
API_KEY=your-secure-api-key-for-external-access
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### 4. 벡터 데이터베이스 설정
```bash
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=/app/chroma_db
```

### 5. 서버 설정 (Railway 자동 설정)
```bash
# PORT는 Railway가 자동으로 설정합니다
HOST=0.0.0.0
WORKERS=1
RELOAD=false
```

## 📝 선택적 환경 변수

### 로깅 설정
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 성능 설정
```bash
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_SEARCH_RESULTS=5
TEMPERATURE=0.7
MAX_TOKENS=1500
```

### CORS 설정
```bash
CORS_ORIGINS=["https://your-frontend-domain.com","http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE"]
CORS_ALLOW_HEADERS=["*"]
```

### 자동 새로고침 설정
```bash
AUTO_REFRESH_ENABLED=false
AUTO_REFRESH_INTERVAL=3600
```

### 모니터링 설정
```bash
ENABLE_METRICS=true
METRICS_PORT=9090
```

## 🚀 Railway 배포 단계

### 1단계: Railway 계정 생성
1. [railway.app](https://railway.app) 방문
2. GitHub 계정으로 로그인
3. 새 프로젝트 생성

### 2단계: GitHub 리포지토리 연결
1. "Deploy from GitHub repo" 선택
2. `hongsw/notion2ragapi` 저장소 선택
3. `main` 브랜치 선택

### 3단계: 환경 변수 설정
1. 프로젝트 대시보드에서 **Variables** 탭 클릭
2. 위의 필수 환경 변수들을 하나씩 추가
3. 특히 다음 변수들은 반드시 설정:
   - `NOTION_TOKEN`
   - `OPENAI_API_KEY`
   - `API_KEY`
   - `JWT_SECRET`

### 4단계: 배포 시작
1. 환경 변수 설정 완료 후 자동 배포 시작
2. **Deployments** 탭에서 배포 상태 확인
3. 빌드 로그 실시간 확인 가능

### 5단계: 도메인 설정
1. **Settings** 탭에서 **Domains** 섹션 이동
2. Railway 제공 도메인 사용 또는 커스텀 도메인 연결
3. 자동 HTTPS 인증서 적용됨

## 🔍 배포 후 확인사항

### 헬스 체크
```bash
curl https://your-app.railway.app/health
```
응답 예시:
```json
{
  "status": "healthy",
  "service": "Notion2RAG2API",
  "version": "0.1.0"
}
```

### API 문서 확인
- Swagger UI: `https://your-app.railway.app/docs`
- ReDoc: `https://your-app.railway.app/redoc`

### 테스트 쿼리
```bash
curl -X POST "https://your-app.railway.app/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "테스트 질문", "top_k": 3}'
```

## 🛠️ 문제 해결

### 일반적인 오류

1. **Build Failed**
   - Dockerfile 구문 확인
   - requirements.txt 의존성 확인

2. **Application Crashed**
   - 환경 변수 누락 확인
   - Railway 로그 확인: `railway logs`

3. **API Key 오류**
   - NOTION_TOKEN 형식 확인 (`ntn_`로 시작)
   - OPENAI_API_KEY 형식 확인 (`sk-`로 시작)

4. **Database Connection Error**
   - CHROMA_PERSIST_DIRECTORY 경로 확인
   - 볼륨 마운트 확인

### Railway CLI를 통한 디버깅

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 프로젝트 연결
railway login
railway link

# 로그 확인
railway logs --tail

# 환경 변수 확인
railway variables

# 로컬에서 Railway 환경 실행
railway shell
```

## 📊 성능 최적화

### 메모리 사용량 모니터링
- Railway 대시보드에서 메모리 사용량 확인
- FAISS 인덱스 크기에 따라 메모리 사용량 증가

### 스케일링 설정
```bash
# Railway에서 스케일링 설정
# Settings > Resources에서 메모리 및 CPU 조정
```

## 🔄 자동 배포 설정

Railway는 GitHub과 연결되어 있어 `main` 브랜치에 push하면 자동으로 배포됩니다:

1. 로컬에서 코드 수정
2. `git push origin main`
3. Railway에서 자동 빌드 및 배포
4. 무중단 배포 (zero-downtime deployment)

## 💰 비용 관리

### 무료 티어 한도
- $5 크레딧/월 제공
- 메모리: 512MB
- CPU: 1 vCPU
- 네트워크: 100GB/월

### 사용량 모니터링
- Railway 대시보드에서 실시간 사용량 확인
- 알림 설정으로 한도 초과 방지

## 🔒 보안 설정

### 환경 변수 보안
- 민감한 정보는 반드시 환경 변수로 설정
- `.env` 파일을 Git에 커밋하지 않음
- API 키 정기적 로테이션 권장

### HTTPS 설정
- Railway에서 자동으로 HTTPS 인증서 제공
- 모든 API 호출은 HTTPS로 보안됨

이 가이드를 따라하면 Railway에서 Notion2RAG2API를 성공적으로 배포할 수 있습니다!