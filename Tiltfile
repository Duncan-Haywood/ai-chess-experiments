# -*- mode: Python -*-

# Load required extensions
load('ext://helm_resource', 'helm_resource')
load('ext://docker', 'docker_build')
load('ext://uibutton', 'cmd_button', 'location')
load('ext://local_resource', 'local_resource')

# Cleanup old containers before starting
local_resource(
    name='cleanup',
    cmd='docker ps -aq | xargs docker rm -f || true',
    auto_init=True,
)

# Build images
docker_build(
    'chess-bot-frontend',
    context='./frontend',
    dockerfile='./frontend/Dockerfile',
    target='development',
    live_update=[
        sync('./frontend/src', '/app/src'),
        sync('./frontend/public', '/app/public'),
    ]
)

docker_build(
    'chess-bot-backend',
    context='./backend',
    dockerfile='./backend/Dockerfile',
    target='development',
    live_update=[
        sync('./backend', '/app'),
    ]
)

# Deploy Helm charts
k8s_yaml('k8s/frontend.yaml')
k8s_yaml('k8s/backend.yaml')

# Configure resources
k8s_resource(
    'frontend',
    port_forwards='5173:5173',
    resource_deps=['backend'],
)

k8s_resource(
    'backend',
    port_forwards='8000:8000',
)

# Health check commands
local_resource(
    name='health-check',
    cmd='''
    echo "Checking frontend..." && \
    curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 && \
    echo "\nChecking backend..." && \
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
    ''',
    auto_init=False,
)

# Development tools
local_resource(
    name='backend-tests',
    cmd='cd backend && poetry run pytest',
    deps=['./backend'],
    ignore=['./backend/**/__pycache__'],
    auto_init=False,
)

local_resource(
    name='frontend-tests',
    cmd='cd frontend && yarn test',
    deps=['./frontend/src'],
    ignore=['./frontend/node_modules'],
    auto_init=False,
)

local_resource(
    name='backend-lint',
    cmd='cd backend && poetry run mypy .',
    deps=['./backend'],
    ignore=['./backend/**/__pycache__'],
    auto_init=False,
)

local_resource(
    name='frontend-lint',
    cmd='cd frontend && yarn lint',
    deps=['./frontend/src'],
    ignore=['./frontend/node_modules'],
    auto_init=False,
)

# Watch settings
watch_settings(
    ignore=['./frontend/node_modules', './backend/**/__pycache__']
)