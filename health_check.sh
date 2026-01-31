#!/bin/bash

# MindLift Health Check Script
# Comprehensive system and application health monitoring

echo "========================================="
echo "    MindLift Health Check System"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Status counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

print_success() {
    echo -e "${GREEN}âœ" $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_error() {
    echo -e "${RED}âœ— $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}âš  $1${NC}"
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo "========================================="
    echo "  $1"
    echo "========================================="
    echo ""
}

# ===================================
# 1. System Resources Check
# ===================================
print_header "1. System Resources"

# CPU Load
LOAD=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1 | xargs)
print_info "CPU Load Average (1 min): $LOAD"

# Memory
MEM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
MEM_USED=$(free -h | awk '/^Mem:/ {print $3}')
MEM_PERCENT=$(free | awk '/^Mem:/ {printf("%.0f", $3/$2 * 100)}')
print_info "Memory: $MEM_USED / $MEM_TOTAL ($MEM_PERCENT%)"

if [ "$MEM_PERCENT" -lt 80 ]; then
    print_success "Memory usage is healthy"
elif [ "$MEM_PERCENT" -lt 90 ]; then
    print_warning "Memory usage is high ($MEM_PERCENT%)"
else
    print_error "Memory usage is critical ($MEM_PERCENT%)"
fi

# Disk Space
DISK_PERCENT=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_USED=$(df -h / | awk 'NR==2 {print $3}')
DISK_TOTAL=$(df -h / | awk 'NR==2 {print $2}')
print_info "Disk Usage: $DISK_USED / $DISK_TOTAL ($DISK_PERCENT%)"

if [ "$DISK_PERCENT" -lt 80 ]; then
    print_success "Disk space is healthy"
elif [ "$DISK_PERCENT" -lt 90 ]; then
    print_warning "Disk space is running low ($DISK_PERCENT%)"
else
    print_error "Disk space is critical ($DISK_PERCENT%)"
fi

# ===================================
# 2. Core Services Check
# ===================================
print_header "2. Core Services"

# Check Nginx
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
fi

# Check MySQL
if systemctl is-active --quiet mysql; then
    print_success "MySQL is running"
else
    print_error "MySQL is not running"
fi

# Check Supervisor
if systemctl is-active --quiet supervisor; then
    print_success "Supervisor is running"
else
    print_error "Supervisor is not running"
fi

# ===================================
# 3. Application Services Check
# ===================================
print_header "3. Application Services"

# Check supervisor services
if command -v supervisorctl &> /dev/null; then
    DJANGO_STATUS=$(supervisorctl status django-gunicorn 2>/dev/null | awk '{print $2}')
    RASA_SERVER_STATUS=$(supervisorctl status rasa-server 2>/dev/null | awk '{print $2}')
    RASA_ACTIONS_STATUS=$(supervisorctl status rasa-actions 2>/dev/null | awk '{print $2}')
    
    # Django
    if [ "$DJANGO_STATUS" = "RUNNING" ]; then
        DJANGO_UPTIME=$(supervisorctl status django-gunicorn | awk '{print $6, $7}')
        print_success "Django (Gunicorn) is running - uptime: $DJANGO_UPTIME"
    else
        print_error "Django (Gunicorn) is not running - status: $DJANGO_STATUS"
    fi
    
    # RASA Server
    if [ "$RASA_SERVER_STATUS" = "RUNNING" ]; then
        RASA_UPTIME=$(supervisorctl status rasa-server | awk '{print $6, $7}')
        print_success "RASA Server is running - uptime: $RASA_UPTIME"
    else
        print_error "RASA Server is not running - status: $RASA_SERVER_STATUS"
    fi
    
    # RASA Actions
    if [ "$RASA_ACTIONS_STATUS" = "RUNNING" ]; then
        ACTIONS_UPTIME=$(supervisorctl status rasa-actions | awk '{print $6, $7}')
        print_success "RASA Actions is running - uptime: $ACTIONS_UPTIME"
    else
        print_error "RASA Actions is not running - status: $RASA_ACTIONS_STATUS"
    fi
else
    print_error "Supervisorctl not found"
fi

# ===================================
# 4. Network Ports Check
# ===================================
print_header "4. Network Ports"

# Port 80 (HTTP)
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    print_success "Port 80 (HTTP) is open"
else
    print_warning "Port 80 (HTTP) is not listening"
fi

# Port 443 (HTTPS)
if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    print_success "Port 443 (HTTPS) is open"
else
    print_warning "Port 443 (HTTPS) is not listening (SSL may not be configured)"
fi

# Port 8000 (Django)
if netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    print_success "Port 8000 (Django) is listening"
else
    print_error "Port 8000 (Django) is not listening"
fi

# Port 5005 (RASA)
if netstat -tuln 2>/dev/null | grep -q ":5005 "; then
    print_success "Port 5005 (RASA) is listening"
else
    print_error "Port 5005 (RASA) is not listening"
fi

# Port 3306 (MySQL)
if netstat -tuln 2>/dev/null | grep -q ":3306 "; then
    print_success "Port 3306 (MySQL) is listening"
else
    print_error "Port 3306 (MySQL) is not listening"
fi

# ===================================
# 5. Application Health Check
# ===================================
print_header "5. Application Health"

# Test Django HTTP
DJANGO_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null)
if [ "$DJANGO_RESPONSE" = "200" ] || [ "$DJANGO_RESPONSE" = "302" ]; then
    print_success "Django is responding (HTTP $DJANGO_RESPONSE)"
else
    print_error "Django is not responding properly (HTTP $DJANGO_RESPONSE)"
fi

# Test RASA
RASA_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5005 2>/dev/null)
if [ "$RASA_RESPONSE" = "200" ]; then
    print_success "RASA is responding (HTTP $RASA_RESPONSE)"
else
    print_warning "RASA endpoint check returned HTTP $RASA_RESPONSE"
fi

# Test RASA webhook
RASA_WEBHOOK=$(curl -s -X POST http://localhost:5005/webhooks/rest/webhook \
    -H "Content-Type: application/json" \
    -d '{"sender":"healthcheck","message":"test"}' 2>/dev/null)

if [ -n "$RASA_WEBHOOK" ]; then
    print_success "RASA webhook is responding"
else
    print_error "RASA webhook is not responding"
fi

# ===================================
# 6. Database Check
# ===================================
print_header "6. Database Health"

# Check if we can connect to MySQL
if mysql -u root -e "SELECT 1" &>/dev/null || mysql -u mindlift_user -e "SELECT 1" &>/dev/null 2>&1; then
    print_success "MySQL connection successful"
    
    # Check database exists
    if mysql -u mindlift_user -e "USE mindlift_db; SELECT 1" &>/dev/null 2>&1; then
        print_success "Database 'mindlift_db' is accessible"
        
        # Count tables
        TABLE_COUNT=$(mysql -u mindlift_user mindlift_db -e "SHOW TABLES;" 2>/dev/null | wc -l)
        if [ $TABLE_COUNT -gt 0 ]; then
            print_info "Found $((TABLE_COUNT-1)) tables in database"
        fi
    else
        print_error "Cannot access database 'mindlift_db'"
    fi
else
    print_error "Cannot connect to MySQL"
fi

# ===================================
# 7. File Permissions Check
# ===================================
print_header "7. File Permissions"

PROJECT_DIR="/home/mindlift/mindlift"

if [ -d "$PROJECT_DIR" ]; then
    OWNER=$(stat -c '%U' "$PROJECT_DIR")
    if [ "$OWNER" = "mindlift" ]; then
        print_success "Project directory owned by mindlift user"
    else
        print_warning "Project directory owned by $OWNER (should be mindlift)"
    fi
    
    # Check static files
    if [ -d "$PROJECT_DIR/webapp/staticfiles" ]; then
        STATIC_OWNER=$(stat -c '%U' "$PROJECT_DIR/webapp/staticfiles")
        if [ "$STATIC_OWNER" = "mindlift" ] || [ "$STATIC_OWNER" = "www-data" ]; then
            print_success "Static files permissions correct"
        else
            print_warning "Static files owned by $STATIC_OWNER"
        fi
    fi
else
    print_error "Project directory not found: $PROJECT_DIR"
fi

# ===================================
# 8. Log Files Check
# ===================================
print_header "8. Log Files"

# Check for recent errors in supervisor logs
SUPERVISOR_LOG_DIR="/var/log/supervisor"

if [ -d "$SUPERVISOR_LOG_DIR" ]; then
    # Django errors
    DJANGO_ERRORS=$(grep -i "error\|exception\|critical" "$SUPERVISOR_LOG_DIR/django-gunicorn.log" 2>/dev/null | tail -5)
    if [ -z "$DJANGO_ERRORS" ]; then
        print_success "No recent Django errors found"
    else
        print_warning "Recent Django errors detected (check logs)"
    fi
    
    # RASA errors
    RASA_ERRORS=$(grep -i "error\|exception\|critical" "$SUPERVISOR_LOG_DIR/rasa-server.log" 2>/dev/null | tail -5)
    if [ -z "$RASA_ERRORS" ]; then
        print_success "No recent RASA errors found"
    else
        print_warning "Recent RASA errors detected (check logs)"
    fi
    
    # Check log file sizes
    for log in "$SUPERVISOR_LOG_DIR"/*.log; do
        if [ -f "$log" ]; then
            LOG_SIZE=$(du -h "$log" | cut -f1)
            LOG_SIZE_BYTES=$(du -b "$log" | cut -f1)
            if [ $LOG_SIZE_BYTES -gt 104857600 ]; then  # 100MB
                print_warning "Large log file: $(basename $log) - $LOG_SIZE"
            fi
        fi
    done
else
    print_warning "Supervisor log directory not found"
fi

# ===================================
# 9. Python Environment Check
# ===================================
print_header "9. Python Environments"

# Check Django venv
WEBAPP_VENV="/home/mindlift/mindlift/webapp/venv"
if [ -d "$WEBAPP_VENV" ]; then
    print_success "Django virtual environment exists"
    
    # Check Django installation
    DJANGO_VERSION=$("$WEBAPP_VENV/bin/python" -c "import django; print(django.get_version())" 2>/dev/null)
    if [ -n "$DJANGO_VERSION" ]; then
        print_info "Django version: $DJANGO_VERSION"
    else
        print_error "Django not installed in venv"
    fi
else
    print_error "Django virtual environment not found"
fi

# Check RASA venv
RASA_VENV="/home/mindlift/mindlift/rasa/venv"
if [ -d "$RASA_VENV" ]; then
    print_success "RASA virtual environment exists"
    
    # Check RASA installation
    RASA_VERSION=$("$RASA_VENV/bin/rasa" --version 2>/dev/null | head -1 | awk '{print $3}')
    if [ -n "$RASA_VERSION" ]; then
        print_info "RASA version: $RASA_VERSION"
    else
        print_error "RASA not installed in venv"
    fi
else
    print_error "RASA virtual environment not found"
fi

# ===================================
# 10. Security Check
# ===================================
print_header "10. Security Configuration"

# Check .env file permissions
ENV_FILE="/home/mindlift/mindlift/webapp/.env"
if [ -f "$ENV_FILE" ]; then
    ENV_PERMS=$(stat -c '%a' "$ENV_FILE")
    if [ "$ENV_PERMS" = "600" ] || [ "$ENV_PERMS" = "400" ]; then
        print_success ".env file has secure permissions ($ENV_PERMS)"
    else
        print_warning ".env file permissions are $ENV_PERMS (should be 600 or 400)"
    fi
    
    # Check DEBUG setting
    if grep -q "DEBUG=False" "$ENV_FILE"; then
        print_success "DEBUG is set to False (production mode)"
    else
        print_warning "DEBUG may not be set to False"
    fi
else
    print_error ".env file not found"
fi

# Check firewall
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        print_success "UFW firewall is active"
    else
        print_warning "UFW firewall is not active"
    fi
else
    print_info "UFW not installed"
fi

# ===================================
# Summary
# ===================================
print_header "Health Check Summary"

echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

# Calculate health score
HEALTH_SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo -n "Overall Health Score: "
if [ $HEALTH_SCORE -ge 90 ]; then
    echo -e "${GREEN}$HEALTH_SCORE% - Excellent${NC}"
elif [ $HEALTH_SCORE -ge 75 ]; then
    echo -e "${YELLOW}$HEALTH_SCORE% - Good${NC}"
elif [ $HEALTH_SCORE -ge 50 ]; then
    echo -e "${YELLOW}$HEALTH_SCORE% - Fair${NC}"
else
    echo -e "${RED}$HEALTH_SCORE% - Poor${NC}"
fi

echo ""

# Recommendations
if [ $FAILED_CHECKS -gt 0 ] || [ $WARNING_CHECKS -gt 0 ]; then
    print_header "Recommendations"
    
    if [ $FAILED_CHECKS -gt 0 ]; then
        echo "âš ï¸  Critical Issues Found:"
        echo "  1. Check failed services: sudo supervisorctl status"
        echo "  2. Review logs: sudo tail -f /var/log/supervisor/*.log"
        echo "  3. Restart failed services: sudo supervisorctl restart all"
        echo ""
    fi
    
    if [ $WARNING_CHECKS -gt 0 ]; then
        echo "âš ï¸  Warnings Found:"
        echo "  1. Review system resources"
        echo "  2. Check log files for errors"
        echo "  3. Verify configuration settings"
        echo ""
    fi
fi

echo "========================================="
echo "Health check completed at: $(date)"
echo "========================================="

# Exit with appropriate code
if [ $FAILED_CHECKS -eq 0 ]; then
    exit 0
else
    exit 1
fi
