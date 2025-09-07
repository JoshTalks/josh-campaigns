# Environment Configuration for Google Cloud SQL

## Database Configuration

Since you're using `cloud_sql_proxy` to connect to Google Cloud SQL, you need to set up your `.env` file with the following variables:

### Option 1: Individual Database Variables
```bash
# Google Cloud SQL Configuration (via cloud_sql_proxy)
# Run: cloud_sql_proxy -instances=joshskills-staging:asia-south1:gcp-js-stg-skills-db=tcp:0.0.0.0:5434
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password
DB_HOST=localhost
DB_PORT=5434
```

### Option 2: DATABASE_URL Format
```bash
# Alternative: Use DATABASE_URL format
DATABASE_URL=postgresql://username:password@localhost:5434/database_name
```

## Complete .env File Example
```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Google Cloud SQL Configuration
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password
DB_HOST=localhost
DB_PORT=5434

# Redis for Celery
REDIS_HOST=localhost:6379
REDIS_PASS=
REDIS_DB=0

# Email Settings
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# MSG91 Configuration for Email Campaigns
MSG91_AUTH_KEY=465189AMRdJW6Oa68a43d18P1
MSG91_EMAIL_FROM=noreply@yourdomain.com
MSG91_EMAIL_FROM_NAME=Your Company Name
```

## Setup Steps

1. **Start cloud_sql_proxy:**
   ```bash
   cloud_sql_proxy -instances=joshskills-staging:asia-south1:gcp-js-stg-skills-db=tcp:0.0.0.0:5434
   ```

2. **Create .env file** with the above configuration

3. **Test connection:**
   ```bash
   python manage.py check
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

## Troubleshooting

- **Port 5434**: Make sure cloud_sql_proxy is running on port 5434
- **Database credentials**: Verify your Google Cloud SQL user credentials
- **Network access**: Ensure your local machine can connect to the proxy
- **Firewall**: Check if any firewall is blocking the connection
