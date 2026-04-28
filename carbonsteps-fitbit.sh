#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Google Health API Integration Deployment Script
#
# Deploys the Steps Challenge with Google Health API integration from the
# 'fitbit' branch. To roll back to the non-integrated version, run
# carbonsteps.sh (which deploys from main).
#
# Required .env additions for Google Health API:
#   GOOGLE_CLIENT_ID=<your Google Cloud Console client ID>
#   GOOGLE_CLIENT_SECRET=<your client secret>
#   GOOGLE_REDIRECT_URI=https://your-domain.com/api/google-health/callback
#
# Get credentials from:
#   Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID
#   Enable "Google Health API" under APIs & Services → Library
# ---------------------------------------------------------------------------

DEPLOY_BRANCH="fitbit"

cd /root/steps-challenge

# Ensure .env exists — docker-compose.yml requires it for secrets
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy .env.example and fill in real values:" >&2
    echo "  cp .env.example .env" >&2
    exit 1
fi

# Check for Google Health API credentials (warn but don't block)
if ! grep -q "^GOOGLE_CLIENT_ID=" .env 2>/dev/null || [ -z "$(grep '^GOOGLE_CLIENT_ID=' .env | cut -d= -f2-)" ]; then
    echo "⚠️  WARNING: GOOGLE_CLIENT_ID not set in .env"
    echo "   Google Health integration will be disabled until configured."
    echo "   See: https://console.cloud.google.com/ → APIs & Services → Credentials"
    echo ""
fi

echo "Deploying Google Health API integration from branch '${DEPLOY_BRANCH}'..."

# Initialize the repo if we just rsync'd without .git
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/hrmerrill/steps-challenge.git
    git fetch
    git checkout -f -t "origin/${DEPLOY_BRANCH}"
else
    echo "Pulling latest changes from ${DEPLOY_BRANCH}..."
    git fetch origin "${DEPLOY_BRANCH}"
    git reset --hard "origin/${DEPLOY_BRANCH}"
fi

echo "Building and restarting Docker containers..."
docker compose up -d --build

echo "Running database migrations..."
docker compose exec -T backend alembic upgrade head

echo ""
echo "Google Health API deployment complete! ✅"
echo ""
echo "To roll back to the non-integrated version:"
echo "  ./carbonsteps.sh"
echo ""
echo "To configure Google Health API, add these to .env:"
echo "  GOOGLE_CLIENT_ID=<client_id>"
echo "  GOOGLE_CLIENT_SECRET=<client_secret>"
echo "  GOOGLE_REDIRECT_URI=https://your-domain.com/api/google-health/callback"
