#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default to docker-compose
DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-compose}

function start_compose() {
    echo -e "${GREEN}Starting with Docker Compose...${NC}"
    docker compose up -d
}

function start_kubernetes() {
    echo -e "${GREEN}Starting with Kubernetes...${NC}"
    
    # Check if minikube is running
    if ! minikube status > /dev/null 2>&1; then
        echo "Starting minikube..."
        minikube start
    fi
    
    # Build images
    echo "Building images..."
    eval $(minikube docker-env)
    docker build -t chess-bot-frontend:latest frontend/
    docker build -t chess-bot-backend:latest backend/
    
    # Apply k8s configs
    echo "Applying Kubernetes configs..."
    kubectl apply -f k8s/
    
    # Wait for deployment
    echo "Waiting for deployment..."
    kubectl wait --for=condition=available deployment/chess-bot --timeout=300s
    
    # Port forward
    echo "Setting up port forwarding..."
    kubectl port-forward svc/chess-bot 5173:80 8000:8000 &
}

function stop_compose() {
    echo -e "${YELLOW}Stopping Docker Compose...${NC}"
    docker compose down
}

function stop_kubernetes() {
    echo -e "${YELLOW}Stopping Kubernetes...${NC}"
    kubectl delete -f k8s/
    pkill -f "port-forward"
}

function show_logs() {
    if [ "$DEPLOYMENT_MODE" = "compose" ]; then
        docker compose logs -f
    else
        kubectl logs -l app=chess-bot -f
    fi
}

function show_status() {
    if [ "$DEPLOYMENT_MODE" = "compose" ]; then
        docker compose ps
    else
        kubectl get pods,svc,hpa
    fi
}

# Parse command line arguments
case "$1" in
    start)
        if [ "$DEPLOYMENT_MODE" = "compose" ]; then
            start_compose
        else
            start_kubernetes
        fi
        ;;
    stop)
        if [ "$DEPLOYMENT_MODE" = "compose" ]; then
            stop_compose
        else
            stop_kubernetes
        fi
        ;;
    restart)
        if [ "$DEPLOYMENT_MODE" = "compose" ]; then
            stop_compose
            start_compose
        else
            stop_kubernetes
            start_kubernetes
        fi
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status}"
        exit 1
        ;;
esac 