import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.config['SECRET_KEY'] = app.secret_key
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///econsular.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"client_encoding": "utf8"} if os.environ.get("DATABASE_URL") else {}
}

# Configure file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'noreply@diplomatie.gouv.cd')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'default_password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@diplomatie.gouv.cd')

# Configure Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.user_login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Initialize extensions
db.init_app(app)
mail.init_app(app)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create services data function
def create_default_services():
    from models import Service
    import json
    
    default_services = [
        {
            'code': 'carte_consulaire',
            'nom': 'Carte Consulaire',
            'description': 'Délivrance de carte consulaire pour les ressortissants congolais',
            'tarif_de_base': 50.0,
            'delai_traitement': 5,
            'documents_requis': json.dumps(['passeport', 'photo', 'justificatif_residence'])
        },
        {
            'code': 'attestation_prise_charge',
            'nom': 'Attestation de Prise en Charge',
            'description': 'Document attestant la prise en charge d\'un citoyen',
            'tarif_de_base': 25.0,
            'delai_traitement': 3,
            'documents_requis': json.dumps(['piece_identite', 'justificatifs_financiers'])
        },
        {
            'code': 'legalisations',
            'nom': 'Légalisations',
            'description': 'Légalisation de documents administratifs',
            'tarif_de_base': 30.0,
            'delai_traitement': 7,
            'documents_requis': json.dumps(['document_original', 'copie'])
        },
        {
            'code': 'passeport',
            'nom': 'Passeport',
            'description': 'Délivrance et renouvellement de passeport',
            'tarif_de_base': 100.0,
            'delai_traitement': 14,
            'documents_requis': json.dumps(['ancien_passeport', 'photo', 'acte_naissance'])
        },
        {
            'code': 'autres_documents',
            'nom': 'Autres Documents',
            'description': 'Traitement d\'autres documents consulaires',
            'tarif_de_base': 20.0,
            'delai_traitement': 5,
            'documents_requis': json.dumps(['piece_identite'])
        },
        {
            'code': 'etat_civil',
            'nom': 'État Civil',
            'description': 'Documents d\'état civil (actes de naissance, mariage, décès)',
            'tarif_de_base': 35.0,
            'delai_traitement': 10,
            'documents_requis': json.dumps(['justificatifs', 'piece_identite'])
        },
        {
            'code': 'procuration',
            'nom': 'Procuration',
            'description': 'Établissement de procurations légales',
            'tarif_de_base': 40.0,
            'delai_traitement': 5,
            'documents_requis': json.dumps(['piece_identite', 'justificatif_domicile'])
        }
    ]
    
    for service_data in default_services:
        existing = Service.query.filter_by(code=service_data['code']).first()
        if not existing:
            service = Service(**service_data)
            db.session.add(service)
            logging.info(f"Service created: {service_data['nom']}")
    
    db.session.commit()

with app.app_context():
    # Import models and routes
    import models
    import routes
    
    
    # Create tables
    db.create_all()
    
    # Create default services
    create_default_services()
    
    # Create default admin user if not exists
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(email='admin@diplomatie.gouv.cd').first()
    if not admin:
        admin_user = User()
        admin_user.username = 'admin'
        admin_user.email = 'admin@diplomatie.gouv.cd'
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.role = 'superviseur'
        admin_user.active = True
        admin_user.first_name = 'Administrateur'
        admin_user.last_name = 'Système'
        db.session.add(admin_user)
        db.session.commit()
        logging.info("Default admin user created")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
