#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

"""
Script utilitaire pour créer les données de test du système e-consulaire hiérarchique
"""

from app import app, db
from models import User, UniteConsulaire, Service, UniteConsulaire_Service
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

def create_test_users():
    """Créer des utilisateurs de test pour tous les rôles"""
    
    users_created = {}
    
    # Vérifier et créer Super Admin
    super_admin = User.query.filter_by(username='superadmin').first()
    if not super_admin:
        super_admin = User(
            username='superadmin',
            email='superadmin@diplomatie.gouv.cd',
            password_hash=generate_password_hash('admin123'),
            first_name='Jean',
            last_name='Kabila',
            role='superviseur',
            profile_complete=True,
            active=True
        )
        db.session.add(super_admin)
        print("✅ Super Admin créé")
    else:
        print("ℹ️  Super Admin existe déjà")
    
    # Vérifier et créer Admin 
    admin = User.query.filter_by(username='admin_rdc').first()
    if not admin:
        admin = User(
            username='admin_rdc',
            email='admin@diplomatie.gouv.cd',
            password_hash=generate_password_hash('admin123'),
            first_name='Marie',
            last_name='Tshilombo',
            role='admin',
            profile_complete=True,
            active=True
        )
        db.session.add(admin)
        print("✅ Admin créé")
    else:
        print("ℹ️  Admin existe déjà")
    
    # Vérifier et créer Agent pour Rabat
    agent_rabat = User.query.filter_by(username='agent_rabat').first()
    if not agent_rabat:
        agent_rabat = User(
            username='agent_rabat',
            email='agent.rabat@diplomatie.gouv.cd',
            password_hash=generate_password_hash('agent123'),
            first_name='Paul',
            last_name='Mukendi',
            role='agent',
            profile_complete=True,
            active=True
        )
        db.session.add(agent_rabat)
        print("✅ Agent Rabat créé")
    else:
        print("ℹ️  Agent Rabat existe déjà")
    
    # Vérifier et créer Agent pour Paris
    agent_paris = User.query.filter_by(username='agent_paris').first()
    if not agent_paris:
        agent_paris = User(
            username='agent_paris',
            email='agent.paris@diplomatie.gouv.cd',
            password_hash=generate_password_hash('agent123'),
            first_name='Claudine',
            last_name='Mbuyi',
            role='agent',
            profile_complete=True,
            active=True
        )
        db.session.add(agent_paris)
        print("✅ Agent Paris créé")
    else:
        print("ℹ️  Agent Paris existe déjà")
    
    # Vérifier et créer Usager test
    usager = User.query.filter_by(username='usager_test').first()
    if not usager:
        usager = User(
            username='usager_test',
            email='usager@test.com',
            password_hash=generate_password_hash('user123'),
            first_name='Joseph',
            last_name='Kalonji',
            role='usager',
            profile_complete=True,
            active=True,
            adresse_ville='Rabat',
            adresse_pays='Maroc'
        )
        db.session.add(usager)
        print("✅ Usager test créé")
    else:
        print("ℹ️  Usager test existe déjà")
    
    db.session.commit()
    print("✅ Utilisateurs synchronisés")
    
    return {
        'super_admin': super_admin,
        'admin': admin,
        'agent_rabat': agent_rabat,
        'agent_paris': agent_paris,
        'usager': usager
    }

def create_consular_units(users):
    """Créer des unités consulaires de test"""
    
    units_created = {}
    
    # Vérifier et créer Ambassade RDC Rabat
    ambassade_rabat = UniteConsulaire.query.filter_by(ville='Rabat', pays='Maroc').first()
    if not ambassade_rabat:
        ambassade_rabat = UniteConsulaire(
        nom='Ambassade de la RD Congo au Maroc',
        type='ambassade',
        ville='Rabat',
        pays='Maroc',
        code_pays='MAR',
        adresse_complete='Avenue Mehdi Ben Barka, Souissi, Rabat 10170, Maroc',
        telephone='+212 5 37-75-47-64',
        email='info@amb-rdc-rabat.org',
        timezone='Africa/Casablanca',
        created_by=users['admin'].id
    )
    
    # Ambassade RDC Paris
    ambassade_paris = UniteConsulaire(
        nom='Ambassade de la RD Congo en France',
        type='ambassade',
        ville='Paris',
        pays='France',
        code_pays='FRA',
        adresse_complete='32 cours Albert 1er, 75008 Paris, France',
        telephone='+33 1-42-25-57-50',
        email='info@amb-rdc-paris.org',
        timezone='Europe/Paris',
        created_by=users['admin'].id
    )
    
    # Consulat RDC Bruxelles
    consulat_bruxelles = UniteConsulaire(
        nom='Consulat Général de la RD Congo à Bruxelles',
        type='consulat',
        ville='Bruxelles',
        pays='Belgique',
        code_pays='BEL',
        adresse_complete='Avenue de Tervuren 4, 1040 Bruxelles, Belgique',
        telephone='+32 2-743-96-60',
        email='info@consulat-rdc-bruxelles.be',
        timezone='Europe/Brussels',
        created_by=users['super_admin'].id
    )
    
    db.session.add_all([ambassade_rabat, ambassade_paris, consulat_bruxelles])
    db.session.commit()
    print("✅ Unités consulaires créées")
    
    return {
        'rabat': ambassade_rabat,
        'paris': ambassade_paris,
        'bruxelles': consulat_bruxelles
    }

def assign_agents_to_units(users, units):
    """Assigner les agents aux unités consulaires"""
    
    # Assigner l'agent de Rabat
    users['agent_rabat'].unite_consulaire_id = units['rabat'].id
    
    # Assigner l'agent de Paris
    users['agent_paris'].unite_consulaire_id = units['paris'].id
    
    db.session.commit()
    print("✅ Agents assignés aux unités consulaires")

def configure_services_for_units(users, units):
    """Configurer les services pour chaque unité avec des tarifs personnalisés"""
    
    # Récupérer tous les services
    services = Service.query.all()
    
    # Configuration pour Rabat (tarifs légèrement réduits)
    rabat_configs = [
        {'service_code': 'carte_consulaire', 'tarif': 45.0},
        {'service_code': 'attestation_prise_charge', 'tarif': 20.0},
        {'service_code': 'legalisations', 'tarif': 25.0},
        {'service_code': 'passeport', 'tarif': 95.0},
        {'service_code': 'etat_civil', 'tarif': 30.0},
    ]
    
    # Configuration pour Paris (tarifs standards)
    paris_configs = [
        {'service_code': 'carte_consulaire', 'tarif': 50.0},
        {'service_code': 'attestation_prise_charge', 'tarif': 25.0},
        {'service_code': 'legalisations', 'tarif': 35.0},
        {'service_code': 'passeport', 'tarif': 100.0},
        {'service_code': 'autres_documents', 'tarif': 20.0},
        {'service_code': 'procuration', 'tarif': 40.0},
    ]
    
    # Configuration pour Bruxelles (tarifs élevés)
    bruxelles_configs = [
        {'service_code': 'carte_consulaire', 'tarif': 55.0},
        {'service_code': 'legalisations', 'tarif': 40.0},
        {'service_code': 'passeport', 'tarif': 110.0},
        {'service_code': 'etat_civil', 'tarif': 40.0},
    ]
    
    # Appliquer les configurations
    configs = [
        (units['rabat'], rabat_configs, users['agent_rabat']),
        (units['paris'], paris_configs, users['agent_paris']),
        (units['bruxelles'], bruxelles_configs, users['super_admin'])
    ]
    
    for unit, service_configs, configurator in configs:
        for config in service_configs:
            service = next((s for s in services if s.code == config['service_code']), None)
            if service:
                unite_service = UniteConsulaire_Service(
                    unite_consulaire_id=unit.id,
                    service_id=service.id,
                    tarif_personnalise=config['tarif'],
                    actif=True,
                    configured_by=configurator.id,
                    configuration=json.dumps({
                        'delai_specifique': service.delai_traitement,
                        'notes': f'Configuré pour {unit.ville}'
                    })
                )
                db.session.add(unite_service)
    
    db.session.commit()
    print("✅ Services configurés pour chaque unité consulaire")

def display_summary():
    """Afficher un résumé du système créé"""
    print("\n" + "="*60)
    print("🏛️  SYSTÈME E-CONSULAIRE HIÉRARCHIQUE INITIALISÉ")
    print("="*60)
    
    # Statistiques des utilisateurs
    users_stats = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
    print("\n👥 UTILISATEURS:")
    for role, count in users_stats:
        print(f"   • {role}: {count}")
    
    # Unités consulaires
    units = UniteConsulaire.query.all()
    print(f"\n🏢 UNITÉS CONSULAIRES: {len(units)}")
    for unit in units:
        agents_count = unit.get_agents_count()
        services_count = len(unit.get_services_actifs())
        print(f"   • {unit.nom}")
        print(f"     Agents: {agents_count} | Services: {services_count}")
    
    # Services disponibles
    services_total = Service.query.count()
    configurations_total = UniteConsulaire_Service.query.count()
    print(f"\n⚙️  SERVICES: {services_total} types disponibles")
    print(f"📋 CONFIGURATIONS: {configurations_total} tarifs personnalisés")
    
    print("\n🔑 COMPTES DE TEST:")
    print("   Super Admin: superadmin@diplomatie.gouv.cd / admin123")
    print("   Admin:       admin@diplomatie.gouv.cd / admin123")
    print("   Agent Rabat: agent.rabat@diplomatie.gouv.cd / agent123")
    print("   Agent Paris: agent.paris@diplomatie.gouv.cd / agent123")
    print("   Usager Test: usager@test.com / user123")
    print("="*60)

def main():
    """Fonction principale pour initialiser tout le système"""
    with app.app_context():
        print("🚀 Initialisation du système e-consulaire hiérarchique...")
        
        # Créer les utilisateurs
        users = create_test_users()
        
        # Créer les unités consulaires
        units = create_consular_units(users)
        
        # Assigner les agents
        assign_agents_to_units(users, units)
        
        # Configurer les services
        configure_services_for_units(users, units)
        
        # Afficher le résumé
        display_summary()
        
        print("\n✅ Système entièrement initialisé et prêt à l'emploi!")

if __name__ == '__main__':
    main()