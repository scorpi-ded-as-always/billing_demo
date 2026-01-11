# Deployment Guide for Inventory Management System

## Quick Start (Production)

### 1. Server Preparation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx supervisor -y
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install python3 python3-pip nginx -y
```

### 2. Application Setup

```bash
# Navigate to your application directory
cd /var/www/inventory_system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set environment variables
export FLASK_ENV=production
export SECRET_KEY='your-random-secret-key-change-this'
```

### 3. Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Configure Gunicorn

Create a Gunicorn configuration file:
```bash
nano gunicorn_config.py
```

Add this content:
```python
import multiprocessing

bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

### 5. Systemd Service Setup

Create a systemd service file:
```bash
sudo nano /etc/systemd/system/inventory.service
```

Add this content:
```ini
[Unit]
Description=Inventory Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/inventory_system
Environment="PATH=/var/www/inventory_system/venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=your-secret-key-here"
ExecStart=/var/www/inventory_system/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable inventory
sudo systemctl start inventory
sudo systemctl status inventory
```

### 6. Nginx Configuration

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/inventory
```

Add this content:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Static files
    location /static {
        alias /var/www/inventory_system/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Auto-renewal is configured automatically.

### 8. Database Backup Setup

Create backup script:
```bash
nano /var/www/inventory_system/backup.sh
```

Add this content:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/inventory"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /var/www/inventory_system/instance/inventory.db $BACKUP_DIR/inventory_$DATE.db
find $BACKUP_DIR -name "inventory_*.db" -mtime +30 -delete
```

Make it executable:
```bash
chmod +x /var/www/inventory_system/backup.sh
```

Add to crontab:
```bash
crontab -e
```

Add this line for daily backup at 2 AM:
```
0 2 * * * /var/www/inventory_system/backup.sh
```

## Domain Configuration

### DNS Settings

1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Add these DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | Your Server IP | 3600 |
| A | www | Your Server IP | 3600 |

### Verify DNS Propagation

```bash
dig your-domain.com
nslookup your-domain.com
```

Wait up to 48 hours for full propagation (usually much faster).

## Cloud Platform Deployment

### AWS EC2

1. Launch Ubuntu 20.04+ instance
2. Configure Security Group:
   - SSH: Port 22
   - HTTP: Port 80
   - HTTPS: Port 443
3. Follow steps 2-8 above

### DigitalOcean Droplet

1. Create droplet with Ubuntu 20.04+
2. Add your SSH key
3. Follow steps 2-8 above

### Google Cloud Platform

1. Create Compute Engine instance
2. Configure firewall rules:
   - allowtcp:80
   - allowtcp:443
   - allowtcp:22
3. Follow steps 2-8 above

## Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

RUN mkdir -p instance

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./instance:/app/instance
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: always
```

Run with Docker:
```bash
docker-compose up -d
```

## Monitoring & Maintenance

### Check Application Status

```bash
# Check service status
sudo systemctl status inventory

# View logs
sudo journalctl -u inventory -f

# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Performance Optimization

1. **Enable Gzip Compression in Nginx:**
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
```

2. **Configure Worker Processes:**
```bash
# In gunicorn_config.py
workers = (2 * $CPU_COUNT) + 1
```

3. **Enable Database Indexing:**
The application automatically creates necessary indexes.

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (ufw)
- [ ] Set up regular backups
- [ ] Monitor logs regularly
- [ ] Keep system updated
- [ ] Use strong passwords
- [ ] Implement rate limiting (in Nginx)
- [ ] Set up fail2ban for SSH protection

### Troubleshooting

**Application not starting:**
```bash
sudo journalctl -u inventory -n 50
```

**502 Bad Gateway:**
```bash
sudo systemctl restart inventory
sudo systemctl reload nginx
```

**Database locked:**
```bash
sudo systemctl stop inventory
sudo chown www-data:www-data /var/www/inventory_system/instance/inventory.db
sudo systemctl start inventory
```

**Permission issues:**
```bash
sudo chown -R www-data:www-data /var/www/inventory_system
sudo chmod -R 755 /var/www/inventory_system
```

## Scaling Considerations

For high-traffic deployments:

1. **Load Balancing:** Use HAProxy or Nginx load balancer
2. **Database:** Switch to PostgreSQL or MySQL
3. **Caching:** Implement Redis caching
4. **CDN:** Use CloudFront or Cloudflare for static assets
5. **Monitoring:** Set up New Relic or DataDog

## Support

For issues:
1. Check application logs
2. Review Nginx error logs
3. Verify systemd service status
4. Test database connectivity
5. Check firewall settings

## Backup & Recovery

### Manual Backup
```bash
cp /var/www/inventory_system/instance/inventory.db /backup/inventory_manual_$(date +%Y%m%d).db
```

### Restore from Backup
```bash
sudo systemctl stop inventory
cp /backup/inventory_YYYYMMDD.db /var/www/inventory_system/instance/inventory.db
sudo chown www-data:www-data /var/www/inventory_system/instance/inventory.db
sudo systemctl start inventory
```

## Update Procedure

```bash
cd /var/www/inventory_system
git pull  # if using version control
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart inventory
```