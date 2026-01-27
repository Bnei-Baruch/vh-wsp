---
description: Code generation in backend services
alwaysApply: false
---
## Architecture & Design Patterns

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.go                              │
│                    (godotenv autoload)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      cmd/root.go                             │
│              (Cobra CLI with subcommands)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      api/app.go                              │
│         (App struct, Initialize(), Run(), Shutdown())        │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌─────────┐    ┌───────────┐    ┌──────────┐
    │ Handlers│    │ Middleware│    │  Routes  │
    └────┬────┘    └───────────┘    └──────────┘
         │
         ▼
    ┌─────────┐
    │  Repo   │ ◄── Interface-based repository
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │PostgreSQL│
    └─────────┘
```

### Core Design Principles

1. **Layered Architecture**: `cmd` → `api` → `repo` with clear separation
2. **Interface-Driven Design**: Repository interfaces for testability
3. **Stateless Services**: All state persisted in PostgreSQL
4. **Event-Driven Communication**: NATS for inter-service messaging
5. **Context Propagation**: Request context flows through all layers

### Key Frameworks & Libraries

| Purpose | Library | Version |
|---------|---------|---------|
| CLI | `github.com/spf13/cobra` | Latest |
| Web Framework | `github.com/gin-gonic/gin` | v1.9.x |
| Database | `github.com/jackc/pgx/v4` | v4.18.x |
| Migrations | `github.com/golang-migrate/migrate/v4` | v4.15.x |
| Config | `github.com/kelseyhightower/envconfig` | v1.4.0 |
| Auth | `github.com/coreos/go-oidc/v3` | v3.10.x |
| Testing | `github.com/stretchr/testify` | v1.9.x |
| Messaging | `github.com/nats-io/nats.go` | v1.33.x |
| Error Tracking | `github.com/getsentry/sentry-go` | v0.27.x |
| Nullable Types | `github.com/volatiletech/null/v9` | v9.0.x |

---

## File Organization

### Standard Project Structure

```
service/
├── main.go                    # Entry point, imports cmd
├── go.mod                     # Module definition
├── go.sum                     # Dependency checksums
├── Dockerfile                 # Multi-stage build
├── Taskfile.yml               # Task runner commands
├── docker-compose.yml         # Production compose
├── docker-compose.dev.yml     # Development compose
├── docker-compose.local.yml   # Local development
├── env.dev                    # Environment template
├── env.example                # Environment documentation
├── README.md                  # Service documentation
│
├── api/                       # HTTP layer
│   ├── app.go                 # App struct, lifecycle methods
│   ├── *_handlers.go          # Route handlers by domain
│   ├── *_api.go               # API struct with handler methods
│   ├── permissions.go         # Authorization helpers
│   └── middleware/            # HTTP middleware
│       ├── auth.go            # JWT/OIDC authentication
│       ├── logging.go         # Request logging
│       ├── recovery.go        # Panic recovery
│       ├── sentry.go          # Error tracking
│       └── events.go          # Event context builder
│
├── cmd/                       # CLI commands
│   ├── root.go                # Root command setup
│   ├── server.go              # HTTP server command
│   ├── migrate.go             # Migration command
│   └── *.go                   # Additional commands
│
├── common/                    # Shared utilities
│   ├── config.go              # Environment configuration
│   ├── consts.go              # Constants and context keys
│   └── errors.go              # Sentinel errors
│
├── repo/                      # Data access layer
│   ├── *_repository.go        # Repository interface definition
│   ├── common.go              # DB connection, migrations
│   ├── *_helpers.go           # Query implementations
│   └── types.go               # Domain types and DTOs
│
├── events/                    # Event handling
│   ├── types.go               # Event type definitions
│   ├── emitter.go             # Event emission logic
│   └── handlers.go            # Event handlers (NATS)
│
├── domain/                    # Business logic (optional)
│   └── events_handler.go      # Domain event processing
│
├── pkg/                       # Reusable packages
│   ├── keycloak/              # Keycloak client
│   ├── utils/                 # Helper functions
│   └── testutil/              # Test utilities
│
├── db/                        # Database assets
│   └── migrations/            # SQL migration files
│
├── internal/                  # Internal packages
│   └── mocks/                 # Generated mocks
│
└── misc/                      # Scripts and cron files
```

### File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Handlers | `*_handlers.go` or `handler_*.go` | `orders_handlers.go`, `handler_get.go` |
| Repository | `*_helpers.go` or `db_*.go` | `accounts_helpers.go`, `db_get.go` |
| Tests | `*_test.go` | `handler_get_test.go` |
| Migrations | `NN_description.up.sql` / `.down.sql` | `06_membership_table.up.sql` |
| Types | `types.go` | `repo/types.go` |

---

## Naming Conventions

### Go Code

```go
// Package names: lowercase, single word
package api
package repo
package common

// Types: PascalCase
type ProfileManager struct {}
type OrdersRepository interface {}
type IDTokenClaims struct {}

// Public functions/methods: PascalCase
func NewApp() *App {}
func (a *App) Initialize() {}

// Private functions/methods: camelCase
func (p *ProfileManager) getProfiles(c *gin.Context) {}
func parseToken(r *http.Request) string {}

// Constants: PascalCase for exported, camelCase for unexported
const ServiceName = "vh-srv-profile"
const CtxAuthClaims = "AUTH_CLAIMS"

// Variables: camelCase
var Config = new(envConfig)
var entropy io.Reader
```

### Handler Naming

```go
// Pattern: handle[Action][Entity]
func (o *OrdersAPI) handleOrderGetByID(c *gin.Context) {}
func (o *OrdersAPI) handleOrderDeleteByID(c *gin.Context) {}
func (o *OrdersAPI) handleCreateOffline(c *gin.Context) {}
func (o *OrdersAPI) handlePaymentFetch(c *gin.Context) {}

// Alternative pattern for CRUD
func (p *ProfileManager) get(c *gin.Context) {}
func (p *ProfileManager) create(c *gin.Context) {}
func (p *ProfileManager) update(c *gin.Context) {}
func (p *ProfileManager) delete(c *gin.Context) {}
```

### Repository Naming

```go
// Pattern: [Action][Entity](ctx, params...)
func (db *ProfileDB) GetProfile(ctx context.Context, keycloakID uuid.UUID) (User, error) {}
func (db *ProfileDB) CreateProfile(ctx context.Context, user UserInput) error {}
func (db *ProfileDB) UpdateProfile(ctx context.Context, keycloakID uuid.UUID, user UserInput) error {}
func (db *ProfileDB) DeleteProfile(ctx context.Context, keycloakID uuid.UUID) error {}

// For multiple items: Get[Plural] or GetAll[Entity]
func (db *ProfileDB) GetMultipleProfiles(ctx context.Context, skip, limit int, ...) ([]User, error) {}
func (o *OrdersDB) GetAllOrders(ctx context.Context, ...) (*[]Order, error) {}

// Soft delete pattern
func (o *OrdersDB) SoftDeleteOrderByID(ctx context.Context, orderID int) error {}
```

### JSON Field Naming

```go
// Use snake_case for JSON tags
type Order struct {
    ID        int       `json:"ID"`                    // Exception: ID fields may be uppercase
    CreatedAt null.Time `json:"created_at"`
    UpdatedAt null.Time `json:"updated_at"`
    DeletedAt null.Time `json:"deleted_at"`
    AccountID null.Int  `json:"AccountID"`             // Legacy: some fields use PascalCase
    UserKey   string    `json:"user_key"`              // Preferred: snake_case
}

// Request/Response types
type userResponse struct {
    UserID              *uuid.UUID `json:"user_id"`
    KeycloakID          *uuid.UUID `json:"keycloak_id"`
    FirstNameVernacular *string    `json:"first_name_vernacular"`
    PrimaryEmail        *string    `json:"primary_email"`
}
```

### Database Naming

```sql
-- Tables: snake_case, plural
CREATE TABLE users (...);
CREATE TABLE phone_numbers (...);
CREATE TABLE membership (...);

-- Columns: snake_case
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    keycloak_id UUID,
    first_name_latin VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Migrations: numbered prefix with descriptive name
-- 00_initial_struct.up.sql
-- 06_membership_table.up.sql
-- 27_martial_status.up.sql
```

---

## API & Interface Conventions

### Route Structure

```go
// Version prefixed routes
baseV1Path := a.gEngine.Group("/v1")
baseV2Path := a.gEngine.Group("/v2")

// Resource-based grouping
account := baseV2Path.Group("/account")
{
    account.POST("/", handler.handleCreateAccount)
    account.GET("/:id", handler.handleGetAccount)
    account.GET("/email/:email", handler.handleGetAccountByEmail)
    account.PATCH("/:id", handler.handlePatchAccount)
    account.DELETE("/:id", handler.handleDeleteAccount)
    account.DELETE("/:id/hard", handler.handleHardDeleteAccount)
}
baseV2Path.GET("/accounts", handler.handleFetchAccounts)  // Collection outside group
```

### Standard Response Format

```go
// Success responses
c.JSON(http.StatusOK, gin.H{
    "message": "Fetched!",
    "data":    result,
    "success": true,
})

c.JSON(http.StatusCreated, gin.H{
    "message": "Created!",
    "data":    id,
    "success": true,
})

// Simple success (no data)
c.JSON(http.StatusOK, gin.H{
    "message": "Deleted!",
    "success": true,
})

// Error responses
c.JSON(http.StatusBadRequest, gin.H{
    "error":   "Invalid id! Accepted value is INTEGER",
    "success": false,
})

// Status-only responses (no body)
c.Status(http.StatusNotFound)
c.Status(http.StatusForbidden)
c.Status(http.StatusInternalServerError)
```

### Request Handling Pattern

```go
func (o *OrdersAPI) handleOrderGetByID(c *gin.Context) {
    // 1. Authorization check (early return)
    if !o.HasAnyRole(c, common.RoleRoot, common.RoleAdmin) {
        return
    }

    // 2. Parameter extraction and validation
    id, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error":   "Invalid id! Accepted value is INTEGER",
            "success": false,
        })
        return
    }

    // 3. Business logic via repository
    order, err := o.repo.GetOrderByID(c.Request.Context(), uint(id))
    if err != nil {
        // 4. Error handling with specific cases
        if errors.Is(err, pgx.ErrNoRows) {
            c.Status(http.StatusNotFound)
        } else {
            c.Status(http.StatusInternalServerError)
            _ = c.Error(fmt.Errorf("repo.GetOrderByID: %w", err))
        }
        return
    }

    // 5. Success response
    c.JSON(http.StatusOK, gin.H{
        "message": "Fetched!",
        "data":    order,
        "success": true,
    })
}
```

### Query Parameters

```go
// Pagination
skip := c.Query("skip")    // Default: "0"
limit := c.Query("limit")  // Default: "10" or "100"

// Filtering
email := c.Query("email")
status := c.Query("status")
country := c.Query("country")

// Sorting
orderBy := c.Query("o-payment-date")  // Values: "asc", "desc"
createdAt := c.Query("created")       // Values: "asc", "desc"

// Boolean filters (string comparison)
membership := c.Query("membership")   // Values: "true", "false"
if membership != "" && membership != "false" && membership != "true" {
    c.JSON(http.StatusBadRequest, gin.H{
        "error": "Invalid membership value! Accepted value is either true or false",
    })
    return
}
```

---

## Error Handling

### Sentinel Errors

```go
// common/errors.go
package common

import "fmt"

var (
    ErrProfileNotFound = fmt.Errorf("no profile found for keycloak id")
    ErrUserNotFound    = fmt.Errorf("no profile found")
    ErrNotFound        = fmt.Errorf("not found")
    ErrInvalidValues   = fmt.Errorf("invalid values")
    ErrNoRowsAffected  = fmt.Errorf("no rows affected")
)
```

### Error Wrapping

```go
// Always wrap errors with context
if err != nil {
    return fmt.Errorf("migrate.New: %w", err)
}

// In handlers, use c.Error() for logging
if err != nil {
    c.Status(http.StatusInternalServerError)
    _ = c.Error(fmt.Errorf("repo.GetProfile: %w", err))
    return
}
```

### Error Checking Pattern

```go
// Use errors.Is for sentinel errors
if errors.Is(err, common.ErrProfileNotFound) {
    c.Status(http.StatusNotFound)
    return
}

// Use errors.Is for package errors
if errors.Is(err, pgx.ErrNoRows) {
    c.Status(http.StatusNotFound)
    return
}

// Combined error handling
if err != nil {
    if errors.Is(err, common.ErrInvalidValues) {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
    } else if errors.Is(err, common.ErrNoRowsAffected) {
        c.Status(http.StatusNotFound)
    } else {
        c.Status(http.StatusInternalServerError)
        _ = c.Error(fmt.Errorf("repo.PatchOrderByID: %w", err))
    }
    return
}
```

### Fatal Errors

```go
// Use LogFatal for unrecoverable errors during startup
func LogFatal(msg string, args ...any) {
    slog.Error(msg, args...)
    os.Exit(1)
}

// Usage
if err != nil {
    utils.LogFatal("sentry.Init", slog.Any("err", err))
}
```

---

## Security & Authentication

### Middleware Stack Order

```go
a.gEngine.Use(
    middleware.Logging(),      // 1. Request logging
    middleware.Recovery(),     // 2. Panic recovery
    sentrygin.New(...),        // 3. Sentry integration
    middleware.Sentry(),       // 4. Sentry context
)

// Debug-only CORS
if gin.IsDebugging() {
    a.gEngine.Use(cors.New(cors.Config{
        AllowAllOrigins:  true,
        AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
        AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
        AllowCredentials: true,
    }))
}

a.gEngine.Use(
    middleware.EventsBuilder(),  // 5. Event context
    middleware.TokenSource(),    // 6. Token extraction
    middleware.Authentication(), // 7. JWT validation
)
```

### Role Definitions

```go
// common/consts.go
const (
    RoleRoot           = "vh_root"           // Service-to-service + super admin
    RoleAdmin          = "vh_admin"          // Admin users
    RoleHelpHaverAdmin = "vh_helphaver_admin" // HelpHaver admin
)

var RoleAnyAdmin = []string{RoleRoot, RoleAdmin, RoleHelpHaverAdmin}
```

### Permission Checking

```go
// Check if user has any of the specified roles
func (o *OrdersAPI) HasAnyRole(c *gin.Context, roles ...string) bool {
    claims := c.Request.Context().Value(common.CtxAuthClaims).(*middleware.IDTokenClaims)
    if !claims.HasAnyRole(roles...) {
        c.Status(http.StatusForbidden)
        return false
    }
    return true
}

// Check if user is the subject OR has admin role
func (p *ProfileManager) isSubjectOrHasAnyRole(c *gin.Context, keycloakID string, roles ...string) bool {
    claims := c.Request.Context().Value(common.CtxAuthClaims).(*middleware.IDTokenClaims)
    if claims.Sub != keycloakID && !claims.HasAnyRole(roles...) {
        c.Status(http.StatusForbidden)
        return false
    }
    return true
}

// Check ownership via database lookup
func (o *OrdersAPI) isUserOrHasAnyRole(c *gin.Context, userID string, roles ...string) bool {
    claims := c.Request.Context().Value(common.CtxAuthClaims).(*middleware.IDTokenClaims)
    if claims.HasAnyRole(roles...) {
        return true
    }
    match, err := o.repo.IsSubjectID(c.Request.Context(), claims.Sub, userID)
    if err != nil {
        c.Status(http.StatusInternalServerError)
        _ = c.Error(fmt.Errorf("repo.IsSubjectID: %w", err))
        return false
    }
    if !match {
        c.Status(http.StatusForbidden)
        return false
    }
    return true
}
```

### Handler Authorization Pattern

```go
func (o *OrdersAPI) handleOrderDeleteByID(c *gin.Context) {
    // Admin-only endpoint
    if !o.HasAnyRole(c, common.RoleRoot, common.RoleAdmin) {
        return  // Status already set by HasAnyRole
    }
    // ... rest of handler
}

func (p *ProfileManager) get(c *gin.Context) {
    keycloakID := c.Param("keycloak_id")
    // User can access their own profile OR admin can access any
    if !p.isSubjectOrHasAnyRole(c, keycloakID, common.RoleAnyAdmin...) {
        return
    }
    // ... rest of handler
}
```

---

## Database & Data Access

### Repository Interface Pattern

```go
// repo/orders_repository.go
type OrdersRepository interface {
    // Account operations
    GetAccount(ctx context.Context, id int, email string) (*Account, error)
    CreateAccount(ctx context.Context, a Account) (int, error)
    PatchAccount(ctx context.Context, req Account, accountID int) error
    SoftDeleteAccount(ctx context.Context, accountID int) error

    // Order operations
    GetOrderByID(ctx context.Context, orderID uint) (*Order, error)
    CreateV2Order(ctx context.Context, order Order) (int, error)
    SoftDeleteOrderByID(ctx context.Context, orderID int) error

    Close()
}

// Implementation
type OrdersDB struct {
    *pgxpool.Pool
    eventEmitter   events.EventEmitter
    profileService profiles.ProfileService
}
```

### Connection Management

```go
// repo/common.go
func GetDBURL() string {
    return fmt.Sprintf("postgres://%s:%s@%s:%s/%s",
        url.QueryEscape(common.Config.PgUser),
        url.QueryEscape(common.Config.PgPass),
        common.Config.PgHost,
        common.Config.PgPort,
        url.QueryEscape(common.Config.PgDbName))
}

func NewOrdersDB(ctx context.Context, eventEmitter events.EventEmitter) (*OrdersDB, error) {
    pool, err := pgxpool.Connect(ctx, GetDBURL())
    if err != nil {
        return nil, fmt.Errorf("pgxpool.Connect: %w", err)
    }
    return &OrdersDB{Pool: pool, eventEmitter: eventEmitter}, nil
}
```

### Query Patterns

```go
// Single row query
func (db *ProfileDB) GetProfile(ctx context.Context, keycloakID uuid.UUID) (User, error) {
    var profile User
    if err := db.QueryRow(ctx, `
        SELECT user_id, updated_at, created_at, ...
        FROM users
        WHERE keycloak_id = $1 AND deleted = false
    `, keycloakID).Scan(
        &profile.UserID,
        &profile.UpdatedAt,
        &profile.CreatedAt,
        // ...
    ); err != nil {
        if err == pgx.ErrNoRows {
            return User{}, common.ErrProfileNotFound
        }
        return User{}, err
    }
    return profile, nil
}

// Multiple rows query
func (db *ProfileDB) GetMultipleProfiles(ctx context.Context, skip, limit int, ...) ([]User, error) {
    rows, err := db.Query(ctx, query, args...)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var profiles []User
    for rows.Next() {
        var p User
        if err := rows.Scan(...); err != nil {
            return nil, err
        }
        profiles = append(profiles, p)
    }
    return profiles, rows.Err()
}
```

### Migration Pattern

```go
func SyncDBStructInsertionAndMigrations() error {
    slog.Info("running db migrations")
    m, err := migrate.New(MigrationFiles(), GetDBURL()+"?sslmode=disable")
    if err != nil {
        return fmt.Errorf("migrate.New: %w", err)
    }
    defer m.Close()

    if err := m.Up(); err != nil {
        if err == migrate.ErrNoChange {
            slog.Info("no changes in migrations")
            return nil
        }
        return fmt.Errorf("migrate.Up: %w", err)
    }
    return nil
}
```

### Nullable Types

```go
// Use volatiletech/null for nullable database fields
import "github.com/volatiletech/null/v9"

type Order struct {
    ID        int          `json:"ID"`
    Amount    null.Float64 `json:"Amount"`
    Currency  null.String  `json:"Currency"`
    Status    null.String  `json:"Status"`
    CreatedAt null.Time    `json:"created_at"`
}

// Creating nullable values
order := Order{
    Amount:   null.Float64From(15.00),
    Currency: null.StringFrom("USD"),
    Status:   null.StringFrom(common.OrderStatusPaid),
}

// Checking if valid
if order.Amount.Valid {
    fmt.Println(order.Amount.Float64)
}
```

---

## Testing Policy

### Test File Organization

```go
// Tests live next to source files
api/
├── handler_get.go
├── handler_get_test.go
├── handler_common_test.go  // Shared test utilities
└── app_test.go             // Integration test setup
```

### Test Setup Pattern

```go
// api/app_test.go
func NewTestApp(t *testing.T) *App {
    gin.SetMode(gin.TestMode)
    a := NewApp()
    a.SetEmitter(new(events.NoopEmitter))

    dbURL, err := testutil.NewTestOrdersDB(t, context.Background())
    require.Nil(t, err)

    a.repo, err = repo.NewOrdersDBUrl(context.Background(), dbURL, a.eventEmitter)
    require.Nil(t, err)

    a.ordersAPI = NewOrdersAPI(a.repo)
    a.gEngine = gin.Default()
    a.gEngine.Use(middleware.Logging(), middleware.EventsBuilder())
    a.initRoutes()
    return a
}

func CloseTestApp(a *App) {
    a.Shutdown()
}
```

### HTTP Test Helpers

```go
func GET(t *testing.T, a *App, path string, expectedCode int) gin.H {
    return do(t, a, "GET", path, nil, expectedCode, DoOptions{})
}

func POST(t *testing.T, a *App, path string, request interface{}, expectedCode int) gin.H {
    return do(t, a, "POST", path, request, expectedCode, DoOptions{})
}

func POST_ROOT(t *testing.T, a *App, path string, request interface{}, expectedCode int) gin.H {
    return do(t, a, "POST", path, request, expectedCode, DoOptions{isRoot: true})
}
```

### Mock Pattern

```go
// handler_common_test.go
type storageMock struct {
    mock.Mock
}

func (m *storageMock) GetProfile(ctx context.Context, keycloakID uuid.UUID) (repo.User, error) {
    args := m.Called(ctx, keycloakID)
    return args.Get(0).(repo.User), args.Error(1)
}

// Test usage
func Test_profileHandler_get_succeeds(t *testing.T) {
    sm := storageMock{}
    sm.On("GetProfile", mock.Anything, userID).
        Return(repo.User{...}, nil)

    profile := NewProfileManager(&sm)
    g := gin.New()
    g.GET("/:keycloak_id", profile.get)

    r := NewRequestAsRoot(http.MethodGet, "/11000000-0000-0000-0000-000000000000", nil)
    w := httptest.NewRecorder()
    g.ServeHTTP(w, r)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, expectedJSON, w.Body.String())
}
```

### Test Naming

```go
// Pattern: Test_[receiver]_[method]_[scenario]
func Test_profileHandler_get_succeeds(t *testing.T) {}
func Test_profileHandler_get_returns_404_when_storage_returns_errProfileNotFound(t *testing.T) {}
func Test_profileHandler_get_returns_500_when_storage_returns_error(t *testing.T) {}
func Test_get_order_by_id(t *testing.T) {}
func Test_duplicate_card_key(t *testing.T) {}
```

### Running Tests

```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run specific package
go test ./api/...

# Run with race detection
go test -race ./...
```

---

## Configuration Management

### Environment Configuration

```go
// common/config.go
package common

import "github.com/kelseyhightower/envconfig"

type envConfig struct {
    // Application settings
    Port string `envconfig:"APP_PORT" default:"7471"`
    Mode string `envconfig:"APP_MODE" default:"debug"`
    Env  string `envconfig:"APP_ENV" default:"dev"`

    // Database
    PgHost   string `envconfig:"DB_HOST" default:"localhost"`
    PgPort   string `envconfig:"DB_PORT" default:"5432"`
    PgUser   string `envconfig:"DB_USER" default:"postgres"`
    PgPass   string `envconfig:"DB_PASSWORD" default:"password"`
    PgDbName string `envconfig:"DB_NAME" default:"profiledb"`

    // External services
    NatsUrl              string `envconfig:"NATS_URL"`
    KeycloakServerUrl    string `envconfig:"KEYCLOAK_SERVER_URL"`
    KeycloakRealm        string `envconfig:"KEYCLOAK_REALM"`
    KeycloakClientID     string `envconfig:"KEYCLOAK_CLIENT_ID"`
    KeycloakClientSecret string `envconfig:"KEYCLOAK_CLIENT_SECRET"`
}

var Config = new(envConfig)

func LoadConfig() {
    envconfig.Process("LIST", Config)
}
```

### Loading Configuration

```go
// main.go - autoload .env
import _ "github.com/joho/godotenv/autoload"

// cmd/root.go - initialize config
func init() {
    cobra.OnInitialize(common.LoadConfig)
}
```

### Environment Files

```bash
# env.dev - Development defaults (committed)
APP_PORT=7471
APP_MODE=debug
APP_ENV=dev
DB_HOST=localhost
DB_PORT=5432
...

# .env - Local overrides (gitignored)
# Copy from env.dev and customize
```

---

## Logging & Observability

### Structured Logging

```go
// Use log/slog (standard library)
import "log/slog"

// Basic logging
slog.Info("db connected and migrated")
slog.Error("failed to connect", slog.Any("err", err))

// Context-aware logging
func LogFor(ctx context.Context) *slog.Logger {
    if val := ctx.Value(common.CtxLogger); val != nil {
        if logger, ok := val.(*slog.Logger); ok {
            return logger
        }
    }
    return slog.Default()
}

// Usage in handlers
logger := utils.LogFor(c.Request.Context())
logger.Info("processing request", slog.String("user_id", userID))
```

### Request Logging Middleware

```go
func Logging() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()

        // Generate or extract request ID
        rid := c.GetHeader("X-Request-ID")
        if rid == "" {
            rid = nuid.Next()
        }
        c.Header("X-Request-ID", rid)

        // Create logger with request ID
        logger := slog.Default().With(slog.String("request_id", rid))
        ctx := context.WithValue(c.Request.Context(), common.CtxRequestID, rid)
        ctx = context.WithValue(ctx, common.CtxLogger, logger)
        c.Request = c.Request.WithContext(ctx)

        c.Next()

        // Log request completion
        level := slog.LevelInfo
        if c.Writer.Status() >= 400 {
            level = slog.LevelWarn
        }
        if c.Writer.Status() >= 500 {
            level = slog.LevelError
        }

        logger.LogAttrs(ctx, level, "request",
            slog.String("method", c.Request.Method),
            slog.String("path", c.Request.URL.Path),
            slog.Int("status", c.Writer.Status()),
            slog.Duration("latency", time.Since(start)),
        )
    }
}
```

### Sentry Integration

```go
// Initialize in app startup
err := sentry.Init(sentry.ClientOptions{
    Release:          common.GitSHA,
    Environment:      common.Config.Env,
    AttachStacktrace: true,
})

// Capture errors
func SentryFor(ctx context.Context) *sentry.Hub {
    if val := sentry.GetHubFromContext(ctx); val != nil {
        return val
    }
    return sentry.CurrentHub()
}

// Usage
utils.SentryFor(ctx).CaptureException(err)
```

---

## Events & Messaging

### Event Types

```go
// events/types.go
const (
    ActorSystem = common.ServiceName

    ComponentAPI           = "api"
    ComponentMembership    = "membership_invalidator"

    TypeCreateProfile     = "create_profile"
    TypeUpdateProfile     = "update_profile"
    TypeDeleteProfile     = "delete_profile"
)

type Event struct {
    ID        string                 `json:"id"`
    Type      string                 `json:"type"`
    Timestamp time.Time              `json:"timestamp"`
    Component string                 `json:"component"`
    Actor     string                 `json:"actor"`
    RequestID string                 `json:"request_id,omitempty"`
    Payload   map[string]interface{} `json:"payload"`
}
```

### Event Emitter Pattern

```go
// Interface
type EventEmitter interface {
    Emit(ctx context.Context, events ...Event)
    Close(ctx context.Context)
}

// NoopEmitter for testing
type NoopEmitter struct{}
func (e *NoopEmitter) Emit(_ ...Event)         {}
func (e *NoopEmitter) Close(_ context.Context) {}

// SimpleEmitter with handlers
type SimpleEmitter struct {
    handlers []EventHandler
}

func (e *SimpleEmitter) Emit(ctx context.Context, events ...Event) {
    for _, event := range events {
        for _, handler := range e.handlers {
            handler.Handle(ctx, event)
        }
    }
}
```

### Event Builder

```go
type EventBuilder interface {
    BuildEvent(eventType string, payload map[string]interface{}) Event
}

// Access from context in repository
func (o *OrdersDB) emitEvent(ctx context.Context, eventType string, payload map[string]interface{}) {
    builder := ctx.Value(common.CtxEventBuilder).(events.EventBuilder)
    event := builder.BuildEvent(eventType, payload)
    o.eventEmitter.Emit(ctx, event)
}
```

---

## Dependencies & Imports

### Import Organization

```go
import (
    // Standard library
    "context"
    "fmt"
    "log/slog"
    "net/http"
    "time"

    // Third-party packages
    "github.com/getsentry/sentry-go"
    "github.com/gin-gonic/gin"
    "github.com/jackc/pgx/v4"

    // Internal packages (project-specific)
    "gitlab.bbdev.team/vh/vh-srv-profile/api/middleware"
    "gitlab.bbdev.team/vh/vh-srv-profile/common"
    "gitlab.bbdev.team/vh/vh-srv-profile/repo"
)
```

### Core Dependencies

```go
// go.mod
module gitlab.bbdev.team/vh/vh-srv-profile

go 1.21

require (
    // Web framework
    github.com/gin-gonic/gin v1.9.1
    github.com/gin-contrib/cors v1.5.0

    // Database
    github.com/jackc/pgx/v4 v4.18.3
    github.com/golang-migrate/migrate/v4 v4.15.2
    github.com/lib/pq v1.10.9

    // Configuration
    github.com/kelseyhightower/envconfig v1.4.0
    github.com/joho/godotenv v1.3.0

    // CLI
    github.com/spf13/cobra v1.7.0

    // Authentication
    github.com/coreos/go-oidc/v3 v3.10.0

    // Messaging
    github.com/nats-io/nats.go v1.33.1

    // Monitoring
    github.com/getsentry/sentry-go v0.27.0
    github.com/hellofresh/health-go/v5 v5.5.3

    // Testing
    github.com/stretchr/testify v1.9.0

    // Utilities
    github.com/volatiletech/null/v9 v9.0.0
    github.com/satori/go.uuid v1.2.0
    github.com/oklog/ulid/v2 v2.1.1
)
```

---

## Development Workflow

### Task Runner (Taskfile.yml)

```yaml
version: '3'

tasks:
  dev:
    desc: Start development in shared mode
    cmds:
      - task: env:init
      - task: db:ensure
      - task: run

  test:
    desc: Run all Go tests
    cmds:
      - go test ./...

  build:
    desc: Build the service
    cmds:
      - go build .

  run:
    desc: Run the service
    cmds:
      - go run ./... server

  docker:build:
    desc: Build Docker image
    cmds:
      - docker build -t vh-srv-profile .

  db:ensure:
    desc: Ensure database exists
    cmds:
      - task: db:wait
      - docker exec vh-dev-db psql -U {{.POSTGRES_USER}} ...

  db:shell:
    desc: Open PostgreSQL shell
    cmds:
      - docker exec -it vh-dev-db psql -U {{.POSTGRES_USER}} -d {{.POSTGRES_DB}}
```

### Docker Build

```dockerfile
FROM golang:1.21 AS base

ARG GIT_SHA
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .
RUN CGO_ENABLED=0 go build -ldflags "-X gitlab.bbdev.team/vh/vh-srv-profile/common.GitSHA=${GIT_SHA}" -o profile .

FROM alpine:latest
RUN apk --no-cache add curl
COPY db /db
COPY --from=base /app/profile /
EXPOSE 7471
CMD ["./profile", "server"]
```

### Git SHA Injection

```go
// common/consts.go
var GitSHA string = "local"  // Set at build time via -ldflags

// cmd/root.go
rootCmd.SetVersionTemplate(fmt.Sprintf("%s -- %s", common.ServiceName, common.GitSHA))

// Build command
go build -ldflags "-X gitlab.bbdev.team/vh/vh-srv-profile/common.GitSHA=${GIT_SHA}"
```

---

## Health Checks

### Health Endpoint Pattern

```go
func (a *App) initHealth() {
    h, _ := health.New(health.WithComponent(health.Component{
        Name:    common.ServiceName,
        Version: common.GitSHA,
    }), health.WithChecks(
        health.Config{
            Name:    "postgres",
            Timeout: time.Second * 5,
            Check:   healthpgx.New(healthpgx.Config{DSN: repo.GetDBURL()}),
        },
    ))

    if common.Config.NatsUrl != "" {
        h.Register(health.Config{
            Name:    "nats",
            Timeout: time.Second * 5,
            Check:   healthnats.New(healthnats.Config{DSN: common.Config.NatsUrl}),
        })
    }

    a.gEngine.GET("/health", func(c *gin.Context) {
        h.HandlerFunc(c.Writer, c.Request)
    })
}
```

---

## Quick Reference

### Creating a New Handler

```go
func (o *OrdersAPI) handleNewEndpoint(c *gin.Context) {
    // 1. Auth check
    if !o.HasAnyRole(c, common.RoleRoot, common.RoleAdmin) {
        return
    }

    // 2. Bind request
    var req RequestType
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // 3. Call repository
    result, err := o.repo.DoSomething(c.Request.Context(), req)
    if err != nil {
        if errors.Is(err, common.ErrNotFound) {
            c.Status(http.StatusNotFound)
        } else {
            c.Status(http.StatusInternalServerError)
            _ = c.Error(fmt.Errorf("repo.DoSomething: %w", err))
        }
        return
    }

    // 4. Return response
    c.JSON(http.StatusOK, gin.H{"data": result, "success": true})
}
```

### Creating a New Repository Method

```go
func (db *OrdersDB) GetSomethingByID(ctx context.Context, id int) (*Something, error) {
    var result Something
    err := db.QueryRow(ctx, `
        SELECT id, name, created_at
        FROM something
        WHERE id = $1 AND deleted_at IS NULL
    `, id).Scan(&result.ID, &result.Name, &result.CreatedAt)

    if err != nil {
        if err == pgx.ErrNoRows {
            return nil, common.ErrNotFound
        }
        return nil, err
    }
    return &result, nil
}
```

### Adding a New Migration

```bash
# Create migration files
touch db/migrations/NN_description.up.sql
touch db/migrations/NN_description.down.sql
```

```sql
-- NN_description.up.sql
CREATE TABLE new_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- NN_description.down.sql
DROP TABLE IF EXISTS new_table;
```

