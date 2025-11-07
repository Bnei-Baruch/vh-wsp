#!/bin/bash

# =============================================================================
# Virtual Home Development Environment Setup Script
# =============================================================================

set -e

echo "🚀 Setting up Virtual Home Development Environment..."

# =============================================================================
# CHECK PREREQUISITES
# =============================================================================

echo "📋 Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Task is installed
if ! command -v task &> /dev/null; then
    echo "❌ Task is not installed. Please install Task first:"
    echo "   https://taskfile.dev/installation/"
    exit 1
fi

echo "✅ All prerequisites are installed."

# =============================================================================
# CREATE ENVIRONMENT FILE
# =============================================================================

echo "📝 Creating environment configuration..."

if [ ! -f .env ]; then
    cp env.dev .env
    echo "✅ Created .env file from env.dev template"
else
    echo "ℹ️  .env file already exists, skipping creation"
fi


# =============================================================================
# CLONE REPOSITORIES
# =============================================================================

echo ""
echo "🔄 Clone repositories"

cat <<EOF
Which repositories do you want to clone?
  1) Backend (profiles, orders, events)
  2) Frontend (front, dash, payments, payments-bo)
  3) All (default: clone all backend AND frontend repositories)
  4) None (skip repo cloning)
EOF
read -p "Choose [1/2/3/4]: " clone_choice

BACKEND_REPOS=(
  "vh-srv-profile"
  "pay/orders"
  "vh-srv-events"
)
FRONTEND_REPOS=(
  "vh-front"
  "vh-dash"
  "pay/vh-payment"
  "pay/vh-payment-bo"
  "vh-events-bo"
)
ALL_REPOS=("${BACKEND_REPOS[@]}" "${FRONTEND_REPOS[@]}")

case "$clone_choice" in
  1)
    TARGET_REPOS=("${BACKEND_REPOS[@]}")
    ;;
  2)
    TARGET_REPOS=("${FRONTEND_REPOS[@]}")
    ;;
  3)
    TARGET_REPOS=("${ALL_REPOS[@]}")
    ;;
  4)
    TARGET_REPOS=()
    ;;
  *)
    TARGET_REPOS=("${ALL_REPOS[@]}")
    ;;
esac

if [ ${#TARGET_REPOS[@]} -eq 0 ]; then
  echo "No repositories selected, skipping repository clone."
else
  echo "Cloning repositories..."
  GITLAB_SSH_BASE="git@gitlab.bbdev.team:vh"
  for REPO in "${TARGET_REPOS[@]}"; do
    if [ -d "../$REPO" ]; then
      echo "✔️  $REPO directory already exists, skipping clone."
    else
      echo "➡️  Cloning $REPO..."
      git clone "$GITLAB_SSH_BASE/$REPO.git" ../$REPO
    fi
  done

  echo "✅ Repository clone step complete."
fi

# =============================================================================
# INITIALIZE BACKEND PROJECTS ENVIRONMENT VARIABLES
# =============================================================================

echo "🐳 Starting development infrastructure..."

# Initialize backend projects environment variables
task backend:env:init

echo "✅ Backend projects environment initialization (env:init) complete."

# =============================================================================
# NEXT STEPS
# =============================================================================

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Choose your development mode and start developing!"
echo "Check the README.md for more details."
