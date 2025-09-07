# Database and Redis Configuration Guide

## 🗄️ **PostgreSQL Database Configuration**

### **Environment Variables**
```bash
# Database Configuration
DB_USER=postgres
DB_PASS=2lEfMvflO3d87xth
DB_NAME=josh_assist
DB_PORT=5432
DB_HOST=joshskills-staging:asia-south1:gcp-js-stg-skills-db
```

### **Configuration Priority**
1. **DATABASE_URL** (highest priority) - Uses `dj-database-url` parsing
2. **Individual DB variables** - Fallback to PostgreSQL with custom settings
3. **SQLite** - Default development fallback

### **Production Database Features**
- **Connection Pooling**: MAX_CONNS=20, MIN_CONNS=5
- **SSL Mode**: `sslmode=require` for production security
- **Connection Health Checks**: Enabled for reliability
- **Connection Timeout**: 10 seconds
- **Max Connection Age**: 0 (close after each request for production)
- **Application Name**: `josh_campaigns` for monitoring

## 🔴 **Redis Configuration**

### **Environment Variables**
```bash
# Redis Configuration
REDIS_HOST=35.200.147.115:6379
REDIS_PASS=JoshRedisHa!
REDIS_DB=0
```

### **Redis Features**
- **Connection Pooling**: Max 20 connections per service
- **Health Checks**: Every 30 seconds
- **Retry Logic**: Automatic retry on timeout
- **Compression**: Zlib compression for data
- **JSON Serialization**: Native JSON support
- **Fallback Handling**: Continues working if Redis is down

### **Cache Configuration**
- **Backend**: `django_redis.cache.RedisCache`
- **Key Prefix**: `josh_campaigns`
- **Default Timeout**: 5 minutes (300 seconds)
- **Compression**: Enabled for large objects
- **Exception Handling**: Graceful degradation

### **Session Storage**
- **Engine**: Redis-based sessions
- **Cookie Security**: HTTPS-only in production
- **SameSite**: Lax policy for compatibility
- **Max Age**: 2 weeks (1,209,600 seconds)

## 🚀 **Celery Configuration**

### **Redis Broker Settings**
- **Connection Pool**: Max 20 connections
- **Retry Logic**: Automatic retry on startup
- **Heartbeat**: 10 seconds
- **Visibility Timeout**: 1 hour
- **Fanout Support**: Enabled for task routing

### **Performance Optimizations**
- **Connection Retry**: Up to 10 attempts
- **Pool Limits**: 10 connections per worker
- **Transport Options**: Optimized for Redis

## 🔧 **Installation Requirements**

### **New Dependencies Added**
```bash
django-redis==5.4.0  # Redis cache backend
redis==4.6.0         # Redis Python client
psycopg2-binary==2.9.7  # PostgreSQL adapter
```

### **Install Command**
```bash
pip install -r requirements.txt
```

## 📊 **Monitoring and Health Checks**

### **Database Health**
- Connection pool status
- Query performance metrics
- SSL connection status
- Connection timeout monitoring

### **Redis Health**
- Connection pool status
- Cache hit/miss ratios
- Memory usage monitoring
- Connection timeout tracking

## 🛡️ **Security Features**

### **Database Security**
- SSL connections required in production
- Connection pooling limits
- Health check monitoring
- Application name identification

### **Redis Security**
- Password authentication
- Connection encryption (if supported)
- Key prefix isolation
- Exception handling for security

## 🚀 **Deployment Commands**

### **Production Deployment**
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml --env-file .env up -d

# Check database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
# Then in shell: from django.core.cache import cache; cache.set('test', 'value', 10)
```

### **Health Check Endpoints**
Add to your Django URLs for monitoring:
```python
# urls.py
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection

def health_check(request):
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Redis check
        cache.set('health_check', 'ok', 10)
        redis_status = cache.get('health_check') == 'ok'
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'redis': 'connected' if redis_status else 'error'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

## 📝 **Environment File Template**

```bash
# .env.prod
DEBUG=False
SECRET_KEY=your-secure-secret-key

# Database
DB_USER=postgres
DB_PASS=your-password
DB_NAME=your-database
DB_PORT=5432
DB_HOST=your-host

# Redis
REDIS_HOST=your-redis-host:6379
REDIS_PASS=your-redis-password
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://:your-password@your-host:6379/0
CELERY_RESULT_BACKEND=django-db
```

## ⚠️ **Important Notes**

1. **SSL Required**: Production database connections require SSL
2. **Connection Limits**: Monitor connection pool usage
3. **Redis Fallback**: Application continues working if Redis is down
4. **Health Monitoring**: Implement health check endpoints
5. **Performance**: Connection pooling significantly improves performance
6. **Security**: All production connections use encrypted channels
