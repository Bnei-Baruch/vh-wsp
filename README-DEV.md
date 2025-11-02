# Virtual Home Development Environment

This workspace provides a unified development environment for the Virtual Home microservices ecosystem.

## 🏗️ Architecture Overview

The development environment includes:

- **vh-srv-profile**: User profile management service
- **vh-srv-events**: Events management service  
- **vh-srv-orders**: Orders and payments service
- **Shared Infrastructure**: PostgreSQL databases, NATS messaging, development tools

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

3. **Verify setup:**
   ```bash
   task dev:status
   ```

## 📋 Available Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Shared PostgreSQL RDBMS |
| NATS | 4222 | Message broker |
| NATS Monitor | 8222 | NATS monitoring interface |

## 🛠️ Development Commands

### Infrastructure Management

```bash
# Start development infrastructure
task dev:up

# Stop development infrastructure  
task dev:stop

# Tear down development infrastructure (containers)
task dev:down

# Clean everything (containers + volumes)
task dev:clean

# View infrastructure logs
task dev:logs

# Check service status
task dev:status
```

### Service Development

```bash
# Run all services locally (requires infrastructure)
task run:all
```

### Database Management

```bash
# Run migrations for all services
task dev:migrate

# Shortcuts to open a psql shell for each service:
task profiles:db:shell
task orders:db:shell
task events:db:shell
```

### Testing

```bash
# Run tests for all services
task test:all

# Run integration tests (infrastructure up first)
task test:integration
```

### Monitoring & Debugging

```bash
# Open NATS monitoring
task dev:nats:monitor

# Check service status
task dev:status
```

## 🔧 Configuration

### Environment Variables

The workspace uses `env.dev` as a template. Copy it to `.env` and customize as needed:

```bash
cp env.dev .env
```

## 🐳 Docker Services

### Infrastructure Services

- **db**: PostgreSQL for all services data
- **nats**: NATS JetStream for messaging

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 5432, 4222, 8222 are available. You can change these in .env
2. **Database connection issues**: Check if infrastructure is running with `task dev:status`
3. **Migration failures**: Ensure databases are healthy before running migrations

### Debugging

```bash
# Check Infra containers logs
task dev:logs

# Open a psql shell for each service:
task profiles:db:shell
task orders:db:shell
task events:db:shell

# Monitor NATS
task dev:nats:monitor
```

### Clean Reset

```bash
# Complete cleanup
./scripts/dev-clean.sh

# Fresh setup
./scripts/dev-setup.sh
```

## 🌐 Frontend Development

The development environment now includes nginx reverse proxy for frontend applications, supporting both hot-reload development and containerized deployment.

### Development Modes

| Mode | Frontend | Backend | Use Case |
|------|----------|---------|----------|
| Frontend Dev | Host (hot-reload) | Containers | FE development, API mocking |
| Backend Dev | Containers | Host (debuggable) | BE development, testing |

### Services and Ports

| Service | Mode | Direct Port | Proxy Port | Access URL |
|---------|------|-------------|------------|------------|
| **Frontend Apps** |
| vh-front | Host | 3000 | 8080 | http://localhost:8080 |
| vh-front | Container | - | 8080 | http://localhost:8080 |
| vh-dash | Host | 3001 | 8080 | http://localhost:8080/dash |
| vh-dash | Container | - | 8080 | http://localhost:8080/dash |
| vh-payment | Host | 3002 | 8080 | http://localhost:8080/pay |
| vh-payment | Container | - | 8080 | http://localhost:8080/pay |
| **Backend APIs** |
| vh-srv-profile | Always Host | 7471 | 9000 | http://localhost:9000/profile/v1 |
| vh-srv-events | Always Host | 7475 | 9000 | http://localhost:9000/events/v1 |
| orders | Always Host | 8185 | 9000 | http://localhost:9000/pay |
| **Infrastructure** |
| PostgreSQL | Container | 5432 | - | localhost:5432 |
| NATS | Container | 4222 | - | localhost:4222 |
| Nginx Proxy | Container | - | 8080, 9000 | - |

### Quick Start - Frontend Dev Mode

For frontend developers who need hot-reload and direct code editing:

```bash
# Start infra + backends (containers) + nginx
cd ~/projects/vh/wsp
task dev:full:host

# Start frontend dev servers (hot-reload)
cd ~/projects/vh/vh-front && yarn start
cd ~/projects/vh/vh-dash && yarn start
cd ~/projects/vh/pay/vh-payment && yarn start

# Access applications
open http://localhost:8080
```

### Quick Start - Backend Dev Mode

For backend developers who need to debug and modify backend services:

```bash
# Start infra + frontends (containers) + nginx
cd ~/projects/vh/wsp
task dev:full:container

# Start backend services for development
cd ~/projects/vh/vh-srv-profile && task run
cd ~/projects/vh/vh-srv-events && task run
cd ~/projects/vh/pay/orders && task run

# Access applications
open http://localhost:8080
```

### Web Proxy Management

```bash
# Start nginx proxy only
task dev:web:up

# Stop nginx proxy
task dev:web:down

# View nginx logs
task dev:web:logs

# Restart nginx (reload config)
task dev:web:restart

# Reload nginx config without restart
task dev:web:reload
```

### How .env.development Works

Each frontend project includes a `.env.development` file that Create React App automatically loads when running `yarn start`:

- `PORT`: Configures webpack dev server port
- `BROWSER=none`: Prevents auto-opening browser tabs
- `PUBLIC_URL`: Configures React Router base path for assets

These files are committed to git and shared by the team.

## Development workflows

### Backend single service
  
Use the standalone infra mode. In the project folder, use `dev:standalone:*` (alias `dev:s:*`) tasks.


```bash
# See the list of tasks 
cd ~/projects/vh/vh-srv-profile && task

# Bring up standalone infra
task dev:s:up

```

Test/run/debug in the IDE or project level tasks (`dev`, `test`, `run`)


### Backend multiple service

Use the shared infra mode in the workspace project.

```bash
# Bring up and prepare shared infra
cd ~/project/vh/wsp && task dev:up dev:migrate
```

Test/run/debug each service individualy in the IDE or project level tasks (`dev`, `test`, `run`)



### Backend with local frontend
Want to drive your backend using the ui? Need a custom ui branch?

Use the workspace project. 
1. Clone the relevant frontends repos
2. Switch to relevant branches
3. Configure env per repo (`config-dev.js`) to point to `localhost:9000` backend
4. In workspace, use the `dev:full:container` task to bring up nginx and web apps containers.

### Frontend 
Either single or multiple apps, you need a backend and keycloak. 
The backend and keycloak you choose must be in sync. Meaning, the backend's DB must have the users matching the keycloak you choose.
Possible combinations:
* External environment, staging or production.
* Local backend, external keycloak.
* Local backend and keycloak. Still not available option.

---
External environment is the easiest. Just have the correct `config-dev.js` and you're good to go.

When it is not good enough?
* Staging is missing data. No payments, no cron jobs, etc...
* Production is great but dangerous. Real payments, real data, even your own user...

---
Local backend, external keycloak, provides greater flexibility and safety but requires more effort.

Use the workspace project.
1. Clone the relevant backend repos
2. Switch to relevant branches
3. Configure env per repo (`.env`) to use the keycloak you choose.
4. In workspace, use the `dev:full:host` task to bring up nginx, backend and infra containers.
5. Optional. Load a production db dump (see `replica` in workspace project). You can modify as much as you want and easily restore again if needed.

--- 

#### Frontend single app

No cross navigation? no problem. Just `yarn start` and access directly. 

#### Frontend multiple apps

Need cross app navigation? use the workspace project.
When you bring up the nginx proxy, you can access all frontend apps via the proxy (`localhost:8080`). This mimic production routing.
Hot reload should still be supported.



## 🤖 Model Context Protocol (MCP) Servers

This workspace includes MCP servers that enable AI assistants (like Cursor AI) to interact with your development environment. These servers provide enhanced capabilities for database queries, code navigation, and development workflow automation.

### Available MCP Servers

All MCP servers are configured in `.cursor/mcp.json` and run via npx commands (on-demand execution).

| Server | Description | Configuration |
|--------|-------------|---------------|
| **PostgreSQL (Profiles)** | Database query access to profiles DB | `.cursor/mcp.json` |
| **PostgreSQL (Orders)** | Database query access to orders DB | `.cursor/mcp.json` |
| **PostgreSQL (Events)** | Database query access to events DB | `.cursor/mcp.json` |
| **Replica (Profiles)** | Read-only access to profiles replica | `.cursor/mcp.json` |
| **Replica (Orders)** | Read-only access to orders replica | `.cursor/mcp.json` |
| **Replica (Events)** | Read-only access to events replica | `.cursor/mcp.json` |
| **GitLab** | GitLab repository access (self-hosted) | `.cursor/mcp.json` |
| **NATS** | NATS JetStream subjects/consumers explorer | `.cursor/mcp.json` |
| **Filesystem** | Enhanced file system operations | `.cursor/mcp.json` |
| **Shell** | Command execution for Taskfile/scripts | `.cursor/mcp.json` |

### Setup

MCP servers are configured in `.cursor/mcp.json` and run automatically via npx when Cursor needs them. No manual startup required - servers are launched on-demand when you interact with the AI assistant.

#### Configuration Requirements

1. **PostgreSQL Connection**: Connection strings are pre-configured in `.cursor/mcp.json`
   - Default: `postgresql://user:password@localhost:5432/{database}?sslmode=disable`
   - Update connection strings in `.cursor/mcp.json` if your PostgreSQL credentials differ

2. **GitLab Token**: Required for GitLab MCP server
   - Create a personal access token at `https://gitlab.bbdev.team/-/profile/personal_access_tokens`
   - Token needs `api` scope
   - Replace `your-gitlab-token-here` in `.cursor/mcp.json`

3. **Filesystem Access**: Configured to access `/Users/edoshor/projects/vh`
   - Adjust path in `.cursor/mcp.json` if your workspace is located elsewhere

### What MCP Servers Enable

- **PostgreSQL Servers**: Query databases, inspect schemas, run migrations, analyze data patterns
- **GitLab Server**: Browse repositories, read issues/MRs, search code, check CI/CD pipelines
- **NATS Server**: Explore JetStream subjects, view consumers, inspect message queues, debug event flows
- **Filesystem Server**: Enhanced file operations, code navigation, multi-directory access
- **Shell Server**: Execute commands, run Taskfile tasks, execute migrations and tests

### Troubleshooting

- **Servers not connecting**: Restart Cursor after configuration changes
- **npx packages downloading slowly**: First run downloads packages - subsequent runs are faster
- **PostgreSQL MCP errors**: Ensure databases are running and accessible
- **GitLab authentication issues**: Verify token has correct scopes and is not expired

For more information, see the [Model Context Protocol documentation](https://modelcontextprotocol.io/).

## 📚 Additional Resources

- [Task Documentation](https://taskfile.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [NATS Documentation](https://docs.nats.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

When adding new services or dependencies:

1. Update `docker-compose.yml`
2. Add service-specific tasks to `Taskfile.yml`
3. Update environment variables in `env.dev`
4. Add initialization scripts if needed
5. Update this documentation
