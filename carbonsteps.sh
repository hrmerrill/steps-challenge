#!/bin/bash
set -e

echo "Deploying new changes from GitHub..."
cd /root/steps-challenge

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

echo "Deployment complete! ✅"
