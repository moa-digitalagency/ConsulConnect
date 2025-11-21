#!/usr/bin/env python
"""
Demo data generator for e-Consulaire RDC
Creates sample data for testing and demonstration
"""
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from backend.models import (
    User, Application, Document, StatusHistory, AuditLog,
    Notification, UniteConsulaire, Service, UniteConsulaire_Service
)

def create_demo_data():
    """Create comprehensive demo data"""
    with app.app_context():
        print("🎬 Creating demo data...")
        
        # Create demo consular units
        print("  → Creating consular units...")
        create_demo_units()
        
        # Create demo users
        print("  → Creating demo users...")
        create_demo_users()
        
        # Create demo applications
        print("  → Creating demo applications...")
        create_demo_applications()
        
        # Create demo notifications
        print("  → Creating demo notifications...")
        create_demo_notifications()
        
        print("✅ Demo data creation complete!")

def create_demo_units():
    """Create demo consular units"""
    units_data = [
        {
            'nom': 'Ambassade RDC Maroc',
            'type': 'ambassade',
            'ville': 'Rabat',
            'pays': 'Maroc',
            'chef_nom': 'Amb. Jean Mbongo',
            'chef_titre': 'Ambassadeur',
            'email_principal': 'ambassade@maroc.diplomatie.cd',
            'telephone_principal': '+212-537-123456',
            'adresse_rue': 'Avenue Moulay Hassan',
            'code_pays': 'MAR'
        },
        {
            'nom': 'Consulat RDC France',
            'type': 'consulat',
            'ville': 'Paris',
            'pays': 'France',
            'chef_nom': 'Cons. Pierre Lukele',
            'chef_titre': 'Consul Général',
            'email_principal': 'consulat@paris.diplomatie.cd',
            'telephone_principal': '+33-1-45678901',
            'adresse_rue': 'Rue de la République',
            'code_pays': 'FRA'
        },
        {
            'nom': 'Ambassade RDC Belgique',
            'type': 'ambassade',
            'ville': 'Bruxelles',
            'pays': 'Belgique',
            'chef_nom': 'Amb. Anne Kasongo',
            'chef_titre': 'Ambassadeur',
            'email_principal': 'ambassade@belgique.diplomatie.cd',
            'telephone_principal': '+32-2-12345678',
            'adresse_rue': 'Avenue Louise',
            'code_pays': 'BEL'
        }
    ]
    
    for unit_data in units_data:
        existing = UniteConsulaire.query.filter_by(nom=unit_data['nom']).first()
        if not existing:
            # Get admin user for created_by
            admin = User.query.filter_by(role='superviseur').first()
            unit_data['created_by'] = admin.id if admin else 1
            
            unit = UniteConsulaire(**unit_data)
            db.session.add(unit)
            db.session.flush()
            
            # Assign all services to this unit
            services = Service.query.all()
            for service in services:
                unit_service = UniteConsulaire_Service(
                    unite_consulaire_id=unit.id,
                    service_id=service.id,
                    tarif_personnalise=service.tarif_de_base,
                    configured_by=admin.id if admin else 1
                )
                db.session.add(unit_service)
            
            print(f"    ✓ Created unit: {unit_data['nom']}")
    
    db.session.commit()

def create_demo_users():
    """Create demo users with different roles"""
    users_data = [
        {
            'username': 'agent_rabat',
            'email': 'agent.rabat@diplomatie.cd',
            'first_name': 'Mohamed',
            'last_name': 'Hamdaoui',
            'role': 'agent',
            'phone': '+212-612345678',
            'password': 'agent123'
        },
        {
            'username': 'agent_paris',
            'email': 'agent.paris@diplomatie.cd',
            'first_name': 'Claude',
            'last_name': 'Dupont',
            'role': 'agent',
            'phone': '+33-612345678',
            'password': 'agent123'
        },
        {
            'username': 'user_demo1',
            'email': 'demo.user1@example.com',
            'first_name': 'Jean',
            'last_name': 'Mugambi',
            'role': 'usager',
            'phone': '+243-812345678',
            'password': 'user123',
            'profile_complete': True,
            'genre': 'M',
            'date_naissance': datetime(1985, 5, 15).date(),
            'lieu_naissance': 'Kinshasa',
            'adresse_ville': 'Kinshasa',
            'adresse_pays': 'Congo (RDC)'
        },
        {
            'username': 'user_demo2',
            'email': 'demo.user2@example.com',
            'first_name': 'Marie',
            'last_name': 'Kalomba',
            'role': 'usager',
            'phone': '+243-823456789',
            'password': 'user123',
            'profile_complete': True,
            'genre': 'F',
            'date_naissance': datetime(1990, 8, 22).date(),
            'lieu_naissance': 'Lubumbashi',
            'adresse_ville': 'Paris',
            'adresse_pays': 'France'
        }
    ]
    
    for user_data in users_data:
        password = user_data.pop('password')
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User(**user_data)
            user.password_hash = generate_password_hash(password)
            db.session.add(user)
            print(f"    ✓ Created user: {user_data['email']}")
    
    db.session.commit()

def create_demo_applications():
    """Create demo applications with various statuses"""
    users = User.query.filter_by(role='usager').all()
    services = Service.query.all()
    units = UniteConsulaire.query.all()
    agents = User.query.filter_by(role='agent').all()
    
    if not users or not services or not units:
        print("    ⚠ Skipping demo applications (missing prerequisites)")
        return
    
    statuses = ['soumise', 'en_traitement', 'validee', 'rejetee']
    
    for i, user in enumerate(users[:2]):
        for j, service in enumerate(services[:3]):
            app_status = statuses[j % len(statuses)]
            agent = agents[i % len(agents)] if agents else None
            unit = units[i % len(units)]
            
            application = Application(
                user_id=user.id,
                unite_consulaire_id=unit.id,
                service_type=service.code,
                status=app_status,
                form_data='{}',
                payment_amount=service.tarif_de_base,
                processed_by=agent.id if agent else None
            )
            db.session.add(application)
            db.session.flush()
            
            # Add status history
            status_history = StatusHistory(
                application_id=application.id,
                new_status=app_status,
                changed_by=agent.id if agent else user.id,
                comment=f'Demande {app_status}'
            )
            db.session.add(status_history)
            print(f"    ✓ Created application: {application.reference_number} ({service.code})")
    
    db.session.commit()

def create_demo_notifications():
    """Create demo notifications"""
    users = User.query.filter_by(role='usager').all()
    
    notification_types = [
        {
            'title': 'Votre demande est en cours',
            'message': 'Votre demande de carte consulaire est actuellement en traitement.',
            'type': 'info'
        },
        {
            'title': 'Document requis',
            'message': 'Veuillez fournir une copie certifiée de votre passeport.',
            'type': 'warning'
        },
        {
            'title': 'Demande approuvée',
            'message': 'Félicitations! Votre demande a été approuvée.',
            'type': 'success'
        }
    ]
    
    for i, user in enumerate(users[:2]):
        for j, notif_data in enumerate(notification_types):
            notification = Notification(
                user_id=user.id,
                **notif_data,
                is_read=j > 0
            )
            db.session.add(notification)
            print(f"    ✓ Created notification for {user.email}")
    
    db.session.commit()

if __name__ == '__main__':
    create_demo_data()
