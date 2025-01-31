# -*- mode: Python -*-

load('ext://docker_compose', 'docker_compose')
load('ext://docker', 'docker_build')
load('ext://uibutton', 'cmd_button', 'location')
load('ext://configmap', 'configmap_create', 'configmap_from_dict')
load('ext://namespace', 'namespace_create')

# Enable Docker Compose support
docker_compose('docker-compose.yml')

# Backend service
docker_build(
    'chess-bot-backend',
    context='./backend',
    dockerfile='./backend/Dockerfile',
    target='development',
    live_update=[
        sync('./backend', '/app'),
        run('cd /app && poetry install', trigger=['./backend/pyproject.toml', './backend/poetry.lock']),
    ],
)

# Frontend service
docker_build(
    'chess-bot-frontend',
    context='./frontend',
    dockerfile='./frontend/Dockerfile',
    target='development',
    live_update=[
        sync('./frontend/src', '/app/src'),
        sync('./frontend/public', '/app/public'),
        run('cd /app && yarn install', trigger=['./frontend/package.json', './frontend/yarn.lock']),
    ],
)

# Resource configuration
config.define_string_list('env-vars', args=True)
config.define_bool('debug', args=True)
cfg = config.parse()

# Set up port forwards
k8s_resource('backend', port_forwards='8000:8000')
k8s_resource('frontend', port_forwards='5173:5173')

# Configure resource dependencies
k8s_resource('frontend', resource_deps=['backend'])

# Add health checks
k8s_resource(
    'backend',
    readiness_probe=probe(
        initial_delay_secs=5,
        period_secs=10,
        http_get=http_get_action(
            path='/health',
            port=8000,
        ),
    ),
)

k8s_resource(
    'frontend',
    readiness_probe=probe(
        initial_delay_secs=10,
        period_secs=10,
        http_get=http_get_action(
            path='/',
            port=5173,
        ),
    ),
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

# Add UI buttons for common tasks
cmd_button(
    'Backend Tests',
    argv=['cd', 'backend', '&&', 'poetry', 'run', 'pytest'],
    location=location.NAV,
    icon_name='bug_report',
)

cmd_button(
    'Frontend Tests',
    argv=['cd', 'frontend', '&&', 'yarn', 'test'],
    location=location.NAV,
    icon_name='bug_report',
)

cmd_button(
    'Backend Lint',
    argv=['cd', 'backend', '&&', 'poetry', 'run', 'mypy', '.'],
    location=location.NAV,
    icon_name='rule',
)

cmd_button(
    'Frontend Lint',
    argv=['cd', 'frontend', '&&', 'yarn', 'lint'],
    location=location.NAV,
    icon_name='rule',
)

# Development environment variables
if cfg.get('env-vars'):
    for env_var in cfg.get('env-vars'):
        k8s_yaml(blob(env_var))

# Debug mode
if cfg.get('debug'):
    config.set_bool('debug', True)
    config.set_int('max_parallel_updates', 1) 