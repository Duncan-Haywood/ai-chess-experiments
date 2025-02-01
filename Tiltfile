# -*- mode: Python -*-

load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://docker', 'docker_build')
load('ext://local_resource', 'local_resource')
load('ext://live_update', 'sync', 'run')
load('ext://probe', 'probe')
load('ext://http_get_action', 'http_get_action')

# Frontend
docker_build(
    'frontend',
    context='./frontend',
    dockerfile='./frontend/Dockerfile',
    target='development',
    live_update=[
        sync('./frontend/src', '/app/src'),
        sync('./frontend/public', '/app/public'),
        run('cd /app && yarn install', trigger=['./frontend/package.json', './frontend/yarn.lock']),
    ]
)

# Backend
docker_build(
    'backend',
    context='./backend',
    dockerfile='./backend/Dockerfile',
    target='development',
    live_update=[
        sync('./backend', '/app'),
        run('cd /app && poetry install', trigger=['./backend/pyproject.toml', './backend/poetry.lock']),
    ]
)

# Deploy Helm charts
helm_resource(
    'frontend',
    chart='./charts/frontend',
    flags=[
        '--values=./charts/frontend/values.yaml',
    ],
    image_deps=['frontend'],
    image_keys=[('image.repository', 'image.tag')],
    port_forwards=['5173:3000']
)

helm_resource(
    'backend',
    chart='./charts/backend',
    flags=[
        '--values=./charts/backend/values.yaml',
    ],
    image_deps=['backend'],
    image_keys=[('image.repository', 'image.tag')],
    resource_deps=['frontend'],
    port_forwards=['8000:8000']
)

# Development tools
local_resource(
    'backend-tests',
    cmd='cd backend && poetry run pytest',
    deps=['./backend'],
    ignore=['./backend/**/__pycache__'],
    auto_init=False,
)

local_resource(
    'frontend-tests',
    cmd='cd frontend && yarn test',
    deps=['./frontend/src'],
    ignore=['./frontend/node_modules'],
    auto_init=False,
)

local_resource(
    'backend-lint',
    cmd='cd backend && poetry run mypy .',
    deps=['./backend'],
    ignore=['./backend/**/__pycache__'],
    auto_init=False,
)

local_resource(
    'frontend-lint',
    cmd='cd frontend && yarn lint',
    deps=['./frontend/src'],
    ignore=['./frontend/node_modules'],
    auto_init=False,
)