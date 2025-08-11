# Overview

e-Consulaire is a comprehensive digital platform for the Democratic Republic of Congo's consular services. The application provides online access to various consular services including consular cards, care attestations, document legalizations, passport applications, and other official documents. Users can submit applications online, upload required documents, make payments, and track their application status through a secure portal.

# User Preferences

Preferred communication style: Simple, everyday language.
UI Design: Modern glassmorphism style with Tailwind CSS
Login Structure: Three separate login interfaces - /admin, /login, /consulate
Remove landing page, direct access to login interfaces only

# System Architecture

## Web Framework
The application is built using Flask, a Python web framework, providing a lightweight yet robust foundation for the consular services platform. Flask-SQLAlchemy is used for database operations with a declarative base model approach.

## Authentication & Authorization
User authentication is handled through Flask-Login with role-based access control supporting three user types:
- **usager** (regular users/citizens)
- **agent** (consular staff)  
- **superviseur** (supervisors)

Sessions are managed securely with environment-based secret keys and support for "remember me" functionality.

## Database Architecture
The system uses SQLAlchemy ORM with support for both SQLite (development) and PostgreSQL (production via DATABASE_URL environment variable). Key database models include:
- **User**: Stores user profiles, roles, and authentication data
- **Application**: Tracks service requests with status workflow management
- **Document**: Handles file uploads and attachments
- **StatusHistory**: Maintains audit trail of application state changes

## Frontend Architecture
The frontend uses Bootstrap 5 for responsive design with custom CSS styling. Templates are organized using Jinja2 with a base template system. JavaScript provides client-side validation and enhanced user interactions.

## File Management
File uploads are handled through Flask-WTF with configurable upload directories and size limits (16MB max). The system supports various document formats for official submissions.

## Business Logic
The platform supports multiple consular services:
- Consular card applications ($50 USD)
- Care attestation documents ($25 USD)
- Document legalizations ($30-50 USD based on urgency)
- Passport pre-applications ($100 USD)
- Other official documents ($20 USD)

Each service follows a standardized workflow: form submission → document upload → payment processing → administrative review → approval/rejection → document generation.

## Document Generation
The system includes PDF generation capabilities using ReportLab for creating official documents with QR codes for verification. Generated documents include official letterheads and digital signatures.

## Notification System
Email notifications are integrated through Flask-Mail supporting SMTP configuration for user communications throughout the application lifecycle.

# External Dependencies

## Email Services
- **Flask-Mail**: Email delivery system configured for SMTP
- **Default SMTP**: Gmail SMTP (smtp.gmail.com:587) with TLS encryption
- **Customizable**: Environment variables support for different email providers

## Database Systems
- **SQLite**: Default development database
- **PostgreSQL**: Production database support via DATABASE_URL environment variable
- **Connection pooling**: Configured with pool recycling and pre-ping for reliability

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome 6**: Icon library for UI elements
- **jQuery**: JavaScript library for enhanced interactions (implied by Bootstrap usage)

## Python Libraries
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: WSGI utilities and password hashing
- **ReportLab**: PDF generation for official documents
- **QRCode**: QR code generation for document verification

## File Upload Security
- **Werkzeug secure_filename**: Secure file naming
- **File type validation**: Controlled file extension acceptance
- **Size limitations**: 16MB maximum file upload size

## Development Tools
- **ProxyFix**: WSGI middleware for reverse proxy deployment
- **Logging**: Python logging system for debugging and monitoring