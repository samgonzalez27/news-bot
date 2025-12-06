#!/bin/bash
# =============================================================================
# News Digest API - Docker Entrypoint Script
# =============================================================================
# Handles container startup:
#   1. Wait for database to be ready
#   2. Run database migrations/initialization
#   3. Start the application
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_MAX_RETRIES="${DB_MAX_RETRIES:-30}"
DB_RETRY_INTERVAL="${DB_RETRY_INTERVAL:-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Logging functions
# -----------------------------------------------------------------------------
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# -----------------------------------------------------------------------------
# Wait for database to be ready
# -----------------------------------------------------------------------------
wait_for_db() {
    log_info "Waiting for database at ${DB_HOST}:${DB_PORT}..."
    
    local retries=0
    while [ $retries -lt $DB_MAX_RETRIES ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            log_info "Database is ready!"
            return 0
        fi
        
        retries=$((retries + 1))
        log_warn "Database not ready (attempt ${retries}/${DB_MAX_RETRIES}). Waiting ${DB_RETRY_INTERVAL}s..."
        sleep "$DB_RETRY_INTERVAL"
    done
    
    log_error "Database did not become ready in time"
    return 1
}

# -----------------------------------------------------------------------------
# Initialize database (create tables if they don't exist)
# -----------------------------------------------------------------------------
init_database() {
    log_info "Initializing database tables..."
    
    python -c "
import asyncio
from src.database import init_db

async def main():
    await init_db()
    print('Database initialization complete')

asyncio.run(main())
"
    
    if [ $? -eq 0 ]; then
        log_info "Database tables initialized successfully"
    else
        log_error "Failed to initialize database tables"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Seed initial data (interests)
# -----------------------------------------------------------------------------
seed_data() {
    log_info "Seeding initial data..."
    
    python -c "
import asyncio
from src.database import get_async_session_maker
from src.services.interest_service import InterestService

async def main():
    session_maker = get_async_session_maker()
    async with session_maker() as db:
        service = InterestService(db)
        created = await service.seed_interests()
        await db.commit()
        if created > 0:
            print(f'Seeded {created} interests')
        else:
            print('Interests already seeded')

asyncio.run(main())
"
    
    if [ $? -eq 0 ]; then
        log_info "Data seeding complete"
    else
        log_warn "Data seeding had issues (non-fatal)"
    fi
}

# -----------------------------------------------------------------------------
# Health check - verify the app can connect to database
# -----------------------------------------------------------------------------
verify_db_connection() {
    log_info "Verifying database connection..."
    
    python -c "
import asyncio
from src.database import get_engine

async def main():
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(__import__('sqlalchemy').text('SELECT 1'))
        result.fetchone()
    print('Database connection verified')

asyncio.run(main())
"
    
    if [ $? -eq 0 ]; then
        log_info "Database connection verified successfully"
    else
        log_error "Failed to verify database connection"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Main entrypoint
# -----------------------------------------------------------------------------
main() {
    log_info "Starting News Digest API entrypoint..."
    log_info "Environment: ${APP_ENV:-development}"
    
    # Step 1: Wait for database
    wait_for_db || exit 1
    
    # Step 2: Verify database connection
    verify_db_connection || exit 1
    
    # Step 3: Initialize database tables
    init_database || exit 1
    
    # Step 4: Seed initial data
    seed_data
    
    log_info "Startup checks complete. Starting application..."
    
    # Step 5: Execute the main command (passed as arguments)
    exec "$@"
}

# Run main with all script arguments
main "$@"
