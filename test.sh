#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error counter
ERRORS=0

# Function to handle errors
handle_error() {
    local name=$1
    local error_msg=$2
    echo -e "${RED}✗ $name failed: $error_msg${NC}\n"
    ERRORS=$((ERRORS + 1))
}

# Function to run a command and check its exit status
run_test() {
    local name=$1
    local cmd=$2
    echo -e "${YELLOW}Running $name...${NC}"
    
    # Run command and capture output
    output=$(eval $cmd 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $name passed${NC}\n"
    else
        handle_error "$name" "$output"
        return 1
    fi
}

echo -e "${GREEN}Starting comprehensive test suite...${NC}\n"

# Frontend Tests
cd frontend || exit 1

echo -e "${GREEN}Frontend Tests${NC}"
echo "===================="

# Clean install
echo "Cleaning npm cache and node_modules..."
rm -rf node_modules
npm cache clean --force

# Install dependencies
echo "Installing frontend dependencies..."
if ! npm ci; then
    handle_error "Frontend dependency installation" "npm ci failed"
    exit 1
fi

# Type checking
run_test "TypeScript type check" "npm run type-check"

# Linting
run_test "ESLint check" "npm run lint"

# Unit tests
run_test "Frontend unit tests" "npm run test"

# E2E tests
run_test "Frontend E2E tests" "npm run test:e2e"

# Backend Tests
cd ../backend || exit 1

echo -e "${GREEN}Backend Tests${NC}"
echo "=================="

# Clean Python environment
echo "Cleaning Python environment..."
rm -rf .venv
rm -rf __pycache__
find . -type d -name "__pycache__" -exec rm -r {} +

# Create fresh virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install poetry and dependencies
echo "Installing poetry and dependencies..."
pip install --upgrade pip
pip install poetry
poetry install

# Type checking
run_test "MyPy type check" "poetry run mypy ."

# Code formatting
run_test "Black formatting check" "poetry run black --check ."
run_test "isort import check" "poetry run isort --check-only ."

# Unit tests with coverage
run_test "Backend unit tests" "poetry run pytest --cov=ai_chess_experiments --cov-report=term-missing"

# Integration Tests
cd .. || exit 1

echo -e "${GREEN}Integration Tests${NC}"
echo "==================="

# Clean Docker environment
echo "Cleaning Docker environment..."
docker compose down -v
docker system prune -f

# Build and start services
echo "Building and starting services..."
if ! docker compose up -d --build; then
    handle_error "Docker build" "Failed to build and start services"
    docker compose logs
    exit 1
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        break
    fi
    if [ $i -eq 30 ]; then
        handle_error "Service startup" "Services failed to start within timeout"
        docker compose logs
        exit 1
    fi
    sleep 1
done

# Run integration tests
run_test "API health check" "curl -f http://localhost:8000/health"
run_test "Frontend health check" "curl -f http://localhost:5173"
run_test "Engine integration tests" "poetry run pytest backend/tests/test_engines.py -v"

# Cleanup
echo "Cleaning up..."
docker compose down -v

# Final report
echo -e "\n${GREEN}Test Summary${NC}"
echo "=============="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS test suites failed${NC}"
    docker compose logs
    exit 1
fi 