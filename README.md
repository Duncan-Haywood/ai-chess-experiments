# Chess Bot Experiments

A chess bot that can play both locally and on Lichess, with a web interface to watch games in real-time.

## Features

- **Local Self-Play**
  - Watch bot vs bot matches in real-time
  - Debug games move by move
  - Experiment with different engine settings

- **Online Play (Lichess)**
  - Play against other players on Lichess
  - Track ELO rating and performance
  - View match history and statistics

- **Web Interface**
  - Real-time board visualization
  - Game statistics (time, moves, etc.)
  - Match history viewer

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up your environment:
```bash
cp .env.example .env
# Add your Lichess API token to .env
```

3. Start the bot:
```bash
# For local self-play with web viewer
docker compose up chess-bot

# For online Lichess games
docker compose up chess-bot-online
```

## Viewing Games

- Local self-play: http://localhost:8000
- Online games: http://localhost:8000/online
- Debug port: 5678 (for VS Code debugging)

## API Endpoints

- `/api/games/current` - View active games
- `/api/games/history` - View past games
- `/api/stats` - Get bot statistics
  - ELO rating
  - Win/loss ratio
  - Average game length
  - Most common openings

## Development

- Written in Python with FastAPI
- Real-time updates via WebSocket
- Simple web interface with vanilla JS
- VS Code debugging support

## Configuration

Key settings in `.env`:
```env
LICHESS_API_TOKEN=your_token_here
ENGINE_DEPTH=3
MAX_GAMES=1
TIME_CONTROL=180,2  # 3min + 2sec increment
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request 