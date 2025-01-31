#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "$1" in
    "start")
        echo -e "${GREEN}Starting chess bot...${NC}"
        docker-compose up -d
        echo -e "${GREEN}Bot started! Check logs with './manage.sh logs'${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}Stopping chess bot...${NC}"
        docker-compose down
        ;;
    "restart")
        echo -e "${YELLOW}Restarting chess bot...${NC}"
        docker-compose restart
        ;;
    "logs")
        echo -e "${GREEN}Showing chess bot logs...${NC}"
        if [ "$2" == "--tail" ]; then
            docker-compose logs -f --tail=100
        else
            docker-compose logs -f
        fi
        ;;
    "build")
        echo -e "${GREEN}Building chess bot container...${NC}"
        docker-compose build --no-cache
        ;;
    "status")
        echo -e "${GREEN}Chess bot status:${NC}"
        docker-compose ps
        echo -e "\n${GREEN}Container resources:${NC}"
        docker stats --no-stream chess-bot
        ;;
    "update")
        echo -e "${YELLOW}Updating chess bot...${NC}"
        git pull
        docker-compose build --no-cache
        docker-compose down
        docker-compose up -d
        echo -e "${GREEN}Bot updated and restarted!${NC}"
        ;;
    "clean")
        echo -e "${YELLOW}Cleaning up old containers and images...${NC}"
        docker-compose down
        docker system prune -f
        echo -e "${GREEN}Cleanup complete!${NC}"
        ;;
    "benchmark")
        echo -e "${GREEN}Running engine benchmarks...${NC}"
        if [ "$2" == "--compare" ]; then
            echo "Comparing all engines..."
            docker-compose run --rm chess-bot poetry run python -m ai_chess_experiments.benchmark.run_benchmark --engines random minimax --compare
        else
            echo "Benchmarking minimax engine..."
            docker-compose run --rm chess-bot poetry run python -m ai_chess_experiments.benchmark.run_benchmark --engines minimax
        fi
        ;;
    *)
        echo -e "${RED}Usage: $0 {start|stop|restart|logs|build|status|update|clean|benchmark}${NC}"
        echo
        echo "Commands:"
        echo "  start     - Start the chess bot"
        echo "  stop      - Stop the chess bot"
        echo "  restart   - Restart the chess bot"
        echo "  logs      - Show bot logs (use --tail for last 100 lines)"
        echo "  build     - Rebuild the container"
        echo "  status    - Show bot status and resource usage"
        echo "  update    - Update bot from git and restart"
        echo "  clean     - Clean up old containers and images"
        echo "  benchmark - Run engine benchmarks (use --compare to compare engines)"
        exit 1
        ;;
esac 