#!/bin/bash

# Database Cleanup Script
# This script helps clean up duplicate tables and migration issues

echo "=================================="
echo "Database Cleanup Script"
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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Database credentials (you should update these)
read -p "Enter MySQL username [mindlift_user]: " DB_USER
DB_USER=${DB_USER:-mindlift_user}

read -sp "Enter MySQL password: " DB_PASS
echo ""

read -p "Enter database name [mindlift_db]: " DB_NAME
DB_NAME=${DB_NAME:-mindlift_db}

# Test connection
mysql -u "$DB_USER" -p"$DB_PASS" -e "USE $DB_NAME;" 2>/dev/null || {
    print_error "Cannot connect to database"
    exit 1
}

print_success "Connected to database"

# Function to execute SQL
execute_sql() {
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "$1" 2>&1
}

# Check for duplicate tables
echo ""
print_info "Checking for tables..."
echo ""

TABLES=$(execute_sql "SHOW TABLES;")
echo "$TABLES"

# Check django_migrations table
echo ""
print_info "Current migrations in database:"
echo ""
execute_sql "SELECT id, app, name, applied FROM django_migrations WHERE app='chatbot' ORDER BY id;"

# Check for duplicate indexes
echo ""
print_info "Checking for indexes..."
echo ""

# Function to check if index exists
check_index() {
    local table=$1
    local index=$2
    execute_sql "SHOW INDEX FROM $table WHERE Key_name='$index';" 2>/dev/null | grep -q "$index"
}

# List of potential duplicate indexes
INDEXES=(
    "audit_logs:audit_timestamp_idx"
    "audit_logs:audit_category_idx"
    "messages:msg_crisis_idx"
    "messages:msg_sent_label_time_idx"
    "sentiment_reports:report_deleted_idx"
    "sentiment_reports:report_user_time_idx"
)

echo "Checking for potentially duplicate indexes:"
for item in "${INDEXES[@]}"; do
    TABLE="${item%:*}"
    INDEX="${item#*:}"
    
    if execute_sql "SHOW TABLES LIKE '$TABLE';" | grep -q "$TABLE"; then
        if check_index "$TABLE" "$INDEX"; then
            print_warning "Index $INDEX exists on table $TABLE"
        fi
    fi
done

# Check for mood_score column
echo ""
print_info "Checking for mood_score column (should not exist)..."
if execute_sql "SHOW COLUMNS FROM sentiment_reports LIKE 'mood_score';" | grep -q "mood_score"; then
    print_warning "mood_score column still exists in sentiment_reports"
    
    read -p "Do you want to remove it? (y/N): " REMOVE_MOOD
    if [ "$REMOVE_MOOD" = "y" ]; then
        execute_sql "ALTER TABLE sentiment_reports DROP COLUMN mood_score;" && \
            print_success "mood_score column removed" || \
            print_error "Failed to remove mood_score column"
    fi
else
    print_success "mood_score column does not exist (correct)"
fi

# Offer to clean up duplicate indexes
echo ""
print_warning "WARNING: The following operations will modify your database"
read -p "Do you want to remove duplicate indexes? (y/N): " CLEANUP

if [ "$CLEANUP" = "y" ]; then
    echo ""
    print_info "Removing duplicate indexes..."
    
    # Remove indexes if they exist
    for item in "${INDEXES[@]}"; do
        TABLE="${item%:*}"
        INDEX="${item#*:}"
        
        if execute_sql "SHOW TABLES LIKE '$TABLE';" | grep -q "$TABLE"; then
            if check_index "$TABLE" "$INDEX"; then
                print_info "Dropping index $INDEX from $TABLE..."
                execute_sql "ALTER TABLE $TABLE DROP INDEX $INDEX;" 2>&1 | grep -v "check that column/key exists" && \
                    print_success "Removed index $INDEX" || \
                    print_info "Index $INDEX might not exist (safe to ignore)"
            fi
        fi
    done
fi

# Check for migration conflicts
echo ""
print_info "Checking for migration conflicts..."

# Check if there are multiple migrations with same dependencies
CONFLICTS=$(execute_sql "
    SELECT name, COUNT(*) as count 
    FROM django_migrations 
    WHERE app='chatbot' 
    GROUP BY name 
    HAVING count > 1;
")

if [ -n "$CONFLICTS" ]; then
    print_warning "Found duplicate migration entries:"
    echo "$CONFLICTS"
else
    print_success "No duplicate migration entries found"
fi

# Offer to reset migrations (dangerous!)
echo ""
print_warning "⚠️  DANGEROUS OPERATION ⚠️"
print_info "You can reset migrations (this will delete all migration records)"
print_info "Only do this if you're starting fresh or having serious migration issues"
read -p "Do you want to reset migrations? (yes/NO): " RESET

if [ "$RESET" = "yes" ]; then
    print_warning "Creating backup first..."
    
    # Backup database
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE" && \
        print_success "Backup created: $BACKUP_FILE" || {
        print_error "Backup failed"
        exit 1
    }
    
    print_info "Deleting migration records..."
    execute_sql "DELETE FROM django_migrations WHERE app='chatbot';" && \
        print_success "Migration records deleted" || \
        print_error "Failed to delete migration records"
    
    print_info "After this, you'll need to run: python manage.py migrate --fake-initial"
fi

# Summary and recommendations
echo ""
echo "=================================="
print_info "Summary and Recommendations"
echo "=================================="
echo ""

print_info "Tables in database:"
execute_sql "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='$DB_NAME';"

echo ""
print_info "Migration status:"
execute_sql "SELECT COUNT(*) as migration_count FROM django_migrations WHERE app='chatbot';"

echo ""
print_info "Next steps:"
echo ""
echo "1. Review the information above"
echo "2. If you reset migrations, run:"
echo "   cd /home/mindlift/mindlift/webapp"
echo "   source venv/bin/activate"
echo "   python manage.py migrate --fake-initial"
echo ""
echo "3. Otherwise, run normal migrations:"
echo "   python manage.py migrate"
echo ""

# Check table sizes
echo ""
print_info "Table sizes:"
execute_sql "
    SELECT 
        table_name AS 'Table',
        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
    FROM information_schema.TABLES
    WHERE table_schema = '$DB_NAME'
    ORDER BY (data_length + index_length) DESC;
"

echo ""
print_success "Database cleanup check completed"
