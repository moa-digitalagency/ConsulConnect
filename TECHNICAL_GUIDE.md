# e-Consulaire RDC - Technical Guide

## System Architecture

### Technology Stack
- **Backend**: Python 3.11 with Flask
- **Database**: PostgreSQL (Replit) / SQLite (Development)
- **Frontend**: Jinja2 templates with Tailwind CSS and Vanilla JavaScript
- **Authentication**: Flask-Login with role-based access control (RBAC)
- **Security**: AES-256 encryption, CSRF protection, password hashing with bcrypt

### Project Structure
```
e-consulaire/
├── backend/                    # Organized backend modules
│   ├── models/                # Database models
│   ├── routes/                # Route handlers
│   ├── services/              # Business logic services
│   └── utils/                 # Utility functions
├── templates/                 # Jinja2 templates
│   ├── auth/                  # Authentication pages
│   ├── dashboard/             # Dashboard templates
│   ├── services/              # Service forms
│   └── public/                # Public pages
├── static/                    # Frontend assets
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript files
├── uploads/                   # User-uploaded documents
├── app.py                     # Flask application factory
├── main.py                    # Application entry point
├── models.py                  # SQLAlchemy models
├── routes.py                  # Route handlers
├── config.py                  # Configuration
├── init_db.py                 # Database initialization
└── demo_data.py               # Demo data generator
```

## Database Schema

### Core Tables
- **users**: User accounts with roles (superviseur, admin, agent, usager)
- **applications**: Consular service requests
- **documents**: Uploaded files associated with applications
- **status_history**: Audit trail of application status changes
- **notifications**: User notifications
- **audit_log**: System activity logging
- **unite_consulaire**: Diplomatic units (embassies, consulates)
- **services**: Available consular services
- **unite_service**: Service pricing per unit

## User Roles

1. **Superviseur** (Supervisor)
   - System-wide administration
   - User and unit management
   - Configuration access

2. **Admin** (Administrator)
   - Unit administration
   - Agent management
   - Service configuration

3. **Agent** (Consular Staff)
   - Application processing
   - Document verification
   - Status updates

4. **Usager** (Regular User)
   - Application submission
   - Profile management
   - Application tracking

## Key Features

### 1. Application Processing
- Service request submission
- Document upload with validation
- Multi-stage workflow (submitted → processing → approved/rejected)
- Reference number generation

### 2. Security
- CSRF token protection on all forms
- Session management with Flask-Login
- Password hashing with bcrypt
- Data encryption for sensitive fields
- Input validation and sanitization

### 3. Email Notifications
- SendGrid integration (optional)
- Application status updates
- Agent notifications

### 4. File Management
- Secure file upload system
- File type and size validation
- Organized document storage

## Deployment

### Environment Variables Required
```
DATABASE_URL=postgresql://user:password@host/database
SESSION_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
SENDGRID_API_KEY=your-sendgrid-key (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
```

### Initialize Database
```bash
python init_db.py
```

### Load Demo Data (Development Only)
```bash
python demo_data.py
```

### Start Application
```bash
python main.py          # Development
gunicorn app:app        # Production
```

## Common Issues and Solutions

### Issue: CSRF token missing
- Ensure all forms include `{{ csrf_token() }}`
- Check that forms extend from FlaskForm

### Issue: Database connection error
- Verify DATABASE_URL is correct
- Check PostgreSQL connection settings
- Test with SQLite locally

### Issue: Email not sending
- Configure SENDGRID_API_KEY environment variable
- Check email configuration in app.py
- Review email_service.py for issues

## Performance Optimization

1. **Database Queries**
   - Use eager loading for relationships
   - Implement pagination for large datasets
   - Add database indexes on frequently queried columns

2. **Caching**
   - Cache service lists and configurations
   - Implement Redis for session storage (optional)

3. **Frontend**
   - Minimize and bundle CSS/JS
   - Optimize images
   - Use async loading for non-critical scripts

## Security Checklist

- [x] CSRF protection enabled
- [x] Password hashing with bcrypt
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS prevention (Jinja2 auto-escaping)
- [x] Rate limiting on login (should be implemented)
- [x] Secure session management
- [x] Input validation and sanitization
- [x] File upload validation

## Testing

### Manual Testing
1. Test user registration and login flows
2. Test application submission for each service type
3. Test admin dashboard functionality
4. Test file uploads with various file types

### Database Testing
```bash
python -c "from app import app, db; from models import *; print(User.query.count())"
```
