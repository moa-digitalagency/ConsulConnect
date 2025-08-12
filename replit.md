# Overview

e-Consulaire is a comprehensive digital platform for the Democratic Republic of Congo's consular services. The application provides online access to various consular services including consular cards, care attestations, document legalizations, passport applications, and other official documents. Users can submit applications online, upload required documents, make payments, and track their application status through a secure portal.

# User Preferences

Preferred communication style: Simple, everyday language.
UI Design: Modern glassmorphism style with Tailwind CSS
Login Structure: Three separate login interfaces - /admin, /login, /consulate
Remove landing page, direct access to login interfaces only

## New Hierarchical System Requirements (August 2025)
- Super Admin/Admin creates consular units (embassies, consulates, diplomatic missions)
- Agents are assigned to specific consular units
- Agents configure available services with variable pricing for their unit
- Forms appear automatically based on user geographic location
- Service requests are routed to appropriate agents by consular unit

# System Architecture

## Web Framework
The application is built using Flask, a Python web framework, providing a lightweight yet robust foundation for the consular services platform. Flask-SQLAlchemy is used for database operations with a declarative base model approach.

## Authentication & Authorization
User authentication is handled through Flask-Login with role-based access control supporting four user types:
- **usager** (regular users/citizens) → /login portal
- **agent** (consular staff) → /consulate portal  
- **admin** (administrators) → /admin portal
- **superviseur** (super admins) → /admin portal

Sessions are managed securely with environment-based secret keys and support for "remember me" functionality.

## Hierarchical Consular Unit System
The new architecture implements a three-tier management system:

### 1. Super Admin/Admin Level
- Creates and manages consular units (UniteConsulaire)
- Assigns agents to specific units
- Oversees overall system operations

### 2. Agent Level  
- Configures available services for their assigned unit
- Sets variable pricing through UniteConsulaire_Service
- Processes applications routed to their unit

### 3. User Level
- Selects appropriate embassy/consulate based on location
- Submits service requests routed to assigned agents
- Forms automatically appear based on geographic matching

## Database Architecture
The system uses SQLAlchemy ORM with PostgreSQL database. Enhanced database models include:

### Core Models
- **User**: Stores user profiles, roles, and authentication data (now includes unite_consulaire_id for agents)
- **Application**: Tracks service requests with status workflow management (now includes unite_consulaire_id)
- **Document**: Handles file uploads and attachments
- **StatusHistory**: Maintains audit trail of application state changes

### New Hierarchical Models (August 2025)
- **UniteConsulaire**: Represents embassies, consulates, and diplomatic missions
- **Service**: Master list of available consular services with base configurations
- **UniteConsulaire_Service**: Junction table linking units to services with custom pricing
- **AuditLog**: System-wide audit trail
- **Notification**: User notification system

### Service Management Workflow
1. Super Admin creates UniteConsulaire (embassy, consulate, diplomatic mission)
2. Admin assigns agents (User.unite_consulaire_id)
3. Agent configures services via UniteConsulaire_Service with custom tariffs
4. Geographic routing displays relevant forms to users
5. Applications route to appropriate agents based on selected unit

## Implementation Status (August 2025)

### ✅ Completed Features
- **Database Architecture**: All hierarchical models implemented (UniteConsulaire, Service, UniteConsulaire_Service)
- **PostgreSQL Integration**: Production-ready database with proper relationships
- **Test Data Creation**: International consular units created (Rabat, Paris, Bruxelles, Kinshasa)
- **Service Configuration**: Base services with customizable pricing per unit
- **Administrative Routes**: Basic admin interfaces for unit and service management
- **API Endpoints**: Geographic-based unit discovery for forms

### 🏛️ Current Consular Units
- **Kinshasa**: Unité Consulaire Principale (RD Congo) - Base unit
- **Rabat**: Ambassade de la RD Congo au Maroc - 4 services configurés
- **Paris**: Ambassade de la RD Congo en France - 5 services configurés  
- **Bruxelles**: Consulat Général à Bruxelles - 4 services configurés

### 🔧 Admin Routes Implemented
- `/admin/hierarchy` - Complete system overview with statistics
- `/admin/units` - List all consular units with metrics
- `/admin/units/<id>/services` - Service configuration per unit
- `/agent/my-unit` - Agent dashboard for assigned unit
- `/api/units-by-location` - Geographic unit discovery
- `/api/unit-services/<id>` - Service pricing API

### 🎯 Next Phase Requirements
- Form modification to include embassy selection dropdown
- Geographic auto-detection based on user location
- Agent service configuration interface
- Enhanced application routing to assigned agents
- Pricing display integration in service forms

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