#!/usr/bin/env python3
"""
Script d'initialisation de la base de données pour le déploiement en production.
Ce script crée toutes les tables nécessaires et initialise les données de démonstration.
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """Initialise la base de données avec la structure et les données"""
    try:
        from app import app, db
        from werkzeug.security import generate_password_hash
        from backend.models import (
            User, UniteConsulaire, Service, UniteConsulaire_Service, 
            Application, StatusHistory, Notification
        )
        import json
        
        with app.app_context():
            logger.info("Création des tables de la base de données...")
            db.create_all()
            logger.info("✓ Tables créées avec succès")
            
            # Créer les services par défaut
            logger.info("Création des services par défaut...")
            services_data = [
                {
                    'code': 'carte_consulaire',
                    'nom': 'Carte Consulaire',
                    'description': 'Délivrance de carte consulaire pour les ressortissants congolais',
                    'tarif_de_base': 50.0,
                    'delai_traitement': 5,
                    'documents_requis': json.dumps(['passeport', 'photo', 'justificatif_residence']),
                    'actif': True
                },
                {
                    'code': 'attestation_prise_charge',
                    'nom': 'Attestation de Prise en Charge',
                    'description': 'Document attestant la prise en charge d\'un citoyen',
                    'tarif_de_base': 25.0,
                    'delai_traitement': 3,
                    'documents_requis': json.dumps(['piece_identite', 'justificatifs_financiers']),
                    'actif': True
                },
                {
                    'code': 'legalisations',
                    'nom': 'Légalisations',
                    'description': 'Légalisation de documents administratifs',
                    'tarif_de_base': 30.0,
                    'delai_traitement': 7,
                    'documents_requis': json.dumps(['document_original', 'copie']),
                    'actif': True
                },
                {
                    'code': 'passeport',
                    'nom': 'Passeport',
                    'description': 'Délivrance et renouvellement de passeport',
                    'tarif_de_base': 100.0,
                    'delai_traitement': 14,
                    'documents_requis': json.dumps(['ancien_passeport', 'photo', 'acte_naissance']),
                    'actif': True
                },
                {
                    'code': 'autres_documents',
                    'nom': 'Autres Documents',
                    'description': 'Traitement d\'autres documents consulaires',
                    'tarif_de_base': 20.0,
                    'delai_traitement': 5,
                    'documents_requis': json.dumps(['piece_identite']),
                    'actif': True
                },
                {
                    'code': 'etat_civil',
                    'nom': 'État Civil',
                    'description': 'Documents d\'état civil (actes de naissance, mariage, décès)',
                    'tarif_de_base': 35.0,
                    'delai_traitement': 10,
                    'documents_requis': json.dumps(['justificatifs', 'piece_identite']),
                    'actif': True
                },
                {
                    'code': 'procuration',
                    'nom': 'Procuration',
                    'description': 'Établissement de procurations légales',
                    'tarif_de_base': 40.0,
                    'delai_traitement': 5,
                    'documents_requis': json.dumps(['piece_identite', 'justificatif_domicile']),
                    'actif': True
                }
            ]
            
            for service_data in services_data:
                existing = Service.query.filter_by(code=service_data['code']).first()
                if not existing:
                    service = Service(**service_data)
                    db.session.add(service)
                    logger.info(f"  ✓ Service créé: {service_data['nom']}")
            
            db.session.commit()
            logger.info("✓ Services créés avec succès")
            
            # Créer un super utilisateur administrateur si non existant
            logger.info("Création du compte administrateur principal...")
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@diplomatie.gouv.cd')
            
            # Require admin password in production
            if os.environ.get('FLASK_ENV') == 'production':
                if not os.environ.get('ADMIN_PASSWORD'):
                    raise RuntimeError("ADMIN_PASSWORD environment variable must be set in production")
                admin_password = os.environ.get('ADMIN_PASSWORD')
            else:
                admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                if admin_password == 'admin123':
                    logger.warning("Using default admin password for development. CHANGE THIS IN PRODUCTION!")
            
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    username='admin',
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    role='superviseur',
                    first_name='Administrateur',
                    last_name='Système',
                    active=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info(f"✓ Compte admin créé: {admin_email}")
                logger.warning(f"⚠ IMPORTANT: Changez le mot de passe par défaut!")
            else:
                logger.info(f"✓ Compte admin existant: {admin_email}")
            
            logger.info("=" * 60)
            logger.info("Initialisation de la base de données terminée avec succès!")
            logger.info("=" * 60)
            logger.info(f"Email admin: {admin_email}")
            logger.info(f"Mot de passe: {'Déjà configuré' if admin_password == 'admin123' else admin_password}")
            logger.info("=" * 60)
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Erreur lors de l'initialisation de la base de données: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_demo_data():
    """Crée des données de démonstration (optionnel, pour les environnements de test)"""
    try:
        from app import app, db
        from werkzeug.security import generate_password_hash
        from backend.models import User, UniteConsulaire, Application
        import json
        
        with app.app_context():
            logger.info("Création des unités consulaires de démonstration...")
            
            # Get first superviseur as creator
            creator = User.query.filter_by(role='superviseur').first()
            if not creator:
                logger.warning("Aucun superviseur trouvé, impossible de créer les unités demo")
                return False
            
            # Unités consulaires
            consular_units = [
                {
                    'nom': 'Ambassade RDC Maroc',
                    'type': 'ambassade',
                    'pays': 'Maroc',
                    'ville': 'Rabat',
                    'chef_nom': 'Amb. Jean Mbongo',
                    'chef_titre': 'Ambassadeur',
                    'adresse_complete': 'Avenue Moulay Hassan, Rabat, Maroc',
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
                    'email_principal': 'ambassade@belgique.diplomatie.cd',
                    'telephone_principal': '+32-2-12345678',
                    'code_pays': 'BEL',
                    'active': True,
                    'created_by': creator.id
                }
            ]
            
            for unit_data in consular_units:
                existing = UniteConsulaire.query.filter_by(
                    pays=unit_data['pays'],
                    ville=unit_data['ville']
                ).first()
                
                if not existing:
                    unit = UniteConsulaire(**unit_data)
                    db.session.add(unit)
                    logger.info(f"  ✓ Unité créée: {unit_data['nom']}")
            
            db.session.commit()
            logger.info("✓ Unités consulaires de démonstration créées")
            
            # Créer les agents consulaires
            logger.info("Création des agents consulaires...")
            unite_rabat = UniteConsulaire.query.filter_by(ville='Rabat').first()
            unite_paris = UniteConsulaire.query.filter_by(ville='Paris').first()
            unite_bruxelles = UniteConsulaire.query.filter_by(ville='Bruxelles').first()
            
            agents_data = [
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
                    'username': 'agent_bruxelles',
                    'email': 'agent.bruxelles@diplomatie.cd',
                    'password': 'agent123',
                    'role': 'agent',
                    'first_name': 'Sophie',
                    'last_name': 'Lemoine',
                    'active': True,
                    'phone': '+32 470 12 34 56',
                    'unite_consulaire_id': unite_bruxelles.id if unite_bruxelles else None
                }
            ]
            
            for user_data in agents_data:
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
                    logger.info(f"  ✓ Agent créé: {user.email}")
            
            db.session.commit()
            
            # Configurer les services pour les unités
            logger.info("Configuration des services pour les unités consulaires...")
            from backend.models import UniteConsulaire_Service, Service
            
            unites = UniteConsulaire.query.filter_by(active=True).all()
            services = Service.query.filter_by(actif=True).all()
            admin = User.query.filter_by(role='superviseur').first()
            
            if unites and services and admin:
                for unite in unites:
                    for service in services:
                        existing = UniteConsulaire_Service.query.filter_by(
                            unite_consulaire_id=unite.id,
                            service_id=service.id
                        ).first()
                        
                        if not existing:
                            config = UniteConsulaire_Service(
                                unite_consulaire_id=unite.id,
                                service_id=service.id,
                                tarif_personnalise=service.tarif_de_base,
                                devise='EUR' if unite.pays in ['France', 'Belgique'] else 'USD',
                                actif=True,
                                delai_personnalise=service.delai_traitement,
                                configured_by=admin.id
                            )
                            db.session.add(config)
                            logger.info(f"  ✓ Service {service.nom} configuré pour {unite.nom}")
                
                db.session.commit()
            
            # Créer des citoyens de démonstration
            logger.info("Création des citoyens de démonstration...")
            citizens_data = [
                {
                    'username': 'citoyen_rabat',
                    'email': 'citoyen.rabat@example.com',
                    'password': 'citoyen123',
                    'role': 'usager',
                    'first_name': 'Jean',
                    'last_name': 'Mukendi',
                    'active': True,
                    'phone': '+212 600 987 654',
                    'country': 'Maroc',
                    'city': 'Rabat',
                    'unite_consulaire_id': unite_rabat.id if unite_rabat else None
                },
                {
                    'username': 'citoyen_paris',
                    'email': 'citoyen.paris@example.com',
                    'password': 'citoyen123',
                    'role': 'usager',
                    'first_name': 'Marie',
                    'last_name': 'Kalomba',
                    'active': True,
                    'phone': '+33 6 98 76 54 32',
                    'country': 'France',
                    'city': 'Paris',
                    'unite_consulaire_id': unite_paris.id if unite_paris else None
                },
                {
                    'username': 'citoyen_bruxelles',
                    'email': 'citoyen.bruxelles@example.com',
                    'password': 'citoyen123',
                    'role': 'usager',
                    'first_name': 'Pierre',
                    'last_name': 'Tshikala',
                    'active': True,
                    'phone': '+32 470 98 76 54',
                    'country': 'Belgique',
                    'city': 'Bruxelles',
                    'unite_consulaire_id': unite_bruxelles.id if unite_bruxelles else None
                }
            ]
            
            for user_data in citizens_data:
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
                    if 'country' in user_data:
                        user.country = user_data['country']
                    if 'city' in user_data:
                        user.city = user_data['city']
                    if 'unite_consulaire_id' in user_data and user_data['unite_consulaire_id']:
                        user.unite_consulaire_id = user_data['unite_consulaire_id']
                    db.session.add(user)
                    logger.info(f"  ✓ Citoyen créé: {user.email}")
            
            db.session.commit()
            
            # Créer des demandes de démonstration
            logger.info("Création des demandes de démonstration...")
            citizens = User.query.filter_by(role='usager').all()
            services_list = Service.query.filter_by(actif=True).all()
            statuses = ['soumise', 'en_traitement', 'validee', 'documents_requis', 'pret_pour_retrait']
            
            for citizen in citizens:
                existing_apps = Application.query.filter_by(user_id=citizen.id).count()
                if existing_apps > 0:
                    continue
                
                num_apps = random.randint(2, 4)
                for i in range(num_apps):
                    service = random.choice(services_list)
                    status = random.choice(statuses)
                    
                    ref_num = f"DC{datetime.now().year}{citizen.unite_consulaire_id or 1:02d}{random.randint(1000, 9999)}"
                    
                    app_demo = Application(
                        user_id=citizen.id,
                        unite_consulaire_id=citizen.unite_consulaire_id,
                        service_type=service.code,
                        reference_number=ref_num,
                        status=status,
                        created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                        updated_at=datetime.now() - timedelta(days=random.randint(0, 5))
                    )
                    db.session.add(app_demo)
                    logger.info(f"  ✓ Demande créée: {ref_num} pour {citizen.email}")
            
            db.session.commit()
            
            logger.info("✓ Données de démonstration créées avec succès")
            logger.info("Comptes créés:")
            logger.info("  - Agent (Rabat): agent.rabat@diplomatie.cd / agent123")
            logger.info("  - Agent (Paris): agent.paris@diplomatie.cd / agent123")
            logger.info("  - Citoyen (Rabat): citoyen.rabat@example.com / citoyen123")
            logger.info("  - Citoyen (Paris): citoyen.paris@example.com / citoyen123")
            return True
            
    except Exception as e:
        logger.error(f"✗ Erreur lors de la création des données de démonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Script d'initialisation de la base de données")
    logger.info("e-Consulaire RDC")
    logger.info("=" * 60)
    
    # Initialiser la base de données
    if init_database():
        logger.info("✓ Base de données initialisée")
        
        # Demander si on veut créer les données demo
        if os.environ.get('CREATE_DEMO_DATA', '').lower() in ['true', '1', 'yes']:
            logger.info("Création des données de démonstration...")
            create_demo_data()
        
        logger.info("✓ Initialisation terminée avec succès!")
        sys.exit(0)
    else:
        logger.error("✗ Échec de l'initialisation")
        sys.exit(1)
