# MindLift - Google Cloud VM Deployment Guide

## Complete Step-by-Step Deployment Guide

This guide will help you deploy the MindLift Django + RASA chatbot on Google Cloud VM.

---

## Table of Contents
1. [VM Instance Creation](#1-vm-instance-creation)
2. [Initial Server Setup](#2-initial-server-setup)
3. [Python 3.10.9 Installation](#3-python-3109-installation)
4. [MySQL Database Setup](#4-mysql-database-setup)
5. [Project Deployment](#5-project-deployment)
6. [RASA Setup](#6-rasa-setup)
7. [Django Setup](#7-django-setup)
8. [Process Management with Supervisor](#8-process-management-with-supervisor)
9. [Nginx Configuration](#9-nginx-configuration)
10. [SSL/HTTPS Setup](#10-sslhttps-setup)
11. [Monitoring & Logs](#11-monitoring--logs)

---

## 1. VM Instance Creation

### Step 1.1: Create VM Instance on Google Cloud

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Navigate to**: Compute Engine > VM Instances
3. **Click**: "CREATE INSTANCE"

### Step 1.2: Configure VM Settings

```yaml
Name: mindlift-production
Region: us-central1 (or your preferred region)
Zone: us-central1-a

Machine Configuration:
  Series: E2
  Machine type: e2-medium (2 vCPU, 4 GB memory)
  # NOTE: Free tier is e2-micro, but NOT recommended for RASA
  # RASA needs at least 2GB RAM

Boot disk:
  Operating System: Ubuntu
  Version: Ubuntu 22.04 LTS
  Boot disk type: Balanced persistent disk
  Size: 30 GB (minimum recommended)

Firewall:
  ✓ Allow HTTP traffic
  ✓ Allow HTTPS traffic
```

### Step 1.3: Configure Firewall Rules

After creating VM, add firewall rules:

```bash
# Go to VPC Network > Firewall > CREATE FIREWALL RULE

Rule 1 - Django Application:
Name: allow-django-8000
Targets: All instances in the network
Source IP ranges: 0.0.0.0/0
Protocols and ports: tcp:8000

Rule 2 - RASA Server:
Name: allow-rasa-5005
Targets: All instances in the network
Source IP ranges: 0.0.0.0/0
Protocols and ports: tcp:5005

Rule 3 - MySQL (if needed externally):
Name: allow-mysql-3306
Targets: Specified target tags
Target tags: mysql-server
Source IP ranges: YOUR_IP_ADDRESS/32
Protocols and ports: tcp:3306
```

### Step 1.4: Connect to VM

```bash
# From Google Cloud Console, click "SSH" button
# OR use gcloud command:
gcloud compute ssh mindlift-production --zone=us-central1-a
```

---

## 2. Initial Server Setup

### Step 2.1: Update System

```bash
# Update package lists
sudo apt-get update

# Upgrade installed packages
sudo apt-get upgrade -y

# Install essential build tools
sudo apt-get install -y build-essential git wget curl vim screen htop
```

### Step 2.2: Configure Timezone

```bash
# Set timezone
sudo timedatectl set-timezone Asia/Kolkata  # or your timezone

# Verify
timedatectl
```

### Step 2.3: Create Application User

```bash
# Create dedicated user for application
sudo useradd -m -s /bin/bash mindlift

# Set password
sudo passwd mindlift

# Add to sudo group (optional)
sudo usermod -aG sudo mindlift

# Switch to mindlift user
sudo su - mindlift
```

---

## 3. Python 3.10.9 Installation

### Step 3.1: Install Python 3.10.9 from Source

```bash
# Install dependencies
sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev \
    libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
    libsqlite3-dev libbz2-dev liblzma-dev

# Download Python 3.10.9
cd /tmp
wget https://www.python.org/ftp/python/3.10.9/Python-3.10.9.tgz

# Extract
tar -xzf Python-3.10.9.tgz
cd Python-3.10.9

# Configure and build
./configure --enable-optimizations --with-ensurepip=install
make -j $(nproc)

# Install
sudo make altinstall

# Verify installation
python3.10 --version
# Should output: Python 3.10.9

# Create symlink for convenience
sudo ln -sf /usr/local/bin/python3.10 /usr/local/bin/python3
sudo ln -sf /usr/local/bin/pip3.10 /usr/local/bin/pip3

# Upgrade pip
python3.10 -m pip install --upgrade pip
```

### Step 3.2: Install virtualenv

```bash
pip3 install virtualenv
```

---

## 4. MySQL Database Setup

### Step 4.1: Install MySQL 8.0

```bash
# Install MySQL Server
sudo apt-get install -y mysql-server mysql-client libmysqlclient-dev

# Secure MySQL installation
sudo mysql_secure_installation
```

**Answer the prompts:**
```
- Set root password: YES (choose a strong password)
- Remove anonymous users: YES
- Disallow root login remotely: YES
- Remove test database: YES
- Reload privilege tables: YES
```

### Step 4.2: Create Database and User

```bash
# Login to MySQL as root
sudo mysql -u root -p

# Run these SQL commands:
```

```sql
-- Create database
CREATE DATABASE mindlift_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'mindlift_user'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD_HERE';

-- Grant privileges
GRANT ALL PRIVILEGES ON mindlift_db.* TO 'mindlift_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Verify
SHOW DATABASES;
SELECT user, host FROM mysql.user WHERE user='mindlift_user';

-- Exit
EXIT;
```

### Step 4.3: Test Database Connection

```bash
# Test connection
mysql -u mindlift_user -p mindlift_db

# Should connect successfully
# Exit with: EXIT;
```

### Step 4.4: Configure MySQL for Production

```bash
# Edit MySQL configuration
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
```

Add/modify these settings:

```ini
[mysqld]
# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Performance tuning
max_connections = 200
innodb_buffer_pool_size = 512M
innodb_log_file_size = 128M

# Binary logging (for backups)
log_bin = /var/log/mysql/mysql-bin.log
expire_logs_days = 7
```

```bash
# Restart MySQL
sudo systemctl restart mysql

# Enable MySQL to start on boot
sudo systemctl enable mysql

# Check status
sudo systemctl status mysql
```

---

## 5. Project Deployment

### Step 5.1: Create Project Directory

```bash
# Switch to mindlift user
sudo su - mindlift

# Create project directory
mkdir -p /home/mindlift/mindlift
cd /home/mindlift/mindlift
```

### Step 5.2: Upload Project Files

**Option A: Using Git (Recommended)**

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/mindlift.git .

# OR if using private repo:
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/mindlift.git .
```

**Option B: Using SCP from Local Machine**

```bash
# On your local Windows machine (PowerShell):
# Compress project first
tar -czf mindlift.tar.gz E:\mindlift\

# Upload to VM (from local machine)
gcloud compute scp mindlift.tar.gz mindlift-production:~ --zone=us-central1-a

# On VM, extract:
cd /home/mindlift/mindlift
tar -xzf ~/mindlift.tar.gz --strip-components=1
```

### Step 5.3: Set Proper Permissions

```bash
cd /home/mindlift/mindlift

# Set ownership
sudo chown -R mindlift:mindlift /home/mindlift/mindlift

# Set directory permissions
find . -type d -exec chmod 755 {} \;

# Set file permissions
find . -type f -exec chmod 644 {} \;

# Make manage.py executable
chmod +x webapp/manage.py
```

---

## 6. RASA Setup

### Step 6.1: Create RASA Virtual Environment

```bash
cd /home/mindlift/mindlift/rasa

# Create virtual environment with Python 3.10
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 6.2: Install RASA Dependencies

```bash
# Install RASA (this will take several minutes)
pip install rasa==3.6.21
pip install rasa-sdk==3.6.2

# Install other dependencies
pip install SQLAlchemy==1.4.49
pip install sanic==21.12.2
pip install sanic-cors==2.0.1

# Verify installation
rasa --version
```

### Step 6.3: Train RASA Model

```bash
# Train the model
rasa train

# This will create model file in models/ directory
# Verify:
ls -lh models/
```

---

## 7. Django Setup

### Step 7.1: Create Django Virtual Environment

```bash
cd /home/mindlift/mindlift/webapp

# Create virtual environment
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 7.2: Install Django Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# If mysqlclient installation fails, install system dependencies first:
# deactivate
# sudo apt-get install -y python3.10-dev libmysqlclient-dev pkg-config
# source venv/bin/activate
# pip install mysqlclient
```

### Step 7.3: Configure Environment Variables

```bash
# Create production .env file
vim /home/mindlift/mindlift/MindLift/webapp/.env
``` for editing the files in env:
i
ESC
:wq

```
for webapp
import nltk; nltk.download('averaged_perceptron_tagger_eng'); nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt'); nltk.download('stopwords')"


python manage.py train_adaptive_models --stats-only  # Check data
python manage.py train_adaptive_models --days 90     # Train models to train models with user data

**Production .env file:**

```bash
# Django Settings
SECRET_KEY=GENERATE_NEW_SECRET_KEY_HERE_CHANGE_THIS
DEBUG=False
ALLOWED_HOSTS=YOUR_VM_IP,YOUR_DOMAIN.com,localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=mindlift_db
DB_USER=mindlift_user
DB_PASSWORD=YOUR_MYSQL_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=3306

# Groq API Configuration
GROQ_API_KEY=your groq api key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=500

# YouTube Data API Configuration
YOUTUBE_API_KEY=your api key

# RASA Configuration
USE_RASA=True
RASA_SERVER_URL=http://localhost:5005

# Performance Settings
MAX_CONTEXT_MESSAGES=4
REQUEST_TIMEOUT=30
```

**Generate a new SECRET_KEY:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 7.4: Run Migrations

```bash
cd /home/mindlift/mindlift/webapp
source venv/bin/activate

# Check for migration issues
python manage.py makemigrations --dry-run

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: admin@mindlift.com
# Password: (choose a secure password)

# Load sample data
python manage.py loaddata initial_data.json  # if you have fixture

# Collect static files
python manage.py collectstatic --noinput
```

### Step 7.5: Test Django Application

```bash
# Test server
python manage.py runserver 0.0.0.0:8000

# From your local browser, visit:
# http://YOUR_VM_IP:8000

# If it works, press Ctrl+C to stop
```

---

## 8. Process Management with Supervisor

### Step 8.1: Install Supervisor

```bash
sudo apt-get install -y supervisor

# Enable supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### Step 8.2: Create Supervisor Configuration Files

**RASA Actions Server:**

```bash
sudo vim /etc/supervisor/conf.d/rasa-actions.conf
```

```ini
[program:rasa-actions]
command=/home/mindlift/mindlift/MindLift/rasa/venv/bin/rasa run actions
directory=/home/mindlift/mindlift/rasa
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/rasa-actions.log
stderr_logfile=/var/log/supervisor/rasa-actions.err.log
environment=PATH="/home/mindlift/mindlift/rasa/venv/bin"
```

**RASA Server:**

```bash
sudo vim /etc/supervisor/conf.d/rasa-server.conf
```

```ini
[program:rasa-server]
command=/home/mindlift/mindlift/rasa/venv/bin/rasa run -m models --enable-api --cors "*" --port 5005
directory=/home/mindlift/mindlift/rasa
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/rasa-server.log
stderr_logfile=/var/log/supervisor/rasa-server.err.log
environment=PATH="/home/mindlift/mindlift/rasa/venv/bin"
```

**Django with Gunicorn:**

```bash
sudo vim /etc/supervisor/conf.d/django-gunicorn.conf
```

```ini
[program:django-gunicorn]
command=/home/mindlift/mindlift/webapp/venv/bin/gunicorn webapp.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
directory=/home/mindlift/mindlift/webapp
user=mindlift
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/django-gunicorn.log
stderr_logfile=/var/log/supervisor/django-gunicorn.err.log
environment=PATH="/home/mindlift/mindlift/webapp/venv/bin"
```

### Step 8.3: Update Supervisor

```bash
# Reread configuration
sudo supervisorctl reread

# Update supervisor
sudo supervisorctl update

# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status
```

**Expected output:**
```
django-gunicorn                  RUNNING   pid 1234, uptime 0:00:05
rasa-actions                     RUNNING   pid 1235, uptime 0:00:05
rasa-server                      RUNNING   pid 1236, uptime 0:00:05
```

### Step 8.4: Supervisor Management Commands

```bash
# Check status
sudo supervisorctl status

# Restart specific service
sudo supervisorctl restart django-gunicorn
sudo supervisorctl restart rasa-server
sudo supervisorctl restart rasa-actions

# Restart all
sudo supervisorctl restart all

# Stop service
sudo supervisorctl stop rasa-server

# View logs
sudo tail -f /var/log/supervisor/django-gunicorn.log
sudo tail -f /var/log/supervisor/rasa-server.log
sudo tail -f /var/log/supervisor/rasa-actions.log
```

---

## 9. Nginx Configuration

### Step 9.1: Install Nginx

```bash
sudo apt-get install -y nginx

# Enable nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Step 9.2: Configure Nginx

```bash
# Create nginx configuration
sudo vim /etc/nginx/sites-available/mindlift
```

```nginx
# Upstream servers
upstream django_app {
    server 127.0.0.1:8000;
}

upstream rasa_server {
    server 127.0.0.1:5005;
}

# HTTP Server - Redirect to HTTPS (after SSL setup)
server {
    listen 80;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com YOUR_VM_IP;

    # For now, serve the app directly
    # After SSL setup, this will redirect to HTTPS

    client_max_body_size 50M;

    # Serve static files
    location /static/ {
        alias /home/mindlift/mindlift/webapp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias /home/mindlift/mindlift/webapp/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # RASA API
    location /rasa/ {
        rewrite ^/rasa/(.*)$ /$1 break;
        proxy_pass http://rasa_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }
}
```

### Step 9.3: Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/mindlift /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 9.4: Test Application

```bash
# Open browser and visit:
http://YOUR_VM_IP

# Should see your MindLift application
```

---

## 10. SSL/HTTPS Setup (Optional but Recommended)

### Step 10.1: Install Certbot

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 10.2: Obtain SSL Certificate

```bash
# Make sure your domain points to VM IP first
# Then run:
sudo certbot --nginx -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose redirect option (2)
```

### Step 10.3: Auto-renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
# Verify:
sudo systemctl list-timers | grep certbot
```

---

## 11. Monitoring & Logs

### Step 11.1: View Logs

```bash
# Django logs
sudo tail -f /var/log/supervisor/django-gunicorn.log

# RASA logs
sudo tail -f /var/log/supervisor/rasa-server.log
sudo tail -f /var/log/supervisor/rasa-actions.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# MySQL logs
sudo tail -f /var/log/mysql/error.log

# System logs
journalctl -u nginx -f
journalctl -u mysql -f
```

### Step 11.2: Monitor System Resources

```bash
# Install monitoring tools
sudo apt-get install -y htop iotop

# Monitor processes
htop

# Monitor disk usage
df -h

# Monitor memory
free -h

# Monitor network
netstat -tulpn | grep LISTEN
```

### Step 11.3: Database Backup

```bash
# Create backup script
vim /home/mindlift/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/mindlift/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="mindlift_db"
DB_USER="mindlift_user"
DB_PASS="YOUR_PASSWORD"

mkdir -p $BACKUP_DIR

mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/mindlift_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "mindlift_*.sql.gz" -mtime +7 -delete

echo "Backup completed: mindlift_$DATE.sql.gz"
```

```bash
# Make executable
chmod +x /home/mindlift/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
```

Add line:
```
0 2 * * * /home/mindlift/backup_db.sh >> /home/mindlift/backup.log 2>&1
```

---

## Troubleshooting

### Issue: RASA Won't Start

```bash
# Check logs
sudo tail -100 /var/log/supervisor/rasa-server.log

# Common fixes:
# 1. Model not found
cd /home/mindlift/mindlift/rasa
source venv/bin/activate
rasa train

# 2. Port already in use
sudo netstat -tulpn | grep 5005
sudo kill -9 PID

# 3. Restart service
sudo supervisorctl restart rasa-server
```

### Issue: Django Database Connection Error

```bash
# Test MySQL connection
mysql -u mindlift_user -p mindlift_db

# Check .env file
cat /home/mindlift/mindlift/webapp/.env

# Test Django connection
cd /home/mindlift/mindlift/webapp
source venv/bin/activate
python manage.py dbshell
```

### Issue: Static Files Not Loading

```bash
# Collect static files
cd /home/mindlift/mindlift/webapp
source venv/bin/activate
python manage.py collectstatic --noinput

# Check permissions
ls -la /home/mindlift/mindlift/webapp/staticfiles/

# Fix permissions
sudo chown -R mindlift:www-data /home/mindlift/mindlift/webapp/staticfiles/
sudo chmod -R 755 /home/mindlift/mindlift/webapp/staticfiles/
```

### Issue: 502 Bad Gateway

```bash
# Check if gunicorn is running
sudo supervisorctl status django-gunicorn

# Check gunicorn logs
sudo tail -50 /var/log/supervisor/django-gunicorn.log

# Restart gunicorn
sudo supervisorctl restart django-gunicorn

# Check nginx error log
sudo tail -50 /var/log/nginx/error.log
```

---

## Maintenance Commands

```bash
# Restart all services
sudo supervisorctl restart all
sudo systemctl restart nginx

# Update code from git
cd /home/mindlift/mindlift
git pull origin main

# Restart Django after code update
cd webapp
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart django-gunicorn

# Retrain RASA after changes
cd /home/mindlift/mindlift/rasa
source venv/bin/activate
rasa train
sudo supervisorctl restart rasa-server

# View all logs in one terminal
sudo tail -f /var/log/supervisor/*.log
```

---

## 12. Automatic Model Training Setup

### Step 12.1: Understanding Adaptive Learning

MindLift includes an adaptive learning system that improves over time by training ML models on user data:

**Models trained:**
- **Sentiment Classifier**: Learns from user feedback corrections
- **Theme Extractor**: Adapts to user language patterns
- **Distortion Detector**: Identifies cognitive distortions (CBT)

**Training Requirements:**
- Minimum 50 messages for sentiment classifier
- Minimum 30 messages for theme extractor  
- Minimum 20 messages for distortion detector

### Step 12.2: Setup Automatic Training with Cron

```bash
# Create scripts directory
mkdir -p /home/mindlift/mindlift/scripts

# Upload setup script (from local machine)
# Or create it on server:
sudo nano /home/mindlift/mindlift/scripts/setup_cron.sh

# Copy the content from scripts/setup_cron.sh
# Make executable
chmod +x /home/mindlift/mindlift/scripts/setup_cron.sh
chmod +x /home/mindlift/mindlift/scripts/check_training_status.sh

# Run setup script
bash /home/mindlift/mindlift/scripts/setup_cron.sh
```

### Step 12.3: Verify Automatic Training

```bash
# Check cron schedule
crontab -l

# Expected output:
# MindLift Auto-Training - Runs daily at 3 AM
# 0 3 * * * /home/mindlift/mindlift/scripts/run_auto_training.sh

# Check training status
bash /home/mindlift/mindlift/scripts/check_training_status.sh

# View training logs
tail -f /home/mindlift/mindlift/logs/auto_training.log
```

### Step 12.4: Manual Training (Optional)

```bash
# Switch to mindlift user
sudo su - mindlift

# Navigate to webapp
cd /home/mindlift/mindlift/webapp

# Activate virtual environment
source ../venv/bin/activate

# Check training data availability
python manage.py auto_train_models --days 90

# Force training (even with insufficient data)
python manage.py auto_train_models --force

# Train with custom thresholds
python manage.py auto_train_models --min-messages 30
```

### Step 12.5: Customize Training Schedule

Edit crontab to change schedule:
```bash
crontab -e

# Examples:
# Every 6 hours:     0 */6 * * *
# Twice daily:       0 3,15 * * *
# Weekly (Sunday):   0 2 * * 0
# Every 12 hours:    0 */12 * * *
```

### Step 12.6: Monitor Model Performance

```bash
# Check trained models
ls -lh /home/mindlift/mindlift/webapp/ml_models/

# Expected files:
# sentiment_classifier.pkl
# theme_extractor.pkl
# distortion_detector.pkl

# View training results in Django admin
# Go to: https://YOUR_DOMAIN.com/admin
# Check recent message analytics
```

### Step 12.7: Training Data Best Practices

**To get quality training data:**

1. **Encourage user engagement** - More conversations = better models
2. **Collect feedback** - User corrections improve sentiment accuracy
3. **Clinical assessments** - PHQ-9 and GAD-7 help validate mental health insights
4. **Diverse conversations** - Different themes help theme extraction

**Minimum data timeline:**
- Week 1-2: Gathering initial conversations (0-50 messages)
- Week 3-4: First automatic training triggers (50+ messages)
- Week 5-8: Models improve with more data (100+ messages)
- Month 3+: Mature models with high accuracy (500+ messages)

### Step 12.8: Troubleshooting Training

```bash
# Check why training didn't run
tail -f /home/mindlift/mindlift/logs/auto_training.log

# Common issues:
# "Insufficient data" - Need more user messages
# "Model training failed" - Check error logs

# Check system logs
grep -i "training" /var/log/syslog

# Manual test run
cd /home/mindlift/mindlift/webapp
source ../venv/bin/activate
python manage.py auto_train_models --force
```

---

## Security Checklist

- [ ] Changed default passwords
- [ ] Configured firewall rules
- [ ] Set DEBUG=False in production
- [ ] Generated new SECRET_KEY
- [ ] MySQL secured (mysql_secure_installation)
- [ ] SSL certificate installed
- [ ] Regular backups configured
- [ ] Monitoring setup
- [ ] Log rotation configured
- [ ] API keys secured in .env
- [ ] Automatic training scheduled

---

## Performance Optimization

1. **Enable Gzip in Nginx**
2. **Configure Redis for caching**
3. **Database indexing**
4. **CDN for static files**
5. **Database connection pooling**

---

## Next Steps

1. Setup domain name and DNS
2. Configure email backend (for notifications)
3. Setup monitoring (e.g., Prometheus, Grafana)
4. Configure automated backups
5. Setup CI/CD pipeline

---

## Support

For issues, check logs first:
```bash
sudo supervisorctl status
sudo tail -f /var/log/supervisor/*.log
sudo tail -f /var/log/nginx/error.log
```

**Your MindLift application should now be running on:**
- Main App: http://YOUR_VM_IP or https://YOUR_DOMAIN.com
- Admin Panel: http://YOUR_VM_IP/admin

---

**Congratulations! Your MindLift application is now deployed on Google Cloud VM! 🚀**
