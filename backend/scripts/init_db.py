#!/usr/bin/env python
"""
Database initialization script for e-Consulaire RDC
Creates all necessary database tables and initializes the database
"""
import os
import sys
from datetime import datetime
from app import app, db
from backend.models import (
    User, Application, Document, StatusHistory, AuditLog, 
    Notification, UniteConsulaire, Service, UniteConsulaire_Service
)

def init_db():
    """Initialize the database by creating all tables"""
    with app.app_context():
        print("🔄 Initializing database...")
        
        # Drop all tables if they exist (only in development)
        if os.environ.get('ENVIRONMENT') != 'production':
            print("  → Dropping existing tables...")
            db.drop_all()
        
        # Create all tables
        print("  → Creating tables...")
        db.create_all()
        
        # Create default services
        print("  → Creating default services...")
        create_default_services()
        
        # Create default admin user
        print("  → Creating default admin user...")
        create_default_admin()
        
        print("✅ Database initialization complete!")

def create_default_services():
    """Create default consular services"""
    services_data = [
        {
            'code': 'carte_consulaire',
            'nom': 'Carte Consulaire',
            'description': 'Délivrance de carte consulaire pour les ressortissants congolais',
            'tarif_de_base': 50.0,
            'delai_traitement': 5,
            'documents_requis': '["passeport", "photo", "justificatif_residence"]'
        },
        {
            'code': 'attestation_prise_charge',
            'nom': 'Attestation de Prise en Charge',
            'description': 'Document attestant la prise en charge d\'un citoyen',
            'tarif_de_base': 25.0,
            'delai_traitement': 3,
            'documents_requis': '["piece_identite", "justificatifs_financiers"]'
        },
        {
            'code': 'legalisations',
            'nom': 'Légalisations',
            'description': 'Légalisation de documents administratifs',
            'tarif_de_base': 30.0,
            'delai_traitement': 7,
            'documents_requis': '["document_original", "copie"]'
        },
        {
            'code': 'passeport',
            'nom': 'Passeport',
            'description': 'Délivrance et renouvellement de passeport',
            'tarif_de_base': 100.0,
            'delai_traitement': 14,
            'documents_requis': '["ancien_passeport", "photo", "acte_naissance"]'
        },
        {
            'code': 'autres_documents',
            'nom': 'Autres Documents',
            'description': 'Traitement d\'autres documents consulaires',
            'tarif_de_base': 20.0,
            'delai_traitement': 5,
            'documents_requis': '["piece_identite"]'
        },
        {
            'code': 'etat_civil',
            'nom': 'État Civil',
            'description': 'Documents d\'état civil (actes de naissance, mariage, décès)',
            'tarif_de_base': 35.0,
            'delai_traitement': 10,
            'documents_requis': '["justificatifs", "piece_identite"]'
        },
        {
            'code': 'procuration',
            'nom': 'Procuration',
            'description': 'Établissement de procurations légales',
            'tarif_de_base': 40.0,
            'delai_traitement': 5,
            'documents_requis': '["piece_identite", "justificatif_domicile"]'
        }
    ]
    
    for service_data in services_data:
        existing = Service.query.filter_by(code=service_data['code']).first()
        if not existing:
            service = Service(**service_data)
            db.session.add(service)
            print(f"    ✓ Created service: {service_data['nom']}")
    
    db.session.commit()

def create_default_admin():
    """Create default admin user"""
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
        print(f"    ✓ Created admin user: {admin_user.email}")

if __name__ == '__main__':
    init_db()
