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

def create_consular_units():
    """Créer ou mettre à jour les unités consulaires de démonstration (idempotent)"""
    from backend.models import UniteConsulaire, User
    
    # Get first superviseur as creator (should already exist from demo users)
    creator = User.query.filter_by(role='superviseur').first()
    if not creator:
        # If no supervisor exists yet, skip unit creation - will be called again later
        logging.warning("No supervisor found, skipping consular units creation for now")
        return
    
    # Define the target consular units - using stable key (pays + ville + type)
    consular_units = [
        {
            'nom': 'Ambassade RDC Maroc',
            'type': 'ambassade',
            'pays': 'Maroc',
            'ville': 'Rabat',
            'chef_nom': 'Amb. Jean Mbongo',
            'chef_titre': 'Ambassadeur',
            'adresse_complete': 'Avenue Moulay Hassan, Rabat, Maroc',
            'adresse_rue': 'Avenue Moulay Hassan',
            'email_principal': 'ambassade@maroc.diplomatie.cd',
            'telephone_principal': '+212-537-123456',
            'code_pays': 'MAR',
            'active': True,
            'created_by': creator.id
        },
        {
            'nom': 'Consulat RDC France',
            'type': 'consulat',
            'pays': 'France',
            'ville': 'Paris',
            'chef_nom': 'Cons. Pierre Lukele',
            'chef_titre': 'Consul Général',
            'adresse_complete': 'Rue de la République, Paris, France',
            'adresse_rue': 'Rue de la République',
            'email_principal': 'consulat@paris.diplomatie.cd',
            'telephone_principal': '+33-1-45678901',
            'code_pays': 'FRA',
            'active': True,
            'created_by': creator.id
        },
        {
            'nom': 'Ambassade RDC Belgique',
            'type': 'ambassade',
            'pays': 'Belgique',
            'ville': 'Bruxelles',
            'chef_nom': 'Amb. Anne Kasongo',
            'chef_titre': 'Ambassadeur',
            'adresse_complete': 'Avenue Louise, Bruxelles, Belgique',
            'adresse_rue': 'Avenue Louise',
            'email_principal': 'ambassade@belgique.diplomatie.cd',
            'telephone_principal': '+32-2-12345678',
            'code_pays': 'BEL',
            'active': True,
            'created_by': creator.id
        }
    ]
    
    # Upsert pattern: use stable composite key (pays + ville + type) to avoid duplicates
    for unit_data in consular_units:
        # Check if unit exists using stable key
        existing = UniteConsulaire.query.filter_by(
            pays=unit_data['pays'],
            ville=unit_data['ville'],
            type=unit_data['type']
        ).first()
        
        if existing:
            # Update existing unit to match current spec (handles renamed units)
            for key, value in unit_data.items():
                if key != 'created_by':  # Don't change the creator
                    setattr(existing, key, value)
            logging.info(f"Consular unit updated: {unit_data['nom']} ({unit_data['ville']}, {unit_data['pays']})")
        else:
            # Create new unit
            unit = UniteConsulaire(**unit_data)
            db.session.add(unit)
            logging.info(f"Consular unit created: {unit_data['nom']} ({unit_data['ville']}, {unit_data['pays']})")
    
    db.session.commit()

def create_demo_users_and_data():
    """Initialise les utilisateurs de démonstration et données de test"""
    from werkzeug.security import generate_password_hash
    from backend.models import User, UniteConsulaire
    
    # Créer d'abord les superviseurs (nécessaires pour created_by des unités)
    superviseurs_data = [
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
            'active': True,
            'phone': '+243 99 111 2233'
        }
    ]
    
    for user_data in superviseurs_data:
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
            logging.info(f"Supervisor created: {user.email}")
    
    db.session.commit()
    
    # Maintenant créer les unités consulaires
    create_consular_units()
    
    # Récupérer les unités pour assignation
    unite_rabat = UniteConsulaire.query.filter_by(ville='Rabat').first()
    unite_paris = UniteConsulaire.query.filter_by(ville='Paris').first()
    
    # Liste des autres utilisateurs de démonstration (superviseurs déjà créés)
    demo_users = [
        # Agents Administratifs
        {
            'username': 'agent_rabat',
            'email': 'agent.rabat@diplomatie.cd',
            'password': 'agent123',
            'role': 'agent',
            'first_name': 'Ahmed',
            'last_name': 'Benali',
            'active': True,
            'phone': '+212 600 111 222',
            'unite_consulaire_id': unite_rabat.id if unite_rabat else None
        },
        {
            'username': 'agent_paris',
            'email': 'agent.paris@diplomatie.cd',
            'password': 'agent123',
            'role': 'agent',
            'first_name': 'François',
            'last_name': 'Dubois',
            'active': True,
            'phone': '+33 6 12 34 56 78',
            'unite_consulaire_id': unite_paris.id if unite_paris else None
        },
        {
            'username': 'agent_test',
            'email': 'agent@test.cd',
            'password': 'agent123',
            'role': 'agent',
            'first_name': 'Celine',
            'last_name': 'Tshisekedi',
            'active': True,
            'phone': '+243 99 222 3344'
        },
        # Personnel Consulaire
        {
            'username': 'consul',
            'email': 'consul@test.cd',
            'password': 'consul123',
            'role': 'agent',
            'first_name': 'Dr. Michel',
            'last_name': 'Mbuyu',
            'active': True,
            'phone': '+243 99 333 4455'
        },
        {
            'username': 'attache',
            'email': 'attache@test.cd',
            'password': 'attache123',
            'role': 'agent',
            'first_name': 'Sandrine',
            'last_name': 'Kasongo',
            'active': True,
            'phone': '+243 99 444 5566'
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
            'phone': '+243 81 234 5678'
        },
        {
            'username': 'usager',
            'email': 'usager@test.cd',
            'password': 'usager123',
            'role': 'usager',
            'first_name': 'Marie',
            'last_name': 'Kalala',
            'active': True,
            'phone': '+243 82 345 6789'
        },
        {
            'username': 'demo_user1',
            'email': 'demo.user1@example.com',
            'password': 'user123',
            'role': 'usager',
            'first_name': 'Jean',
            'last_name': 'Mugambi',
            'active': True,
            'phone': '+212 600 987 654',
            'unite_consulaire_id': unite_rabat.id if unite_rabat else None
        },
        {
            'username': 'demo_user2',
            'email': 'demo.user2@example.com',
            'password': 'user123',
            'role': 'usager',
            'first_name': 'Marie',
            'last_name': 'Kalomba',
            'active': True,
            'phone': '+33 6 98 76 54 32',
            'unite_consulaire_id': unite_paris.id if unite_paris else None
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
            if 'unite_consulaire_id' in user_data and user_data['unite_consulaire_id']:
                user.unite_consulaire_id = user_data['unite_consulaire_id']
            db.session.add(user)
            logging.info(f"User created: {user.email} (role: {user.role})")
    
    db.session.commit()
    logging.info("Demo users and consular units initialization completed")

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
