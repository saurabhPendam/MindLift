#!/bin/bash

# Migration Verification Script
# This script checks for migration issues before running migrations

echo "=================================="
echo "Migration Verification Script"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

WEBAPP_DIR="/home/mindlift/mindlift/webapp"

# Check if webapp directory exists
if [ ! -d "$WEBAPP_DIR" ]; then
    print_error "Webapp directory not found: $WEBAPP_DIR"
    exit 1
fi

cd $WEBAPP_DIR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found"
    print_info "Run: python3.10 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

print_info "Checking Django installation..."
python -c "import django; print(f'Django version: {django.get_version()}')" || {
    print_error "Django not installed"
    exit 1
}

print_success "Django is installed"

# Check database connection
print_info "Checking database connection..."
python manage.py dbshell --command="SELECT 1;" 2>/dev/null || {
    print_error "Cannot connect to database"
    print_info "Please check your .env file and MySQL service"
    exit 1
}
print_success "Database connection OK"

# List current migrations
print_info "Current migrations in database:"
echo ""
python manage.py showmigrations chatbot

echo ""
print_info "Checking for migration conflicts..."

# Check for duplicate migration names
DUPLICATES=$(find chatbot/migrations/ -name "*.py" ! -name "__init__.py" -exec basename {} \; | sort | uniq -d)

if [ -n "$DUPLICATES" ]; then
    print_error "Duplicate migration files found:"
    echo "$DUPLICATES"
    echo ""
    print_info "Please resolve duplicates before proceeding"
    exit 1
else
    print_success "No duplicate migrations found"
fi

# Check for unapplied migrations
print_info "Checking for unapplied migrations..."
UNAPPLIED=$(python manage.py showmigrations chatbot | grep "\[ \]" | wc -l)

if [ $UNAPPLIED -gt 0 ]; then
    print_info "Found $UNAPPLIED unapplied migration(s)"
    echo ""
    python manage.py showmigrations chatbot | grep "\[ \]"
    echo ""
else
    print_success "All migrations are applied"
fi

# Check for migration dependencies
print_info "Checking migration dependencies..."
python manage.py makemigrations --check --dry-run 2>&1 | grep -q "No changes detected" && {
    print_success "No new migrations needed"
} || {
    print_info "New migrations may be needed"
    echo ""
    python manage.py makemigrations --dry-run
    echo ""
}

# Check for specific known issues in your migrations
echo ""
print_info "Checking for known migration issues..."

# Issue 1: Duplicate index names
if grep -r "audit_timestamp_idx\|audit_category_idx\|msg_crisis_idx\|report_deleted_idx" chatbot/migrations/*.py 2>/dev/null | grep -v "Remove"; then
    print_error "Found duplicate index definitions"
    print_info "These should only be created once or removed"
fi

# Issue 2: mood_score field (should be removed)
if grep -r "mood_score" chatbot/migrations/*.py 2>/dev/null; then
    print_info "Found mood_score references in migrations"
    print_info "This field should be removed (migration 0009)"
fi

# List all migration files in order
echo ""
print_info "Migration files in chatbot/migrations/:"
ls -1 chatbot/migrations/*.py | grep -v __init__ | grep -v __pycache__

# Show migration graph
echo ""
print_info "Migration dependency graph:"
python manage.py showmigrations chatbot --plan

# Summary
echo ""
echo "=================================="
print_info "Summary"
echo "=================================="
echo ""

# Count migrations
TOTAL_MIGRATIONS=$(find chatbot/migrations/ -name "*.py" ! -name "__init__.py" | wc -l)
APPLIED_MIGRATIONS=$(python manage.py showmigrations chatbot | grep "\[X\]" | wc -l)

echo "Total migration files: $TOTAL_MIGRATIONS"
echo "Applied migrations: $APPLIED_MIGRATIONS"
echo "Unapplied migrations: $UNAPPLIED"

echo ""
print_info "Next steps:"
echo ""
echo "1. Review the migration list above"
echo "2. If everything looks good, run: python manage.py migrate"
echo "3. If there are issues, fix them before migrating"
echo ""

# Suggested fix for common issues
if [ $UNAPPLIED -gt 0 ]; then
    echo ""
    print_info "To apply migrations:"
    echo "  cd $WEBAPP_DIR"
    echo "  source venv/bin/activate"
    echo "  python manage.py migrate"
    echo ""
fi

# Check for manual SQL migrations
if ls chatbot/migrations/*remove*.py 2>/dev/null | grep -q "0006\|0008\|0009"; then
    echo ""
    print_info "Note: Some migrations contain RemoveIndex operations"
    print_info "These may fail if indexes don't exist - this is normal"
    echo ""
fi

deactivate
