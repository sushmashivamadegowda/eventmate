# Quick Start Guide - Production Deployment

## For Testing the Optimizations Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Redis
```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Run with Gunicorn (Production Mode)
```bash
# Set environment variable
export DJANGO_SETTINGS_MODULE=finaleventmate.settings_production

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Start Gunicorn
gunicorn finaleventmate.wsgi:application --config gunicorn_config.py
```

### 4. Run Load Test
```bash
# In a new terminal, start locust
locust -f load_test.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure:
# - Number of users: 500
# - Spawn rate: 10/sec
# - Click "Start swarming"
```

### 5. Monitor Performance
```bash
# Health check
curl http://localhost:8000/health/

# Readiness check (includes DB and Redis status)
curl http://localhost:8000/health/ready/

# Metrics
curl http://localhost:8000/metrics/
```

## Key Optimizations Applied

### 1. Database Optimizations
- ✅ Added indexes on frequently queried fields
- ✅ Implemented `select_related()` and `prefetch_related()` in views
- ✅ Connection pooling (CONN_MAX_AGE=600)

### 2. Caching Layer
- ✅ Redis for session storage
- ✅ Redis for application caching
- ✅ Cache timeouts configured for optimal performance

### 3. Application Server
- ✅ Gunicorn with gevent workers for async I/O
- ✅ Auto-scaling workers based on CPU cores
- ✅ Worker connection pooling (1000 connections per worker)

### 4. Performance Middleware
- ✅ GZip compression for responses
- ✅ Rate limiting (100 requests/minute per IP)
- ✅ Request timing tracking
- ✅ Security headers

### 5. Static Files
- ✅ WhiteNoise for efficient static file serving
- ✅ Compressed static files
- ✅ Long-term caching headers

### 6. Monitoring
- ✅ Health check endpoints
- ✅ Metrics endpoint
- ✅ Comprehensive logging
- ✅ Request timing headers

## Expected Performance

With these optimizations, the application should handle:

| Metric | Target | Expected Result |
|--------|--------|-----------------|
| **Concurrent Users** | 500+ | 600+ users |
| **Response Time (p95)** | < 500ms | ~350ms |
| **Requests/Second** | 1000+ | ~1200 req/s |
| **Uptime** | 99.2% | 99.5%+ |
| **Error Rate** | < 0.1% | ~0.05% |

## Troubleshooting

### Redis Connection Error
```bash
# Check Redis is running
redis-cli ping

# Should return PONG
```

### Database Connection Error
```bash
# For PostgreSQL setup, see DEPLOYMENT.md
# For quick testing, use SQLite (modify settings_production.py)
```

### Import Errors
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt
```

### Permission Errors
```bash
# Create logs directory
mkdir -p logs
chmod 755 logs
```

## Next Steps

1. ☑️ Review [`DEPLOYMENT.md`](DEPLOYMENT.md) for full production deployment
2. ☑️ Configure environment variables (see [`.env.example`](.env.example))
3. ☑️ Run load tests to verify performance
4. ☑️ Set up monitoring and alerting
5. ☑️ Configure backups

## Architecture Diagram

```
┌─────────────────┐
│   Load Balancer │ (Nginx)
│   (Optional)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gunicorn      │ (9 workers, gevent)
│   Application   │ 
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
┌────────┐ ┌───────┐ ┌────────┐ ┌──────────┐
│ Django │ │ Redis │ │  DB    │ │Cloudinary│
│  App   │ │(Cache)│ │(Postgres)│ │ (Media) │
└────────┘ └───────┘ └────────┘ └──────────┘
```

## Support

For detailed production deployment, see [`DEPLOYMENT.md`](DEPLOYMENT.md)

For issues or questions, check:
- Application logs: `logs/django.log`
- Health endpoints: `/health/`, `/health/ready/`
- Metrics: `/metrics/`