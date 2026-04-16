#!/bin/bash
set -e

cd /root/steps-challenge

# Ensure .env exists — docker-compose.yml requires it for secrets
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy .env.example and fill in real values:" >&2
    echo "  cp .env.example .env" >&2
    exit 1
fi

echo "Deploying new changes from GitHub..."

# Initialize the repo if we just rsync'd without .git
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/hrmerrill/steps-challenge.git
    git fetch
    git checkout -f -t origin/main
else
    echo "Pulling latest changes..."
    git fetch origin main
    git reset --hard origin/main
fi

echo "Building and restarting Docker containers..."
docker compose up -d --build

echo "Running database migrations..."
docker compose exec -T backend alembic upgrade head

echo "Deployment complete! ✅"
