# Virtual Home Development Environment

This workspace provides a unified development environment for the Virtual Home microservices ecosystem.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Go 1.21+
- Task (https://taskfile.dev/)

### Setup

1. **Clone and navigate to workspace:**
   ```bash
   cd ~/projects/vh
   git clone git@gitlab.bbdev.team:vh/wsp.git
   cd wsp
   ```

2. **Run setup script:**
   ```bash
   ./scripts/dev-setup.sh
   ```
   This will:
   <ol type="a">
   <li>Verify prerequisite tools are installed</li>
   <li>Initialize the workspace environment</li>
   <li>Clone relevant repositories if missing</li>
   </ol>


3. **Get to work!:**
   
   Choose your [work mode](#development-workflows) and get to work.


## 🏗️ Architecture Overview

The development environment supports **full-stack development** including both backend services and multiple front-end applications. It is designed for rapid iteration, integration testing, and real-world simulation with production-like infrastructure.

**Core architecture includes:**

- **Backend Services**: Go-based microservices for profile management, events, orders, and payments, each with its own database schema and business logic.
- **Frontend Applications**: React-based dashboards and web portals (e.g., membership pay, management dashboard), with local development configs for easy frontend-backend integration.
- **Infrastructure**: 
  - Shared PostgreSQL databases for persistent storage
  - NATS message broker for event-driven communication
  - Docker Compose manages service orchestration, networking, and dependencies
  - Taskfile scripts for automated builds, migrations, and test execution
- **Dev Tooling**:
  - Hot reload for Go and frontend code
  - Local configuration files (e.g., `config-dev.js`) for pointing frontends at the dev backend and auth servers
  - MCP-powered tools for advanced database, messaging, GitLab, and shell integration from within the editor

This setup allows you to develop and test backend APIs and frontend UIs together, with support for SSO integration, real API connectivity, and end-to-end workflow simulation.


## 🔄 Development Workflows

This section covers common development scenarios and how to set up your environment for each.

### Backend Development

#### Single Service Development

For working on a single backend service in isolation:

1. **Navigate to the service directory:**
   ```bash
   cd ~/projects/vh/vh-srv-profile  # or vh-srv-events, pay/orders
   ```

2. **Use standalone infrastructure mode:**
   ```bash
   # View available tasks
   task
   
   # Bring up standalone infrastructure (PostgreSQL + NATS)
   task dev:s:up  # or dev:standalone:up
   ```

3. **Run, test, or debug:**
   - Use IDE debugger or run directly: `task run`
   - Run tests: `task test`
   - Run with hot reload: `task dev`

The standalone mode creates isolated infrastructure for that service only.

#### Multiple Services Development

For working with multiple backend services that need to interact:

1. **Start shared infrastructure:**
   ```bash
   cd ~/projects/vh/wsp
   task infra:up
   task backend:migrate
   ```

2. **Run each service individually:**
   ```bash
   # In separate terminals or via IDE:
   cd ~/projects/vh/vh-srv-profile && task run
   cd ~/projects/vh/vh-srv-events && task run
   cd ~/projects/vh/pay/orders && task run
   ```

All services share the same PostgreSQL and NATS instances, enabling integration testing.

#### Backend with Local Frontend

When you need to test your backend changes with a UI:

1. **Clone and configure frontend repositories:**
   ```bash
   # Clone relevant frontends
   cd ~/projects/vh
   git clone git@gitlab.bbdev.team:vh/vh-front.git
   git clone git@gitlab.bbdev.team:vh/vh-dash.git
   # ... etc
   ```

2. **Configure frontend to use local backend:**
   - Edit `config-dev.js` in each frontend repo
   - Point API endpoints to `http://localhost:9000`

3. **Start workspace with frontend containers:**
   ```bash
   cd ~/projects/vh/wsp
   task all:backend:host  # Starts infra + nginx + frontend containers
   ```

4. **Run backend services locally:**
   ```bash
   cd ~/projects/vh/vh-srv-profile && task run
   # ... other services
   ```

Frontend containers will proxy requests to your local backend services.

### Frontend Development

Frontend development requires a backend and Keycloak instance. The backend database must have users matching your Keycloak instance.

#### Environment Options

**Option 1: External Environment (Easiest)**
- Use staging or production backend and Keycloak
- Just configure `config-dev.js` with correct endpoints
- **Pros**: No setup required
- **Cons**: Limited data, no control over backend state

**Option 2: Local Backend + External Keycloak**
- Run backend services locally
- Use external Keycloak (staging/production)
- **Pros**: Full backend control, safe testing
- **Cons**: Requires backend setup

**Option 3: Local Backend + Local Keycloak**
- Not yet available

#### Single Frontend App

For working on a single frontend app without cross-app navigation:

```bash
cd ~/projects/vh/vh-front  # or vh-dash, pay/vh-payment
yarn start
```

Access directly at the dev server port (e.g., `http://localhost:3000`).

#### Multiple Frontend Apps

For cross-app navigation that mimics production:

1. **Start workspace with nginx proxy:**
   ```bash
   cd ~/projects/vh/wsp
   task nginx:up  # For production like routing (cross navigation)
   ```

2. **Run frontend dev servers:**
   ```bash
   cd ~/projects/vh/vh-front && yarn start
   cd ~/projects/vh/vh-dash && yarn start
   cd ~/projects/vh/pay/vh-payment && yarn start
   ```

3. **Access via proxy:**
   - All apps accessible at `http://localhost:8080`
   - Routes: `/`, `/dash`, `/pay`
   - Hot reload still works

#### Local Backend Setup for Frontend

1. **Clone and configure backend repositories:**
   ```bash
   cd ~/projects/vh
   git clone git@gitlab.bbdev.team:vh/vh-srv-profile.git
   # ... clone other backends
   ```

2. **Configure backend to use external Keycloak:**
   - Edit `.env` in each backend repo
   - Set Keycloak URL to staging/production

3. **Start workspace:**
   ```bash
   cd ~/projects/vh/wsp
   task all:frontend:host  # Starts infra + nginx + backend containers
   ```

4. **Optional: Load production database dump:**
   ```bash
   # See replica/ directory for database dumps
   # Modify data as needed, easily restore if needed
   ```

## 📋 Available Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Shared PostgreSQL database |
| NATS | 4222 | NATS message broker |
| NATS Monitor | 8222 | NATS monitoring web interface |
| Nginx (Web) | 8080 | Frontend reverse proxy |
| Nginx (API) | 9000 | Backend API reverse proxy |

## 🛠️ Development Commands

All commands are run from the workspace root (`~/projects/vh/wsp`) unless otherwise specified.

See the full list of available development commands by running:

```bash
task -l
```

This will display all major workspace commands for infrastructure, services, testing, migrations, frontend, backend, and utilities.

## 🔧 Configuration

### Environment Variables

The workspace uses `env.dev` as a template. On first setup, copy it to `.env`:

```bash
cp env.dev .env
```

Key configuration variables:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials
- `POSTGRES_PORT`: Database port (default: 5432)
- `NATS_PORT`: NATS broker port (default: 4222)
- `NGINX_WEB_PORT`: Frontend proxy port (default: 8080)
- `NGINX_API_PORT`: Backend API proxy port (default: 9000)

### Frontend Configuration

Each frontend project uses `config-dev.js` for local development:

- **Location**: `public/config/config-dev.js` or `public/config-dev.js`
- **Purpose**: Points frontend to backend API and Keycloak endpoints
- **Example**: Set API base URL to `http://localhost:9000` for local backend

Frontend projects also include `.env.development` files:
- `PORT`: Webpack dev server port
- `BROWSER=none`: Prevents auto-opening browser
- `PUBLIC_URL`: React Router base path

### Backend Configuration

Each backend service uses `.env` files:
- Database connection strings
- NATS connection details
- Keycloak configuration
- Service-specific settings

## 🐳 Docker Services

Services are organized into Docker Compose profiles. Use `task` commands which handle profiles automatically.

### Profile System

| Profile | Services | Use Case |
|---------|----------|----------|
| `infra` | PostgreSQL, NATS | Infrastructure only |
| `backend` | Backend containers | Backend service containers |
| `web` | Nginx reverse proxy | Proxy services |
| `web-app` | Frontend containers | Frontend application containers |

### Service Details

**Infrastructure (`infra` profile):**
- `db`: PostgreSQL database for all services
- `nats`: NATS JetStream message broker

**Web (`web` profile):**
- `nginx`: Reverse proxy for frontend and API routing

**Backend (`backend` profile):**
- Backend service containers

**Web Apps (`web-app` profile):**
- Frontend application containers

## 🌐 Frontend Development Details

### Development Modes

| Mode | Frontend | Backend | Use Case |
|------|----------|---------|----------|
| Frontend Dev | Host (hot-reload) | Containers | Frontend development |
| Backend Dev | Containers | Host (debuggable) | Backend development |

### Service Ports and URLs

| Service | Direct Port | Proxy Port | Access URL |
|---------|-------------|------------|------------|
| **Frontend Apps** |
| vh-front | 3000 | 8080 | http://localhost:8080 |
| vh-dash | 3001 | 8080 | http://localhost:8080/dash |
| vh-payment | 3002 | 8080 | http://localhost:8080/pay |
| **Backend APIs** |
| vh-srv-profile | 7471 | 9000 | http://localhost:9000/profile/v1 |
| vh-srv-events | 7475 | 9000 | http://localhost:9000/events/v1 |
| orders | 8185 | 9000 | http://localhost:9000/pay |
| **Infrastructure** |
| PostgreSQL | 5432 | - | localhost:5432 |
| NATS | 4222 | - | localhost:4222 |

## 🔍 Troubleshooting

### Common Issues

**Port Conflicts**
- Ensure ports 5432, 4222, 8222, 8080, 9000 are available
- Change ports in `.env` if needed

**Database Connection Issues**
- Verify infrastructure is running: `task infra:status`
- Check database is healthy: `task profiles:db:shell`

**Migration Failures**
- Ensure databases are running before migrations
- Check database logs: `task infra:logs`

**Service Not Starting**
- Check service logs in respective project directories
- Verify environment variables are set correctly
- Ensure infrastructure is running

### Debugging Commands

```bash
# Check infrastructure logs
task infra:logs

# Open database shells
task profiles:db:shell
task orders:db:shell
task events:db:shell

# Monitor NATS
task infra:nats:monitor

# Check service status
task infra:status
```

### Clean Reset

If things get into a bad state:

```bash
# Complete cleanup (removes containers and volumes)
./scripts/dev-clean.sh

# Fresh setup
./scripts/dev-setup.sh
```

## 🤖 Model Context Protocol (MCP) Servers

This workspace includes MCP servers that enable AI assistants (like Cursor AI) to interact with your development environment, providing enhanced capabilities for database queries, code navigation, and workflow automation.

### Available MCP Servers

All MCP servers are configured in `.cursor/mcp.json` and run automatically via npx when needed.

| Server | Description |
|--------|-------------|
| **PostgreSQL (Profiles/Orders/Events)** | Database query access to each service DB |
| **Replica (Profiles/Orders/Events)** | Read-only access to production replicas |
| **GitLab** | GitLab repository access (self-hosted) |
| **NATS** | NATS JetStream subjects/consumers explorer |
| **Filesystem** | Enhanced file system operations |
| **Shell** | Command execution for Taskfile/scripts |

### Setup

MCP servers run automatically - no manual startup required. They launch on-demand when you interact with the AI assistant.

**Configuration Requirements:**

1. **PostgreSQL Connection**: Pre-configured in `.cursor/mcp.json`
   - Default: `postgresql://user:password@localhost:5432/{database}?sslmode=disable`
   - Update if your credentials differ

2. **GitLab Token**: Required for GitLab MCP server
   - Create token at `https://gitlab.bbdev.team/-/profile/personal_access_tokens`
   - Needs `api` scope
   - Replace `your-gitlab-token-here` in `.cursor/mcp.json`

3. **Filesystem Access**: Configured for `/Users/edoshor/projects/vh`
   - Adjust path in `.cursor/mcp.json` if your workspace is elsewhere

### Capabilities

- **PostgreSQL**: Query databases, inspect schemas, run migrations, analyze data
- **GitLab**: Browse repositories, read issues/MRs, search code, check CI/CD
- **NATS**: Explore JetStream subjects, view consumers, debug event flows
- **Filesystem**: Enhanced file operations, code navigation
- **Shell**: Execute commands, run Taskfile tasks, execute migrations and tests

### Troubleshooting

- **Servers not connecting**: Restart Cursor after configuration changes
- **Slow first run**: npx downloads packages on first use - subsequent runs are faster
- **PostgreSQL errors**: Ensure databases are running and accessible
- **GitLab auth issues**: Verify token has correct scopes and is not expired

For more information, see the [Model Context Protocol documentation](https://modelcontextprotocol.io/).

## 📚 Additional Resources

- [Task Documentation](https://taskfile.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [NATS Documentation](https://docs.nats.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

When adding new services or dependencies to the workspace:

1. Update `docker-compose.yml` with new services
2. Add service-specific tasks to `Taskfile.yml`
3. Update environment variables in `env.dev`
4. Add initialization scripts if needed
5. Update this documentation
