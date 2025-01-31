FROM --platform=linux/arm64 python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry using pip (more reliable than installer script)
RUN pip install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

# Final stage
FROM --platform=linux/arm64 python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy only necessary files
COPY ai_chess_experiments ./ai_chess_experiments
COPY .env ./.env

# Set Python to run in optimized mode
ENV PYTHONOPTIMIZE=1
ENV PYTHONUNBUFFERED=1

# Run as non-root user for better security
RUN useradd -m -u 1000 bot
USER bot

# Run the bot
CMD ["python", "-OO", "ai_chess_experiments/bot_runner.py"] 