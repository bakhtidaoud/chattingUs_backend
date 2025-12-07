# Deployment Guide - ChattingUs Admin Dashboard

Complete guide for deploying the admin dashboard to production.

## 🚀 Production Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx
- SSL certificate
- Domain name

### Server Setup

#### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

#### 2. Install Dependencies

```bash
# Python
sudo apt install python3 python3-pip python3-venv -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Redis
sudo apt install redis-server -y

# Nginx
sudo apt install nginx -y

# Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### 3. Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE chattingus_db;
CREATE USER chattingus_user WITH PASSWORD 'your_secure_password';
ALTER ROLE chattingus_user SET client_encoding TO 'utf8';
ALTER ROLE chattingus_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE chattingus_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE chattingus_db TO chattingus_user;
\q
```

### Application Deployment

#### 1. Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/yourusername/chattingus-backend.git
cd chattingus-backend
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Requirements

```bash
pip install -r requirements.txt
pip install gunicorn
```

#### 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

Update with production values:

```env
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=chattingus_db
DB_USER=chattingus_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

# Email (use production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### 5. Run Migrations

```bash
python manage.py migrate
```

#### 6. Create Superuser

```bash
python manage.py createsuperuser
```

#### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 8. Test Application

```bash
python manage.py runserver 0.0.0.0:8000
```

Visit `http://your-server-ip:8000/admin-dashboard/` to verify.

### Gunicorn Setup

#### 1. Create Gunicorn Socket

```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

#### 2. Create Gunicorn Service

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/chattingus-backend
Environment="PATH=/var/www/chattingus-backend/venv/bin"
ExecStart=/var/www/chattingus-backend/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          chattingus_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### 3. Start Gunicorn

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
```

### Nginx Configuration

#### 1. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/chattingus
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/chattingus-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/chattingus-backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

#### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/chattingus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts to complete SSL setup.

### Redis Configuration

```bash
sudo nano /etc/redis/redis.conf
```

Update:
```
supervised systemd
bind 127.0.0.1
```

Restart Redis:
```bash
sudo systemctl restart redis
```

### Firewall Setup

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## 📊 Monitoring & Logging

### Application Logs

```bash
# Gunicorn logs
sudo journalctl -u gunicorn

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Error Tracking (Sentry)

1. Install Sentry SDK:
```bash
pip install sentry-sdk
```

2. Configure in `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### Performance Monitoring

Install and configure:
- **New Relic** or **DataDog** for APM
- **Prometheus** + **Grafana** for metrics
- **ELK Stack** for log aggregation

## 🔄 Continuous Deployment

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /var/www/chattingus-backend
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart gunicorn
          sudo systemctl reload nginx
```

## 🔐 Security Hardening

### Django Settings

```python
# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### Fail2Ban

```bash
sudo apt install fail2ban -y
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true
```

Restart:
```bash
sudo systemctl restart fail2ban
```

## 💾 Backup Strategy

### Database Backups

Create backup script `/usr/local/bin/backup-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U chattingus_user chattingus_db > $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -type f -mtime +7 -delete
```

Make executable:
```bash
sudo chmod +x /usr/local/bin/backup-db.sh
```

Add to crontab:
```bash
sudo crontab -e
```

```
0 2 * * * /usr/local/bin/backup-db.sh
```

### Media Files Backup

```bash
rsync -avz /var/www/chattingus-backend/media/ backup-server:/backups/media/
```

## 🔄 Updates & Maintenance

### Update Application

```bash
cd /var/www/chattingus-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

### Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_user_email ON users_user(email);
CREATE INDEX idx_post_created ON posts_post(created_at);

-- Analyze tables
ANALYZE;
```

### Redis Caching

Configure in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### CDN Setup

Use Cloudflare or AWS CloudFront for static assets:

1. Upload static files to CDN
2. Update `STATIC_URL` in settings
3. Configure CORS headers

## ✅ Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] SSL certificate valid
- [ ] Database migrations applied
- [ ] Static files served correctly
- [ ] Media uploads working
- [ ] Email sending working
- [ ] Redis connection working
- [ ] Gunicorn running
- [ ] Nginx configured
- [ ] Firewall configured
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Error tracking enabled
- [ ] Logs accessible
- [ ] Performance acceptable
- [ ] Security headers present
- [ ] CORS configured
- [ ] Rate limiting enabled

## 🆘 Troubleshooting

### Gunicorn Not Starting

```bash
sudo journalctl -u gunicorn
sudo systemctl status gunicorn
```

### Nginx 502 Bad Gateway

```bash
sudo systemctl status gunicorn
sudo tail -f /var/log/nginx/error.log
```

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### Database Connection Error

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1"
```

## 📞 Support

For deployment issues:
- Check logs first
- Review this guide
- Contact: devops@chattingus.com

---

**Last Updated**: December 2024
**Version**: 1.0.0
