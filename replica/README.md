# Replica Database Management Tool

This tool allows you to load production PostgreSQL dumps into your local development environment using the shared `vh-dev-db` container.

## Setup

1. Place your production dump files (`.dump` format) in the `dumps/` directory
2. Update `manifest.txt` to map database names to dump files:
   ```
   profiles_replica:profiles_prod_20251029.dump
   orders_replica:orders_prod_20251029.dump
   events_replica:events_prod_20251029.dump
   ```

## Usage

All commands are run from the workspace root using the `replica:` prefix:

### Load Databases

```bash
# Load a single database (looks up dump file in manifest)
task replica:load:one DB=profiles_replica

# Load a single database with specific dump file
task replica:load:one DB=test_db DUMP_FILE=my_dump.dump

# Load all databases from manifest
task replica:load:all
```

### Drop Databases

```bash
# Drop a single database
task replica:drop:one DB=profiles_replica

# Drop all databases from manifest
task replica:drop:all
```

### Database Access

```bash
# Open psql shell to a database
task replica:db:shell DB=profiles_replica

# List all databases in manifest
task replica:list
```

## Prerequisites

- The `vh-dev-db` container must be running (start with `task dev:up`)
- Dump files must be in PostgreSQL custom format (`.dump` files created with `pg_dump -Fc`)

## Notes

- **Role Permissions**: The tool automatically suppresses role-related errors when loading production dumps into development environments using `--no-owner` and `--no-privileges` flags
- **Data Integrity**: All data, schema, and constraints are preserved; only ownership and permission settings are ignored

## File Structure

```
replica/
├── Taskfile.yml      # Replica management tasks
├── manifest.txt      # Database name to dump file mapping
├── dumps/            # Directory for .dump files
│   └── .gitkeep      # Ensures directory is tracked in git
└── README.md         # This file
```

## Notes

- Dump files are mounted read-only into the container
- All operations run inside the `vh-dev-db` container using `docker exec`
- Active connections are terminated before dropping databases
- The tool is OS-agnostic and uses shell commands available in most environments
