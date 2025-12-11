# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Architecture

This is a **Notion to RAG API** service built with Python/FastAPI that:
1. Fetches documents from Notion workspace
2. Processes and chunks text for optimal retrieval
3. Generates embeddings using OpenAI's API
4. Stores vectors in ChromaDB for similarity search
5. Provides REST API endpoints for RAG-based queries

### Core Components

- **FastAPI Backend** (`backend/app/`): Async REST API server
- **Notion Integration** (`services/notion_service.py`): Handles Notion API interactions
- **RAG Pipeline** (`services/rag_service.py`): Query processing with GPT-4
- **Vector Database** (`services/vector_db.py`): ChromaDB for vector storage
- **Text Processing** (`utils/text_processor.py`): Chunking and normalization

## 🛠️ Common Development Commands

### Setup and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
cd backend && python -m uvicorn app.main:app --reload --port 5000

# Run with Docker
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Testing
```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_api.py

# Run with coverage
pytest --cov=backend/app backend/tests/

# Run with verbose output
pytest -v backend/tests/
```

### Database Management
```bash
# Clear ChromaDB (development)
rm -rf chroma_db/

# Backup ChromaDB
tar -czf chroma_backup.tar.gz chroma_db/

# Restore ChromaDB
tar -xzf chroma_backup.tar.gz
```

## 🔑 Key Design Patterns

### Service Layer Pattern
All business logic is encapsulated in service classes:
- `NotionService`: Notion API operations
- `EmbeddingService`: OpenAI embedding generation
- `VectorDBService`: Vector database operations
- `IndexingService`: Document indexing orchestration
- `RAGService`: RAG query processing

### Async/Await Throughout
The entire codebase uses async/await for optimal performance:
- All API endpoints are async
- Service methods use `async/await`
- Database operations are async-compatible

### Configuration Management
- Environment variables via `pydantic-settings`
- Centralized configuration in `core/config.py`
- Type-safe settings with validation

### Error Handling Strategy
- Structured logging with `structlog`
- Graceful degradation for external service failures
- Retry logic with exponential backoff for API calls

## 📁 Important File Locations

### Configuration
- `backend/app/core/config.py`: All settings and environment variables
- `.env.example`: Template for environment variables

### API Endpoints
- `backend/app/api/query.py`: Main query endpoint
- `backend/app/api/refresh.py`: Index refresh endpoint
- `backend/app/api/auth.py`: Authentication logic

### Core Services
- `backend/app/services/notion_service.py`: Notion document fetching
- `backend/app/services/rag_service.py`: RAG query processing
- `backend/app/services/vector_db.py`: Vector database interface

### Text Processing
- `backend/app/utils/text_processor.py`: Chunking and text utilities

## 🚀 Adding New Features

### Adding a New API Endpoint
1. Create new router file in `backend/app/api/`
2. Define Pydantic models for request/response
3. Implement async endpoint function
4. Include router in `main.py`

### Adding a New Vector Database
1. Create new class implementing `VectorDBInterface` in `vector_db.py`
2. Add configuration options in `config.py`
3. Update `VectorDBService` initialization logic

### Extending Text Processing
1. Add new methods to `TextProcessor` class
2. Consider token limits for embeddings
3. Maintain chunk overlap for context preservation

## ⚠️ Critical Considerations

### Rate Limits
- **Notion API**: 3 requests per second
- **OpenAI API**: Varies by tier, implement backoff
- **Embedding Batch Size**: Max 100 texts per request

### Security
- Never commit `.env` files
- Rotate JWT secrets regularly
- Validate all user inputs
- Use API keys for production

### Performance
- Batch embedding generation for efficiency
- Use async operations throughout
- Implement caching where appropriate
- Monitor vector DB size

## 🧪 Testing Strategy

### Unit Tests
- Test individual service methods
- Mock external API calls
- Validate data transformations

### Integration Tests
- Test API endpoint flows
- Verify database operations
- Check authentication/authorization

### End-to-End Tests
- Full refresh → index → query flow
- Cross-service interactions
- Error handling scenarios

## 📚 External Dependencies

### Core Libraries
- **FastAPI**: Web framework
- **notion-client**: Official Notion SDK
- **openai**: OpenAI API client
- **chromadb**: Vector database
- **tiktoken**: Token counting

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **structlog**: Structured logging

## 🔄 Typical Development Workflow

1. **Feature Development**
   - Create feature branch
   - Implement service layer first
   - Add API endpoint
   - Write tests
   - Update documentation

2. **Debugging Issues**
   - Check logs in `docker-compose logs`
   - Verify environment variables
   - Test individual services
   - Use breakpoints with `import pdb; pdb.set_trace()`

3. **Performance Optimization**
   - Profile with `cProfile`
   - Monitor API response times
   - Optimize database queries
   - Implement caching layers

## 💡 Next Steps for Development

### High Priority
- [ ] Implement React frontend
- [ ] Add comprehensive test suite
- [ ] Set up CI/CD pipeline
- [ ] Add request caching with Redis

### Medium Priority
- [ ] Support for Qdrant/Pinecone
- [ ] Implement user management
- [ ] Add query history tracking
- [ ] Create admin dashboard

### Future Enhancements
- [ ] Multi-language support
- [ ] Custom embedding models
- [ ] Webhook for Notion updates
- [ ] GraphQL API support

## 🐛 Known Issues

1. **Notion Block Types**: Not all Notion block types are fully supported
2. **Large Documents**: Performance degrades with very large pages (>10MB)
3. **Rate Limiting**: No sophisticated rate limit handling yet
4. **Cache Invalidation**: Manual refresh required for Notion updates

## 📞 Getting Help

- Check `TODO.md` for development roadmap
- Review `spec.md` for original requirements
- See API docs at `/docs` when server is running
- Use structured logging for debugging