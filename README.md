# Chess Bot Experiments

A chess bot that plays locally with a web interface to watch games in real-time.

## Features

- **Local Self-Play**
  - Watch bot vs bot matches in real-time
  - Debug games move by move
  - Experiment with different engine settings

- **Web Interface**
  - Real-time board visualization with 250ms polling
  - Game state tracking
  - Health checks and automatic reconnection

## Setup

1. Install dependencies:
```bash
# Backend
cd backend
poetry install

# Frontend
cd ../frontend
npm install
```

2. Start the application:
```bash
# Using Docker Compose (recommended)
docker compose up --build --detach --watch

# Or manually:
# Terminal 1 (Backend)
cd backend
poetry run python -m ai_chess_experiments.bot_runner

# Terminal 2 (Frontend)
cd frontend
npm run dev
```

## Viewing Games

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

- `/health` - Health check endpoint
- `/api/game` - Get current game state
- `/api/move/{move_uci}` - Make a move
- `/api/new_game` - Start a new game

## Development

- Backend: Python with FastAPI
- Frontend: React with Vite
- Real-time updates via polling
- Docker Compose with watch mode and health checks

## Configuration

Key settings in `backend/pyproject.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.11"
python-chess = "^1.999"
fastapi = "^0.109.0"
uvicorn = "^0.27.0"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request 