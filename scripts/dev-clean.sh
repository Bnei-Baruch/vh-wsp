#!/bin/bash

# =============================================================================
# Virtual Home Development Environment Cleanup Script
# =============================================================================

set -e

echo "🧹 Cleaning Virtual Home Development Environment..."

# =============================================================================
# STOP AND REMOVE CONTAINERS
# =============================================================================

echo "🛑 Stopping and removing containers..."

# Stop all development containers
task dev:down 2>/dev/null || echo "ℹ️  No containers to stop"

# Clean up containers and volumes
task dev:clean

# =============================================================================
# REMOVE DOCKER VOLUMES
# =============================================================================

echo "🗑️  Removing Docker volumes..."

# Remove development volumes
docker volume rm vh-dev-db_data 2>/dev/null || echo "ℹ️  db volume not found"
docker volume rm vh-dev-nats_data 2>/dev/null || echo "ℹ️  nats volume not found"

# =============================================================================
# REMOVE DOCKER NETWORKS
# =============================================================================

echo "🌐 Removing Docker networks..."

# Remove development network
docker network rm vh-dev-network 2>/dev/null || echo "ℹ️  vh-dev-network not found"

# =============================================================================
# CLEAN UP LOCAL FILES
# =============================================================================

echo "📁 Cleaning up local files..."

# Remove environment file if it exists
if [ -f .env ]; then
    rm .env
    echo "✅ Removed .env file"
fi

echo ""
echo "🎉 Development environment cleanup complete!"
echo ""
echo "💡 To start fresh, run: ./scripts/dev-setup.sh"
