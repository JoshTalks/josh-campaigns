# Development Environment Setup

## 🎯 **Overview**

Your development environment is now configured to use the **same staging database and Redis** as production, allowing you to:
- Test with real data
- Develop against the actual database schema
- Use the same Redis instance for caching and Celery
- Ensure consistency between development and production

## 🔧 **Environment Files**

### **Development Environment (.env.dev)**
```bash
# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-)ljd&1l11d1m)26i@2c=401mbk-z&7hi3qij9*!4%5wm%kel-g
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration (Using Staging DB for Testing)
DB_USER=postgres
DB_PASS=2lEfMvflO3d87xth
DB_NAME=josh_assist
DB_PORT=5432
DB_HOST=joshskills-staging:asia-south1:gcp-js-stg-skills-db

# Redis Configuration (Using Staging Redis for Testing)
REDIS_HOST=35.200.147.115:6379
REDIS_PASS=JoshRedisHa!
REDIS_DB=1  # Different DB number to avoid conflicts

# Email Configuration
SENDGRID_API_KEY=your-sendgrid-api-key-here

# Celery Configuration
CELERY_BROKER_URL=redis://:JoshRedisHa!@35.200.147.115:6379/1
CELERY_RESULT_BACKEND=django-db

# Development Settings
DJANGO_SETTINGS_MODULE=joshCampaigns.settings
```

### **Production Environment (.env)**
```bash
# Uses REDIS_DB=0 (same as staging production)
# Uses same database and Redis instance
```

## 🚀 **Running Development Environment**

### **Option 1: Using Development Compose File**
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f web

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### **Option 2: Using Main Compose File**
```bash
# Start with main compose file
docker-compose --env-file .env up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### **Option 3: Using Production Compose File (for testing)**
```bash
# Test production configuration locally
docker-compose -f docker-compose.prod.yml --env-file .env up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## 🗄️ **Database Configuration**

### **Staging Database Details**
- **Host**: `joshskills-staging:asia-south1:gcp-js-stg-skills-db`
- **Database**: `josh_assist`
- **User**: `postgres`
- **Port**: `5432`
- **Connection**: Via Cloud SQL Proxy

### **Database Access**
```bash
# Connect to database via Django shell
docker-compose exec web python manage.py dbshell

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check database status
docker-compose exec web python manage.py showmigrations
```

## 🔴 **Redis Configuration**

### **Redis Instance Details**
- **Host**: `35.200.147.115:6379`
- **Password**: `JoshRedisHa!`
- **Development DB**: `1` (to avoid conflicts with production)
- **Production DB**: `0`

### **Redis Testing**
```bash
# Test Redis connection via Django shell
docker-compose exec web python manage.py shell

# In Django shell:
from django.core.cache import cache
cache.set('test_key', 'test_value', 10)
result = cache.get('test_key')
print(f"Redis test: {result}")
```

## 🧪 **Testing with Staging Data**

### **Benefits of Using Staging Environment**
1. **Real Data**: Test with actual customer and campaign data
2. **Schema Consistency**: Ensure your models match production
3. **Performance Testing**: Test with realistic data volumes
4. **Integration Testing**: Verify external service connections

### **Development Workflow**
1. **Start Environment**: Use development compose file
2. **Make Changes**: Modify models, views, or templates
3. **Test Locally**: Test against staging database
4. **Run Migrations**: Apply schema changes
5. **Verify**: Ensure everything works with real data

## ⚠️ **Important Considerations**

### **Data Safety**
- **Development uses REDIS_DB=1** (different from production REDIS_DB=0)
- **Same database instance** - be careful with destructive operations
- **Test migrations** on staging before production
- **Backup data** before major schema changes

### **Performance**
- **Cloud SQL Proxy** adds slight latency
- **External Redis** may have network delays
- **Monitor connection pools** for optimal performance

### **Security**
- **Service account key** required for database access
- **Redis password** authentication enabled
- **Environment variables** contain sensitive information

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Cloud SQL Proxy Connection Failed**
```bash
# Check service account key
ls -la service-account-key.json

# Verify environment variables
docker-compose exec web env | grep DB_

# Check proxy logs
docker-compose logs cloud-sql-proxy
```

#### **2. Redis Connection Failed**
```bash
# Test Redis connectivity
docker-compose exec web python -c "
import redis
r = redis.Redis(host='35.200.147.115', port=6379, password='JoshRedisHa!', db=1)
print(r.ping())
"
```

#### **3. Database Migration Issues**
```bash
# Check migration status
docker-compose exec web python manage.py showmigrations

# Reset migrations (if needed)
docker-compose exec web python manage.py migrate --fake-initial

# Check database connection
docker-compose exec web python manage.py dbshell
```

### **Health Checks**
```bash
# Database health
docker-compose exec web python manage.py check --database default

# Redis health
docker-compose exec web python -c "
from django.core.cache import cache
cache.set('health', 'ok', 10)
print('Redis:', cache.get('health'))
"
```

## 📚 **Useful Commands**

### **Development Commands**
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart specific service
docker-compose -f docker-compose.dev.yml restart web

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec web python manage.py shell

# Check service status
docker-compose -f docker-compose.dev.yml ps
```

### **Database Commands**
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Check migration status
docker-compose exec web python manage.py showmigrations

# Reset database (careful!)
docker-compose exec web python manage.py flush
```

## 🎉 **Getting Started**

1. **Ensure you have the service account key**: `service-account-key.json`
2. **Choose your environment file**: `.env.dev` for development, `.env` for production testing
3. **Start the environment**: Use the appropriate compose file
4. **Test connections**: Verify database and Redis are working
5. **Start developing**: Make changes and test with real data!

Your development environment is now fully configured to use the staging infrastructure! 🚀
