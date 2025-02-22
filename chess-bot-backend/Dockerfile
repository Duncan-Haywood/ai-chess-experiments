# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Install poetry
ENV POETRY_VERSION=1.6.1
RUN pip install "poetry==${POETRY_VERSION}"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Test stage
FROM builder AS test

WORKDIR /test

# Copy source code and tests
COPY . .

# Run linting and tests
RUN poetry run pylint ai_chess_experiments/ && \
    poetry run mypy ai_chess_experiments/ && \
    poetry run pytest tests/ -v --cov=ai_chess_experiments

# Development stage
FROM python:3.11-slim AS development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Install in development mode
RUN pip install -e .

# Add non-root user
RUN useradd -m -u 1000 chess && \
    chown -R chess:chess /app
USER chess

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use uvicorn with auto-reload for development
CMD ["uvicorn", "ai_chess_experiments.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy Python packages and executables from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 chess && \
    chown -R chess:chess /app

# Switch to non-root user
USER chess

# Install gunicorn
RUN pip install --user gunicorn

# Add local bin to PATH
ENV PATH="/home/chess/.local/bin:${PATH}"

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application with optimized settings
CMD ["gunicorn", "ai_chess_experiments.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "5", "--access-logfile", "-"] 