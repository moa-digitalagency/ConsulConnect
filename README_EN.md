# e-Consulaire DRC - Consular Services System

[![🇺🇸 English](https://img.shields.io/badge/🇺🇸-English-blue?style=for-the-badge)](README_EN.md) [![🇫🇷 Français](https://img.shields.io/badge/🇫🇷-Français-red?style=for-the-badge&color=red)](README.md)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API](#api)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## 🌍 Overview

**e-Consulaire DRC** is a comprehensive digital platform for the Democratic Republic of Congo's consular services. This application enables citizens to access various consular services online and allows diplomatic agents to efficiently manage requests.

### ✨ Key Features

- **🏛️ Hierarchical System**: Multi-level management (Supervisor → Admin → Agent → User)
- **🌐 Multi-unit Support**: Support for embassies, consulates, and diplomatic missions
- **🔐 Enhanced Security**: AES-256 encryption, multi-factor authentication
- **📧 Automatic Notifications**: SendGrid for communications
- **💳 Integrated Payments**: Support for secure transactions
- **📊 Advanced Dashboard**: Real-time statistics and tracking

## 🎯 Features

### 👥 User Management
- **System Supervisor**: Global management, consular unit creation
- **Administrator**: Local management, service configuration
- **Consular Agent**: Request processing, document validation
- **User**: Request submission, status tracking

### 📄 Consular Services
- **Consular Card** ($50 USD)
- **Care Attestation** ($25 USD)
- **Document Legalization** ($30-50 USD based on urgency)
- **Passport Pre-application** ($100 USD)
- **Other Official Documents** ($20 USD)

### 🏢 Unit Management
- Creation and configuration of embassies/consulates
- Agent assignment by geographical unit
- Variable pricing per consular unit
- Automatic routing based on geolocation

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Email**: SendGrid API
- **Security**: bcrypt, cryptography, JWT
- **Server**: Gunicorn with reload support

### Database Structure

```sql
-- Main Models
User                    -- System users
UniteConsulaire        -- Embassies/Consulates
Service               -- Consular services
Application           -- User requests
Document              -- Attached files
AuditLog              -- Audit trail
Notification          -- User notifications

-- Relations
UniteConsulaire_Service -- Services per unit with pricing
StatusHistory          -- Status history
```

### Security Architecture
- **Encryption**: AES-256 for sensitive data
- **Authentication**: Secure sessions with Flask-Login
- **Authorization**: RBAC (Role-Based Access Control)
- **Audit**: Complete user action traceability

## 🚀 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Git

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/your-org/e-consulaire-rdc.git
cd e-consulaire-rdc

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings

# Initialize the database
python backend/scripts/init_db.py

# (Optional) Create demo data
python backend/scripts/demo_data.py

# Start the application
python main.py
# Or in production:
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/e_consulaire

# Security
SESSION_SECRET=your_very_secure_secret_key
ENCRYPTION_KEY=your_32_character_encryption_key

# Email (SendGrid)
SENDGRID_API_KEY=your_sendgrid_key

# PostgreSQL (auto-configured on Replit)
PGHOST=localhost
PGPORT=5432
PGUSER=your_user
PGPASSWORD=your_password
PGDATABASE=e_consulaire
```

### Consular Units Configuration

```python
# Pre-configured unit examples
units = [
    {
        "nom": "DRC Embassy in Morocco",
        "type_unite": "Embassy",
        "pays": "Morocco",
        "ville": "Rabat",
        "email": "embassy@drcongo-morocco.org"
    },
    {
        "nom": "Consulate General in Brussels",
        "type_unite": "Consulate",
        "pays": "Belgium", 
        "ville": "Brussels",
        "email": "consulate@drcongo-belgium.be"
    }
]
```

## 💻 Usage

### Interface Access

- **Users**: `/login` - Citizen interface
- **Agents**: `/consulate` - Consular interface
- **Admins/Supervisors**: `/admin` - Administration interface

### Request Workflow

1. **Submission**: User fills out online form
2. **Validation**: Upload required documents
3. **Payment**: Secure transaction
4. **Processing**: Review by consular agent
5. **Approval**: Final validation
6. **Generation**: Official document with QR code

### REST API

```python
# Unit discovery by geolocation
GET /api/units-by-location?country=France&city=Paris

# Available services per unit
GET /api/unit-services/1

# Application submission
POST /api/applications
{
    "service_id": 1,
    "unite_consulaire_id": 2,
    "personal_data": {...},
    "documents": [...]
}
```

## 🔒 Security

### Protection Measures
- **End-to-end encryption**: All sensitive data
- **Secure sessions**: Automatic expiration
- **Server-side validation**: CSRF/XSS protection
- **Complete audit**: Traceability of all actions
- **Automatic backup**: Backup and restoration

### Compliance
- **GDPR**: Personal data protection
- **Diplomatic standards**: International consular security
- **PCI DSS**: Payment security (if applicable)

## 🤝 Contributing

### Development Process

```bash
# Create a feature branch
git checkout -b feature/new-feature

# Develop and test
python -m pytest tests/

# Submit a pull request
git push origin feature/new-feature
```

### Code Standards
- **PEP 8**: Python code style
- **Type hints**: Type annotations
- **Docstrings**: Function documentation
- **Unit tests**: Coverage > 80%

## 📊 Project Status

### ✅ Completed Features
- Complete hierarchical architecture
- CRUD for all entities
- Robust authentication system
- Modern user interface
- Optimized PostgreSQL database

### 🚧 In Development
- Integrated payment module
- Companion mobile application
- Public REST API
- Advanced analytics dashboard

### 🎯 Upcoming Versions
- **v2.0**: Stripe payment module
- **v2.1**: Complete REST API
- **v2.2**: iOS/Android mobile application
- **v3.0**: AI for automatic validation

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## 📞 Support

### Technical Contact
- **Email**: support@diplomatie.gouv.cd
- **Documentation**: [Project Wiki](https://github.com/your-org/e-consulaire-rdc/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/e-consulaire-rdc/issues)

### Development Team
- **Lead Developer**: [Lead developer name]
- **DevOps**: [DevOps name]
- **UI/UX**: [Designer name]

---

**Developed with ❤️ for the Democratic Republic of Congo**

[![🇫🇷 Version Française](https://img.shields.io/badge/🇫🇷-Lire%20en%20Français-red?style=for-the-badge&color=red)](README.md)