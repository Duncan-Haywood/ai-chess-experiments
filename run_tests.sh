#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Running all tests..."

# Run backend tests
echo -e "\n${GREEN}Running Backend Tests${NC}"
cd backend
poetry run pytest -v --cov=ai_chess_experiments tests/

# Run frontend tests
echo -e "\n${GREEN}Running Frontend Tests${NC}"
cd ../frontend
npm run test

# Run E2E tests
echo -e "\n${GREEN}Running E2E Tests${NC}"
npm run test:e2e

# Run Docker tests
echo -e "\n${GREEN}Running Docker Tests${NC}"
cd ../
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Check exit codes
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed${NC}"
    exit 1
fi 