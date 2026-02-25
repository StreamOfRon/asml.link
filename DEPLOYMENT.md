# Deployment Guide

Complete guide for deploying the Link Shortening Service to production.

## Deployment Options

### 1. Docker (Recommended)
- Best for cloud platforms (AWS, GCP, Azure, Heroku, Railway, Fly.io)
- Consistent across environments
- Easy scaling with container orchestration

### 2. Traditional Server
- VPS or dedicated server
- Requires Python 3.10+, PostgreSQL, Nginx/Apache
- More hands-on management

### 3. Platform-as-a-Service
- Heroku, Railway, Fly.io, Render
- Easiest for small deployments
- Built-in CI/CD and monitoring

## Prerequisites

### All Deployments
- PostgreSQL 12+ database
- Python 3.10+ or Docker
- Domain name with DNS configured
- SSL/TLS certificate (Let's Encrypt recommended)

### OAuth Providers
Configure these before deployment:

**Google OAuth:**
- Production redirect URI: `https://yourdomain.com/auth/callback/google`

**GitHub OAuth:**
- Production redirect URI: `https://yourdomain.com/auth/callback/github`

## Docker Deployment

### Production Dockerfile

The project includes a multi-stage `Dockerfile`:

```dockerfile
# Development stage
FROM python:3.13-slim as development
WORKDIR /app
RUN apt-get update && apt-get install -y git
RUN pip install uv
COPY . .
RUN uv sync
CMD ["uv", "run", "dev"]

# Production stage
FROM python:3.13-slim as production
WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY . .
RUN uv sync --production
RUN uv pip install gunicorn hypercorn
EXPOSE 5000
CMD ["hypercorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
```

### Build and Push Production Image

```bash
# Build production image
docker build -t yourusername/link-shortener:latest --target production .

# Tag for registry
docker tag yourusername/link-shortener:latest yourusername/link-shortener:v1.0.0

# Push to Docker Hub
docker push yourusername/link-shortener:latest
```

### Deploy with Docker Compose (Production)

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: link_shortener_db
    environment:
      POSTGRES_DB: shortlink
      POSTGRES_USER: shortlink_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - link_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shortlink_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    image: yourusername/link-shortener:latest
    container_name: link_shortener_app
    environment:
      DATABASE_URL: postgresql+asyncpg://shortlink_user:${DB_PASSWORD}@db:5432/shortlink
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GOOGLE_REDIRECT_URI: https://yourdomain.com/auth/callback/google
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
      GITHUB_REDIRECT_URI: https://yourdomain.com/auth/callback/github
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CSRF_SECRET_KEY: ${CSRF_SECRET_KEY}
      ENABLE_HTTPS_REDIRECT: "true"
      SESSION_SECURE_COOKIES: "true"
      DEBUG: "false"
      INSTANCE_NAME: ${INSTANCE_NAME}
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - link_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: link_shortener_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./static:/app/static:ro
    depends_on:
      - app
    networks:
      - link_network
    restart: unless-stopped

volumes:
  db_data:

networks:
  link_network:
    driver: bridge
```

### Production .env File

```bash
# Database
DB_PASSWORD=<strong-random-password>

# OAuth
GOOGLE_CLIENT_ID=<production-client-id>
GOOGLE_CLIENT_SECRET=<production-secret>
GITHUB_CLIENT_ID=<production-client-id>
GITHUB_CLIENT_SECRET=<production-secret>

# Security
JWT_SECRET_KEY=<strong-random-key-32chars>
CSRF_SECRET_KEY=<strong-random-key-32chars>

# Application
INSTANCE_NAME=My Link Shortener
```

### Deploy with Compose

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Nginx Reverse Proxy Configuration

**nginx.conf:**

```nginx
upstream app {
    server app:5000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/access.log combined;
    error_log /var/log/nginx/error.log;

    # Client limits
    client_max_body_size 10M;

    # Proxy to Quart app
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## SSL/TLS Certificate Setup

### Using Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

Certificates are stored in `/etc/letsencrypt/live/yourdomain.com/`

### Using Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout private.key -out certificate.crt -days 365 -nodes
```

## Database Setup

### PostgreSQL on Production Server

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE shortlink;
CREATE USER shortlink_user WITH PASSWORD 'strong_password';
ALTER ROLE shortlink_user SET client_encoding TO 'utf8';
ALTER ROLE shortlink_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE shortlink_user SET default_transaction_deferrable TO on;
ALTER ROLE shortlink_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE shortlink TO shortlink_user;
\q
```

### Backup Strategy

```bash
# Daily automated backup
0 2 * * * pg_dump -U shortlink_user shortlink | gzip > /backups/shortlink_$(date +\%Y\%m\%d).sql.gz

# Upload to cloud storage (AWS S3 example)
0 3 * * * aws s3 cp /backups/ s3://your-bucket/shortlink-backups/ --recursive --exclude "*" --include "*.sql.gz"
```

### Database Migrations

Run migrations before starting the app:

```bash
# In container
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

# Or locally
alembic upgrade head
```

## Monitoring & Health Checks

### Health Check Endpoint

The app provides `/health` endpoint for monitoring:

```bash
curl https://yourdomain.com/health
```

### Docker Health Check

Configured in `docker-compose.prod.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Log Aggregation

Configure logs to external service:

```yaml
# docker-compose.prod.yml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=link-shortener"
```

## Scaling & Performance

### Horizontal Scaling

Load balance multiple app instances:

```nginx
upstream app {
    least_conn;
    server app1:5000;
    server app2:5000;
    server app3:5000;
}
```

### CDN Configuration

For static assets and shortened links:

```bash
# CloudFlare example
# Point DNS to CloudFlare nameservers
# Configure caching for /static/ and shortened links
```

### Database Connection Pooling

Configured automatically in production:

```python
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

## Security Checklist

- [ ] HTTPS/SSL enabled
- [ ] Security headers configured in Nginx
- [ ] PostgreSQL user has limited privileges
- [ ] `.env` file not in version control
- [ ] Strong secrets for JWT and CSRF
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Regular database backups
- [ ] Database credentials secure
- [ ] Firewall rules configured
- [ ] SSH hardened
- [ ] Regular security updates

## Deployment Checklist

- [ ] Database created and migrations run
- [ ] PostgreSQL backups configured
- [ ] OAuth providers configured with production URLs
- [ ] SSL certificate installed and valid
- [ ] Nginx reverse proxy configured
- [ ] `.env` file configured with production values
- [ ] Docker image built and tested locally
- [ ] Health checks passing
- [ ] Logs aggregation working
- [ ] DNS pointing to server/load balancer
- [ ] HTTPS redirect working
- [ ] All OAuth providers tested
- [ ] User registration tested
- [ ] Link creation tested
- [ ] Admin dashboard accessible
- [ ] Rate limiting tested
- [ ] Performance under load tested

## Platform-Specific Deployments

### Heroku

```bash
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0

# Set environment variables
heroku config:set JWT_SECRET_KEY=<value>
heroku config:set CSRF_SECRET_KEY=<value>
# ... other vars

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

### Railway.app

```bash
# Connect GitHub repository
# Select Dockerfile
# Add PostgreSQL plugin
# Set environment variables
# Deploy
```

### Fly.io

```bash
# Launch app
fly launch

# Set secrets
fly secrets set JWT_SECRET_KEY=<value>
fly secrets set CSRF_SECRET_KEY=<value>

# Deploy
fly deploy
```

## Troubleshooting Deployment

### Issue: Database Connection Fails

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec db pg_isready -U shortlink_user
```

### Issue: SSL Certificate Error

```bash
# Verify certificate
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Renew certificate
sudo certbot renew --force-renewal
```

### Issue: High Memory Usage

```bash
# Check processes
docker-compose -f docker-compose.prod.yml top app

# Reduce workers in hypercorn command
CMD ["hypercorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

### Issue: OAuth Redirect URI Mismatch

Verify in OAuth provider:
- Google: Settings → Authorized redirect URIs
- GitHub: Settings → OAuth Apps → Authorized redirect URIs

Must exactly match `REDIRECT_URI` environment variable.

## Monitoring Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Database stats
docker-compose -f docker-compose.prod.yml exec db psql -U shortlink_user -d shortlink -c "SELECT * FROM pg_stat_statements LIMIT 10;"

# Container stats
docker stats

# SSL certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

**Last Updated**: February 24, 2026
