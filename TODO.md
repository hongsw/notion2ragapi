# TODO.md - Notion2RAG2API 개발 작업 목록

## 📌 프로젝트 개요
Notion 문서를 RAG(Retrieval-Augmented Generation)로 변환하고 REST API/GraphQL로 질의할 수 있는 웹 서비스 구축

## 🎯 개발 단계별 작업 목록

### Phase 0: 프로젝트 초기화 및 환경 설정
- [x] TODO.md 작성 및 프로젝트 계획 수립
- [ ] 프로젝트 구조 초기화
  - [ ] Git 저장소 초기화
  - [ ] .gitignore 파일 생성
  - [ ] 프로젝트 디렉토리 구조 생성
- [ ] Python 백엔드 환경 설정
  - [ ] requirements.txt 생성
  - [ ] 가상환경 설정 가이드
  - [ ] FastAPI 프로젝트 구조 설정
- [ ] 환경 변수 설정
  - [ ] .env.example 파일 생성
  - [ ] 환경 변수 로더 구현
  - [ ] 설정 검증 로직

### Phase 1: Alpha - 핵심 기능 구현

#### 1.1 Notion API 연동
- [ ] Notion API 클라이언트 구현
  - [ ] 인증 처리
  - [ ] 워크스페이스/데이터베이스 조회
  - [ ] 페이지 내용 가져오기
  - [ ] 블록 재귀적 파싱
- [ ] 텍스트 추출 및 정규화
  - [ ] 블록 타입별 텍스트 추출
  - [ ] 메타데이터 보존 (page_id, hierarchy)
  - [ ] Plain text 변환

#### 1.2 RAG 파이프라인 구축
- [ ] 텍스트 청킹 모듈
  - [ ] 250-500 토큰 단위 분할
  - [ ] 문맥 유지 로직
  - [ ] 청크 메타데이터 관리
- [ ] 임베딩 생성
  - [ ] OpenAI API 연동
  - [ ] text-embedding-3-small 모델 사용
  - [ ] 배치 처리 최적화
- [ ] 벡터 데이터베이스 설정
  - [ ] Chroma DB 초기 설정
  - [ ] 인덱싱 로직 구현
  - [ ] 검색 기능 구현

#### 1.3 기본 API 엔드포인트
- [ ] FastAPI 앱 구조 설정
- [ ] /api/v1/query 엔드포인트
  - [ ] 자연어 질의 처리
  - [ ] 벡터 검색
  - [ ] LLM 응답 생성
  - [ ] 소스 정보 포함
- [ ] /api/v1/refresh 엔드포인트
  - [ ] Notion 데이터 재동기화
  - [ ] 임베딩 재생성
  - [ ] 인덱스 업데이트

### Phase 2: Beta - Web UI 및 고급 기능

#### 2.1 인증 시스템
- [ ] API 키 기반 인증
  - [ ] API 키 생성/관리
  - [ ] 요청 검증 미들웨어
- [ ] JWT 인증 (UI용)
  - [ ] 로그인/로그아웃
  - [ ] 세션 관리

#### 2.2 React 프론트엔드
- [ ] React 앱 초기화
  - [ ] Create React App 또는 Vite 설정
  - [ ] 라우팅 설정
  - [ ] API 클라이언트 설정
- [ ] 대시보드 페이지
  - [ ] Notion 연결 상태
  - [ ] 페이지 목록 표시
  - [ ] 임베딩 통계
- [ ] 검색 인터페이스
  - [ ] 질의 입력 UI
  - [ ] 결과 표시
  - [ ] 소스 문서 링크
  - [ ] 질의 히스토리
- [ ] 설정 페이지
  - [ ] API 키 관리
  - [ ] 모델 선택
  - [ ] 벡터 DB 설정

#### 2.3 고급 기능
- [ ] 페이지네이션
  - [ ] 검색 결과 페이징
  - [ ] 히스토리 페이징
- [ ] 실시간 업데이트
  - [ ] WebSocket 지원
  - [ ] 자동 리프레시 스케줄링
- [ ] 에러 처리 및 재시도
  - [ ] Rate limit 처리
  - [ ] 네트워크 에러 복구

### Phase 3: GA - 프로덕션 준비

#### 3.1 다중 사용자 지원
- [ ] OAuth Notion 연동
  - [ ] OAuth 플로우 구현
  - [ ] 토큰 관리
- [ ] 사용자별 워크스페이스
  - [ ] 데이터 격리
  - [ ] 권한 관리
- [ ] RBAC (Role-Based Access Control)
  - [ ] 역할 정의
  - [ ] 권한 체크

#### 3.2 모니터링 및 분석
- [ ] 로깅 시스템
  - [ ] 구조화된 로그
  - [ ] 에러 추적
- [ ] 메트릭 수집
  - [ ] API 사용량
  - [ ] 성능 지표
  - [ ] 사용자 활동
- [ ] 대시보드 통계
  - [ ] 사용량 차트
  - [ ] 성능 모니터링

#### 3.3 배포 및 운영
- [ ] Docker 설정
  - [ ] Dockerfile 작성
  - [ ] docker-compose.yml
  - [ ] 환경별 설정
- [ ] CI/CD 파이프라인
  - [ ] GitHub Actions 설정
  - [ ] 자동 테스트
  - [ ] 자동 배포
- [ ] 프로덕션 최적화
  - [ ] 캐싱 전략
  - [ ] 부하 분산
  - [ ] 데이터베이스 최적화

### Phase 4: 문서화 및 테스트

#### 4.1 문서화
- [ ] README.md 작성
  - [ ] 설치 가이드
  - [ ] 사용법
  - [ ] API 문서
- [ ] CLAUDE.md 작성
  - [ ] 개발 가이드
  - [ ] 아키텍처 설명
  - [ ] 주요 명령어
- [ ] OpenAPI 스펙
  - [ ] Swagger 문서 생성
  - [ ] API 클라이언트 생성

#### 4.2 테스트
- [ ] 단위 테스트
  - [ ] API 엔드포인트
  - [ ] 비즈니스 로직
  - [ ] 유틸리티 함수
- [ ] 통합 테스트
  - [ ] E2E 시나리오
  - [ ] API 통합
- [ ] 성능 테스트
  - [ ] 부하 테스트
  - [ ] 응답 시간 측정

## 🔧 기술 스택

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Vector DB**: Chroma (로컬) → Qdrant (프로덕션)
- **Embedding**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-4

### Frontend
- **Framework**: React 18
- **UI Library**: Material-UI / Ant Design
- **State Management**: Redux Toolkit / Zustand
- **API Client**: Axios / React Query

### Infrastructure
- **Container**: Docker
- **Database**: PostgreSQL (메타데이터)
- **Cache**: Redis (선택사항)
- **Monitoring**: Prometheus + Grafana

## 📊 진행 상태

- **전체 진행률**: 5% (1/20 주요 작업 완료)
- **현재 단계**: Phase 0 - 프로젝트 초기화
- **다음 마일스톤**: Alpha 버전 (기본 API 동작)

## 🚀 빠른 시작 (목표)

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일에 NOTION_TOKEN, OPENAI_API_KEY 입력

# 2. Docker로 실행
docker-compose up -d

# 3. 브라우저에서 접속
open http://localhost:5000
```

## 📝 작업 기록

### 2024-12-11
- [x] spec.md 분석 완료
- [x] TODO.md 작성
- [ ] 프로젝트 구조 초기화 시작

---

*이 문서는 개발 진행에 따라 지속적으로 업데이트됩니다.*