# Use Python 3.11 slim image for Railway compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy environment example file
COPY .env.example .env.example

# Create necessary directories with proper permissions
RUN mkdir -p /app/chroma_db /app/logs && \
    chmod 755 /app/chroma_db /app/logs

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Railway will set PORT dynamically)
EXPOSE 8000

# Health check for Railway (use Railway's dynamic PORT)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application with dynamic port
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"]