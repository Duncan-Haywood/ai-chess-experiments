import pytest
import subprocess
import os
import logging
import docker
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def docker_client():
    """Create a Docker client."""
    return docker.from_env()

def test_backend_docker_build():
    """Test building the backend Docker image."""
    logger.info("Testing backend Docker build")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    backend_dir = project_root / "backend"
    
    # Build the backend image
    result = subprocess.run(
        ["docker", "build", "-t", "chess-backend:test", "."],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    
    logger.debug("Docker build output: %s", result.stdout)
    if result.stderr:
        logger.error("Docker build errors: %s", result.stderr)
    
    assert result.returncode == 0, f"Backend Docker build failed: {result.stderr}"

def test_frontend_docker_build():
    """Test building the frontend Docker image."""
    logger.info("Testing frontend Docker build")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    frontend_dir = project_root / "frontend"
    
    # Build the frontend image
    result = subprocess.run(
        ["docker", "build", "-t", "chess-frontend:test", "."],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    
    logger.debug("Docker build output: %s", result.stdout)
    if result.stderr:
        logger.error("Docker build errors: %s", result.stderr)
    
    assert result.returncode == 0, f"Frontend Docker build failed: {result.stderr}"

def test_backend_container_health(docker_client):
    """Test that the backend container starts and is healthy."""
    logger.info("Testing backend container health")
    
    # Run the backend container
    container = docker_client.containers.run(
        "chess-backend:test",
        detach=True,
        ports={'8000/tcp': None},  # Let Docker assign a random port
        environment={
            "PYTHONUNBUFFERED": "1",
            "LOG_LEVEL": "DEBUG"
        }
    )
    
    try:
        # Wait for container to be ready
        container.reload()
        logs = container.logs().decode('utf-8')
        logger.debug("Container logs: %s", logs)
        
        # Get the mapped port
        container.reload()
        port = container.ports['8000/tcp'][0]['HostPort']
        
        # Test health endpoint
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://localhost:{port}/health"],
            capture_output=True,
            text=True
        )
        
        assert result.stdout == "200", f"Health check failed: {result.stderr}"
        
    finally:
        # Cleanup
        container.stop()
        container.remove()

def test_frontend_container_health(docker_client):
    """Test that the frontend container starts and serves content."""
    logger.info("Testing frontend container health")
    
    # Run the frontend container
    container = docker_client.containers.run(
        "chess-frontend:test",
        detach=True,
        ports={'3000/tcp': None}  # Let Docker assign a random port
    )
    
    try:
        # Wait for container to be ready
        container.reload()
        logs = container.logs().decode('utf-8')
        logger.debug("Container logs: %s", logs)
        
        # Get the mapped port
        container.reload()
        port = container.ports['3000/tcp'][0]['HostPort']
        
        # Test that the server responds
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://localhost:{port}"],
            capture_output=True,
            text=True
        )
        
        assert result.stdout == "200", f"Frontend health check failed: {result.stderr}"
        
    finally:
        # Cleanup
        container.stop()
        container.remove()

def test_docker_compose():
    """Test that docker-compose brings up both services correctly."""
    logger.info("Testing docker-compose")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Bring up the services
        up_result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        logger.debug("Docker compose up output: %s", up_result.stdout)
        if up_result.stderr:
            logger.error("Docker compose up errors: %s", up_result.stderr)
        
        assert up_result.returncode == 0, f"Docker compose up failed: {up_result.stderr}"
        
        # Wait for services to be ready
        subprocess.run(["sleep", "10"])
        
        # Check backend health
        backend_health = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/health"],
            capture_output=True,
            text=True
        )
        assert backend_health.stdout == "200", "Backend health check failed"
        
        # Check frontend
        frontend_health = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3000"],
            capture_output=True,
            text=True
        )
        assert frontend_health.stdout == "200", "Frontend health check failed"
        
    finally:
        # Cleanup
        down_result = subprocess.run(
            ["docker-compose", "down"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if down_result.stderr:
            logger.error("Docker compose down errors: %s", down_result.stderr)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 