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
# START DEVELOPMENT INFRASTRUCTURE
# =============================================================================

echo "🐳 Starting development infrastructure..."

# Start infrastructure services
task dev:up

echo "⏳ Waiting for services to be ready..."
sleep 15

# =============================================================================
# VERIFY DEVELOPMENT INFRASTRUCTURE
# =============================================================================

echo "🔍 Verifying development infrastructure..."

# Check if services are running
task dev:status

echo ""
echo "🎉 Development environment infrastructure setup complete!"
echo ""
echo "📋 Available services:"
echo "   • Shared PostgreSQL:   localhost:${DB_PORT:-5432} (database)"
echo "   • Shared NATS:    localhost:${NATS_PORT:-4222} (monitoring: localhost:${NATS_MONITOR_PORT:-8222})"
echo ""
echo "🚀 Quick start commands:"
echo "   • task dev:up           - Start all infrastructure"
echo "   • task dev:stop         - Stop infrastructure (keep data)"
echo "   • task dev:down         - Stop and remove infrastructure"
echo "   • task dev:status       - Check service status"
echo ""
echo "📚 For more commands, run: task --list"

# TODO (edo):
# clone all vh-* repositories
# configure .env file for each service
# run database migrations for each service (dev:migrate task)