# e-Consulaire RDC - Consular Services System

## Overview

**e-Consulaire RDC** is a comprehensive digital platform for the Democratic Republic of Congo's consular services. This Flask-based web application enables citizens to access various consular services online while providing a hierarchical management system for diplomatic personnel. The platform supports multiple user roles (Supervisor → Admin → Agent → User) across different consular units worldwide, featuring secure document processing, payment integration, and real-time status tracking.

The system handles key consular services including consular cards, care attestations, document legalization, passport pre-applications, and other official documents, with variable pricing and automated routing based on geographical units.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **CSS Framework**: Tailwind CSS with custom corporate styling for professional appearance
- **JavaScript**: Vanilla JavaScript with modular components for form validation, file uploads, and interactive features
- **Design System**: Corporate theme with RDC national colors (blue, yellow, red) and diplomatic branding
- **Responsive Design**: Mobile-first approach with accessibility features and multi-language support (French/English)

### Backend Architecture
- **Web Framework**: Flask with modular blueprint structure for different user roles
- **Database ORM**: SQLAlchemy with declarative base for database operations
- **Authentication**: Flask-Login with session management and role-based access control
- **File Handling**: Secure file upload system with size limits and type validation
- **Email System**: Flask-Mail integration with SendGrid support for automated notifications

### Database Design
- **Primary Database**: PostgreSQL (production) / SQLite (development) with connection pooling
- **User Management**: Hierarchical role system (superviseur → admin → agent → usager)
- **Document Storage**: File-based storage with database metadata tracking
- **Audit Logging**: Comprehensive audit trail for all system actions and security events

### Security Implementation
- **Encryption**: AES-256 encryption service for sensitive data
- **Authentication**: Multi-factor authentication support with secure password hashing
- **Session Security**: CSRF protection and secure session management
- **Access Control**: Role-based permissions with unit-specific access restrictions
- **Security Monitoring**: Automated security event logging and rate limiting

### Service Layer Architecture
- **Email Service**: SendGrid integration for transactional emails and notifications
- **Notification Service**: Real-time notification system for application status updates
- **Backup Service**: Automated backup system with configurable retention policies
- **Update Service**: Git-based automatic update system with database migration support
- **Security Service**: Centralized security functions including encryption and audit logging

### Data Management
- **Application Processing**: Structured workflow for consular service requests
- **Document Generation**: PDF generation with QR codes for verification
- **Status Tracking**: Real-time application status with notification triggers
- **Geographic Routing**: Automatic unit assignment based on user location

## External Dependencies

### Core Infrastructure
- **Flask**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **PostgreSQL/SQLite**: Primary database systems
- **Werkzeug**: WSGI utilities and security helpers

### Authentication & Security
- **Flask-Login**: User session management
- **Cryptography**: AES-256 encryption implementation
- **PBKDF2**: Password hashing with salt

### Email & Communications
- **SendGrid**: Email delivery service for notifications
- **Flask-Mail**: Email integration framework

### Frontend & UI
- **Tailwind CSS**: Utility-first CSS framework
- **Font Awesome**: Icon library for UI elements
- **ReportLab**: PDF document generation

### Development & Deployment
- **Git**: Version control and automatic updates
- **Schedule**: Task scheduling for automated operations

### Payment Processing
- **Simulated Payment System**: Configurable payment methods for different services

### File & Document Management
- **File Upload System**: Secure file handling with validation
- **QR Code Generation**: Document verification system

### System Monitoring
- **Audit Logging**: Comprehensive system activity tracking
- **Backup Services**: Automated data backup and recovery
- **Security Monitoring**: Real-time security event detection