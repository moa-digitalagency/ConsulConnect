import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.config['SECRET_KEY'] = app.secret_key
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///econsular.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 20,
    "pool_size": 10,
    "max_overflow": 20,
    "connect_args": {
        "client_encoding": "utf8",
        "connect_timeout": 10,
        "sslmode": "prefer"
    } if os.environ.get("DATABASE_URL") else {}
}

# Configure file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for multiple documents

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
    from backend.models import Service
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

def create_demo_users_and_data():
    """Initialise les utilisateurs de démonstration et données de test"""
    from werkzeug.security import generate_password_hash
    from backend.models import User, UniteConsulaire
    
    # Liste des utilisateurs de démonstration
    demo_users = [
        # Superviseurs
        {
            'username': 'admin',
            'email': 'admin@diplomatie.gouv.cd',
            'password': 'admin123',
            'role': 'superviseur',
            'first_name': 'Administrateur',
            'last_name': 'Système',
            'active': True
        },
        {
            'username': 'superviseur',
            'email': 'superviseur@test.cd',
            'password': 'superviseur123',
            'role': 'superviseur',
            'first_name': 'Paul',
            'last_name': 'Kabila',
            'active': True
        },
        # Citoyens/Usagers
        {
            'username': 'citoyen',
            'email': 'citoyen@test.cd',
            'password': 'citoyen123',
            'role': 'usager',
            'first_name': 'Jean',
            'last_name': 'Mukendi',
            'active': True,
            'phone': '+243 900 000 001'
        },
        {
            'username': 'usager',
            'email': 'usager@test.cd',
            'password': 'usager123',
            'role': 'usager',
            'first_name': 'Marie',
            'last_name': 'Kalala',
            'active': True,
            'phone': '+243 900 000 002'
        }
    ]
    
    # Créer les utilisateurs
    for user_data in demo_users:
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User()
            user.username = user_data['username']
            user.email = user_data['email']
            user.password_hash = generate_password_hash(user_data['password'])
            user.role = user_data['role']
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.active = user_data.get('active', True)
            if 'phone' in user_data:
                user.phone = user_data['phone']
            db.session.add(user)
            logging.info(f"User created: {user.email} (role: {user.role})")
    
    db.session.commit()
    logging.info("Demo users initialization completed")

with app.app_context():
    from backend.models import User
    from backend.routes import routes
    
    from backend.routes.routes_crud import crud_bp
    app.register_blueprint(crud_bp)
    
    db.create_all()
    create_default_services()
    create_demo_users_and_data()

@login_manager.user_loader
def load_user(user_id):
    from backend.models import User
    return User.query.get(int(user_id))

# Error handler for file size limit exceeded
@app.errorhandler(413)
def request_entity_too_large(error):
    from flask import flash, redirect, request
    flash('La taille totale des fichiers dépasse la limite autorisée de 100 MB. Veuillez réduire la taille des fichiers ou en soumettre moins à la fois.', 'error')
    # Redirect back to the referring page or home
    return redirect(request.referrer or '/')
