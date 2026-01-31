#!/bin/bash

# MindLift Configuration Script
# Run this after uploading project files
# Run as: sudo bash configure.sh

set -e

echo "=================================="
echo "MindLift Configuration Script"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0;m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Variables
PROJECT_DIR="/home/mindlift/mindlift"
WEBAPP_DIR="$PROJECT_DIR/webapp"
RASA_DIR="$PROJECT_DIR/rasa"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    print_info "Please upload your project files first"
    exit 1
fi

# Step 1: Set permissions
echo ""
print_info "Step 1: Setting file permissions..."
chown -R mindlift:mindlift $PROJECT_DIR
find $PROJECT_DIR -type d -exec chmod 755 {} \;
find $PROJECT_DIR -type f -exec chmod 644 {} \;
[ -f "$WEBAPP_DIR/manage.py" ] && chmod +x $WEBAPP_DIR/manage.py
print_success "Permissions set"

# Step 2: Setup Django virtual environment
echo ""
print_info "Step 2: Setting up Django virtual environment..."
if [ -d "$WEBAPP_DIR" ]; then
    cd $WEBAPP_DIR
    
    # Remove old venv if exists
    [ -d "venv" ] && rm -rf venv
    
    # Create new venv
    sudo -u mindlift python3.10 -m venv venv
    
    # Activate and install dependencies
    sudo -u mindlift bash -c "
        source venv/bin/activate
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
    "
    
    print_success "Django virtual environment created"
else
    print_error "Django webapp directory not found: $WEBAPP_DIR"
    exit 1
fi

# Step 3: Setup RASA virtual environment
echo ""
print_info "Step 3: Setting up RASA virtual environment..."
if [ -d "$RASA_DIR" ]; then
    cd $RASA_DIR
    
    # Remove old venv if exists
    [ -d "venv" ] && rm -rf venv
    
    # Create new venv
    sudo -u mindlift python3.10 -m venv venv
    
    # Activate and install dependencies
    sudo -u mindlift bash -c "
        source venv/bin/activate
        pip install --upgrade pip setuptools wheel
        pip install rasa==3.6.21
        pip install rasa-sdk==3.6.2
        pip install SQLAlchemy==1.4.49
        pip install sanic==21.12.2
        pip install sanic-cors==2.0.1
    "
    
    print_success "RASA virtual environment created"
else
    print_error "RASA directory not found: $RASA_DIR"
    exit 1
fi

# Step 4: Check .env file
echo ""
print_info "Step 4: Checking environment configuration..."
if [ ! -f "$WEBAPP_DIR/.env" ]; then
    print_error ".env file not found in $WEBAPP_DIR"
    print_info "Creating .env from template..."
    
    cat > $WEBAPP_DIR/.env << 'EOF'
# Django Settings
SECRET_KEY=CHANGE_THIS_TO_RANDOM_SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=YOUR_VM_IP,YOUR_DOMAIN.com,localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=mindlift_db
DB_USER=mindlift_user
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Groq API Configuration
GROQ_API_KEY=GROQ_API_KEY
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=500

# YouTube Data API Configuration
YOUTUBE_API_KEY=YOUTUBE_API_KEY

# RASA Configuration
USE_RASA=True
RASA_SERVER_URL=http://localhost:5005

# Performance Settings
MAX_CONTEXT_MESSAGES=4
REQUEST_TIMEOUT=30
EOF
    
    chown mindlift:mindlift $WEBAPP_DIR/.env
    chmod 600 $WEBAPP_DIR/.env
    
    print_info "Please edit $WEBAPP_DIR/.env and update the values"
    print_info "Generate SECRET_KEY: python3 -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
else
    print_success ".env file exists"
fi

# Step 5: Run migrations
echo ""
print_info "Step 5: Running Django migrations..."
print_info "Make sure database is created first!"
read -p "Press Enter to continue or Ctrl+C to abort..."

cd $WEBAPP_DIR
sudo -u mindlift bash -c "
    source venv/bin/activate
    python manage.py migrate
    python manage.py collectstatic --noinput
"
print_success "Migrations completed"

# Step 6: Train RASA model
echo ""
print_info "Step 6: Training RASA model..."
cd $RASA_DIR
sudo -u mindlift bash -c "
    source venv/bin/activate
    rasa train
"
print_success "RASA model trained"

# Step 7: Create supervisor configs
echo ""
print_info "Step 7: Creating Supervisor configurations..."

# RASA Actions
cat > /etc/supervisor/conf.d/rasa-actions.conf << EOF
[program:rasa-actions]
command=$RASA_DIR/venv/bin/rasa run actions
directory=$RASA_DIR
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/rasa-actions.log
stderr_logfile=/var/log/supervisor/rasa-actions.err.log
environment=PATH="$RASA_DIR/venv/bin"
stopwaitsecs=60
EOF

# RASA Server
cat > /etc/supervisor/conf.d/rasa-server.conf << EOF
[program:rasa-server]
command=$RASA_DIR/venv/bin/rasa run -m models --enable-api --cors "*" --port 5005
directory=$RASA_DIR
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/rasa-server.log
stderr_logfile=/var/log/supervisor/rasa-server.err.log
environment=PATH="$RASA_DIR/venv/bin"
stopwaitsecs=60
EOF

# Django Gunicorn
cat > /etc/supervisor/conf.d/django-gunicorn.conf << EOF
[program:django-gunicorn]
command=$WEBAPP_DIR/venv/bin/gunicorn webapp.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
directory=$WEBAPP_DIR
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/django-gunicorn.log
stderr_logfile=/var/log/supervisor/django-gunicorn.err.log
environment=PATH="$WEBAPP_DIR/venv/bin"
stopwaitsecs=60
EOF

supervisorctl reread
supervisorctl update
print_success "Supervisor configurations created"

# Step 8: Configure Nginx
echo ""
print_info "Step 8: Configuring Nginx..."
read -p "Enter your VM IP or domain name: " DOMAIN

cat > /etc/nginx/sites-available/mindlift << EOF
upstream django_app {
    server 127.0.0.1:8000;
}

upstream rasa_server {
    server 127.0.0.1:5005;
}

server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 50M;

    location /static/ {
        alias $WEBAPP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $WEBAPP_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://django_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /rasa/ {
        rewrite ^/rasa/(.*)$ /\$1 break;
        proxy_pass http://rasa_server;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_redirect off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/mindlift /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx
print_success "Nginx configured"

# Step 9: Start services
echo ""
print_info "Step 9: Starting all services..."
supervisorctl start all

sleep 5

echo ""
supervisorctl status

echo ""
echo "=================================="
print_success "Configuration completed!"
echo "=================================="
echo ""
print_info "Your application should be available at: http://$DOMAIN"
echo ""
print_info "Check logs with:"
echo "  sudo tail -f /var/log/supervisor/*.log"
echo ""
print_info "Manage services with:"
echo "  sudo supervisorctl status"
echo "  sudo supervisorctl restart all"
echo ""
