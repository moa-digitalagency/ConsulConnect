# e-Consulaire RDC - Deployment Guide

## Deployment Steps

### 1. Pre-Deployment Checklist

- [ ] All code pushed to repository
- [ ] Database migrations completed
- [ ] Environment variables configured
- [ ] Security settings verified
- [ ] SSL/TLS certificates in place
- [ ] Backup strategy implemented

### 2. Environment Setup

#### Replit Deployment
1. Push code to your Replit project
2. Set environment variables in Replit secrets:
   ```
   DATABASE_URL=<PostgreSQL connection string>
   SESSION_SECRET=<generate secure key>
   ENCRYPTION_KEY=<generate secure key>
   SENDGRID_API_KEY=<your API key>
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=<your SendGrid API key>
   ```

#### Linux/VPS Deployment
1. Install Python 3.11
2. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install postgresql-client libpq-dev
   ```
3. Clone repository
4. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Database Setup

#### Initialize Database
```bash
# Development
python init_db.py

# With demo data
python demo_data.py
```

#### PostgreSQL Production Setup
```bash
# Create database
createdb econsular_prod

# Create user
createuser econsular_user
ALTER USER econsular_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE econsular_prod TO econsular_user;

# Connection string
postgresql://econsular_user:secure_password@localhost:5432/econsular_prod
```

### 4. Application Startup

#### Replit
- Click "Run" button to start application
- Application starts on port 5000
- Access via Replit-provided URL

#### Local/VPS with Gunicorn
```bash
# Development
python main.py

# Production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 5. Monitoring and Logs

#### Check Application Status
```bash
# View logs
tail -f /var/log/econsular/app.log

# Check process
ps aux | grep gunicorn

# Monitor database
psql -U econsular_user -d econsular_prod
```

### 6. Backup Strategy

#### Database Backup
```bash
# Full backup
pg_dump -U econsular_user econsular_prod > backup.sql

# Automated backup (cron)
0 2 * * * pg_dump -U econsular_user econsular_prod | gzip > /backups/econsular_$(date +\%Y\%m\%d).sql.gz
```

#### File Backup
```bash
# Backup uploads folder
tar -czf uploads_backup.tar.gz uploads/
```

### 7. Security Hardening

#### Web Server Security
- Enable HTTPS/SSL
- Set security headers:
  ```
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Strict-Transport-Security: max-age=31536000
  ```

#### Application Security
- Use environment variables for all secrets
- Enable rate limiting
- Implement login attempt limits
- Set up Web Application Firewall (WAF)

#### Database Security
- Use strong passwords
- Restrict database access by IP
- Enable SSL connections to database
- Regular security updates

### 8. Performance Optimization

#### Gunicorn Configuration
```bash
gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 0.0.0.0:5000 \
  --timeout 60 \
  --access-logfile /var/log/econsular/access.log \
  --error-logfile /var/log/econsular/error.log \
  app:app
```

#### Database Optimization
- Add indexes on frequently queried fields
- Archive old records periodically
- Configure connection pooling

#### Caching
- Implement Redis for session storage
- Cache static assets with CDN
- Use browser caching headers

### 9. Monitoring and Alerts

#### Application Monitoring
- Set up error tracking (Sentry, Rollbar)
- Monitor application performance
- Track API response times
- Alert on high error rates

#### System Monitoring
- CPU and memory usage
- Disk space availability
- Database performance
- Network connectivity

### 10. Maintenance

#### Regular Tasks
- Update dependencies monthly
- Run security scans
- Clean up old logs
- Monitor backup integrity

#### Database Maintenance
```bash
# Vacuum and analyze
VACUUM ANALYZE;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname != 'pg_catalog';
```

## Troubleshooting

### Application Won't Start
1. Check Python version: `python --version`
2. Verify dependencies: `pip list`
3. Check database connection
4. Review application logs

### Database Connection Issues
```bash
# Test connection
psql -h localhost -U econsular_user -d econsular_prod -c "SELECT 1;"
```

### High Memory Usage
- Check for memory leaks in application code
- Optimize database queries
- Reduce worker count in Gunicorn

### Slow Application
- Profile database queries
- Check server resources
- Review application logs for errors
- Enable query caching

## Rollback Procedure

### Code Rollback
```bash
# Using Git
git log --oneline
git revert <commit-hash>
git push

# Or restore from backup
git reset --hard <previous-version>
```

### Database Rollback
```bash
# Restore from backup
psql -U econsular_user econsular_prod < backup.sql
```

## Contact and Support

- **Documentation**: See TECHNICAL_GUIDE.md
- **Issues**: Create GitHub issues for bug reports
- **Development**: Contact development team for features
