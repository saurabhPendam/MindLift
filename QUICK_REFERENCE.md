# MindLift - Quick Reference Guide

## Quick Start

```bash
# 1. Initial Setup (run once)
sudo bash deploy.sh

# 2. Upload project files to /home/mindlift/mindlift

# 3. Configure application
sudo bash configure.sh

# 4. Create database
sudo mysql -u root -p
```

```sql
CREATE DATABASE mindlift_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mindlift_user'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON mindlift_db.* TO 'mindlift_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## Service Management

### Check Status
```bash
sudo supervisorctl status
```

### Restart Services
```bash
# Restart all
sudo supervisorctl restart all

# Restart individual service
sudo supervisorctl restart django-gunicorn
sudo supervisorctl restart rasa-server
sudo supervisorctl restart rasa-actions
```

### Stop/Start Services
```bash
sudo supervisorctl stop all
sudo supervisorctl start all
```

---

## View Logs

```bash
# Django logs
sudo tail -f /var/log/supervisor/django-gunicorn.log

# RASA logs
sudo tail -f /var/log/supervisor/rasa-server.log
sudo tail -f /var/log/supervisor/rasa-actions.log

# All logs together
sudo tail -f /var/log/supervisor/*.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Update Code

```bash
# If using Git
cd /home/mindlift/mindlift
git pull origin main

# Update Django
cd webapp
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
deactivate

# Restart Django
sudo supervisorctl restart django-gunicorn

# Update RASA (if needed)
cd ../rasa
source venv/bin/activate
rasa train
deactivate

# Restart RASA
sudo supervisorctl restart rasa-server rasa-actions
```

---

## Database Operations

### Backup Database
```bash
mysqldump -u mindlift_user -p mindlift_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore Database
```bash
gunzip < backup_20250131.sql.gz | mysql -u mindlift_user -p mindlift_db
```

### Django Migrations
```bash
cd /home/mindlift/mindlift/webapp
source venv/bin/activate

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo supervisorctl tail -f rasa-server

# Manual test
cd /home/mindlift/mindlift/rasa
source venv/bin/activate
rasa run -m models --enable-api
```

### Port Already in Use

```bash
# Find process using port 8000
sudo netstat -tulpn | grep 8000

# Kill process
sudo kill -9 PID

# Restart service
sudo supervisorctl restart django-gunicorn
```

### Database Connection Error

```bash
# Test connection
mysql -u mindlift_user -p mindlift_db

# Check .env file
cat /home/mindlift/mindlift/webapp/.env

# Test from Django
cd /home/mindlift/mindlift/webapp
source venv/bin/activate
python manage.py dbshell
```

### Static Files Not Loading

```bash
cd /home/mindlift/mindlift/webapp
source venv/bin/activate
python manage.py collectstatic --noinput

# Fix permissions
sudo chown -R mindlift:www-data staticfiles/
sudo chmod -R 755 staticfiles/

# Restart nginx
sudo systemctl restart nginx
```

---

## Common Commands

### System Monitoring

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Check running processes
ps aux | grep python

# Network connections
sudo netstat -tulpn
```

### Nginx

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

### MySQL

```bash
# Login
mysql -u mindlift_user -p

# Check running processes
sudo systemctl status mysql

# Restart MySQL
sudo systemctl restart mysql
```

---

## File Locations

```
Project Root:     /home/mindlift/mindlift
Django App:       /home/mindlift/mindlift/webapp
RASA:             /home/mindlift/mindlift/rasa
Static Files:     /home/mindlift/mindlift/webapp/staticfiles
Media Files:      /home/mindlift/mindlift/webapp/media
Logs:             /var/log/supervisor/
Nginx Config:     /etc/nginx/sites-available/mindlift
Supervisor:       /etc/supervisor/conf.d/
```

---

## Environment Variables

Edit: `/home/mindlift/mindlift/webapp/.env`

After editing, restart Django:
```bash
sudo supervisorctl restart django-gunicorn
```

---

## Creating Superuser

```bash
cd /home/mindlift/mindlift/webapp
source venv/bin/activate
python manage.py createsuperuser
```

---

## SSL Certificate (Optional)

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Firewall Rules

```bash
# Check status
sudo ufw status

# Enable firewall
sudo ufw enable

# Allow specific ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
```

---

## Performance Monitoring

```bash
# Check response time
curl -o /dev/null -s -w "Time: %{time_total}s\n" http://localhost:8000

# Monitor logs in real-time
sudo tail -f /var/log/nginx/access.log | grep -E "POST|GET"

# Check RASA response
curl http://localhost:5005/webhooks/rest/webhook \
  -d '{"sender": "test", "message": "hello"}' \
  -H "Content-Type: application/json"
```

---

## Backup Script

Create: `/home/mindlift/backup.sh`

```bash
#!/bin/bash
BACKUP_DIR="/home/mindlift/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u mindlift_user -pYOUR_PASSWORD mindlift_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/mindlift/mindlift/webapp/media

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to cron:
```bash
chmod +x /home/mindlift/backup.sh
crontab -e
# Add: 0 2 * * * /home/mindlift/backup.sh
```

---

## Health Check

```bash
# Check all services
curl http://localhost:8000
curl http://localhost:5005

# Check database
mysql -u mindlift_user -p -e "SELECT 1"

# Check supervisor
sudo supervisorctl status

# Check nginx
curl -I http://localhost
```

---

## Emergency Restart

```bash
# If everything fails, restart all services
sudo supervisorctl stop all
sudo systemctl restart nginx
sudo systemctl restart mysql
sleep 5
sudo supervisorctl start all

# Check status
sudo supervisorctl status
```

---

## Useful Aliases

Add to `~/.bashrc`:

```bash
alias logs='sudo tail -f /var/log/supervisor/*.log'
alias restart-all='sudo supervisorctl restart all'
alias status='sudo supervisorctl status'
alias django-shell='cd /home/mindlift/mindlift/webapp && source venv/bin/activate && python manage.py shell'
```

---

## Contact & Support

- Django Admin: http://YOUR_IP/admin
- Application: http://YOUR_IP
- RASA API: http://YOUR_IP:5005

For issues, check logs first:
```bash
sudo supervisorctl status
sudo tail -f /var/log/supervisor/*.log
```
