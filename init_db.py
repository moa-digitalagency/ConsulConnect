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
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
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
            
            logger.info("✓ Données de démonstration créées avec succès")
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
