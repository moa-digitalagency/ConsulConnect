#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

"""
Script pour créer des utilisateurs de test pour l'application e-Consulaire RDC
"""
import sys
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_test_users():
    """Créer des utilisateurs de test pour chaque panneau de connexion"""
    
    with app.app_context():
        print("🚀 Création des utilisateurs de test...")
        
        # Supprimer les utilisateurs de test existants
        test_emails = [
            'citoyen@test.cd', 'usager@test.cd',
            'superviseur@test.cd', 'agent@test.cd', 
            'consul@test.cd', 'attache@test.cd'
        ]
        
        for email in test_emails:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                db.session.delete(existing_user)
                print(f"❌ Suppression de l'utilisateur existant: {email}")
        
        db.session.commit()
        
        # Créer les nouveaux utilisateurs de test
        test_users = [
            # PANEL CITOYENS (/login)
            {
                'username': 'citoyen_test',
                'email': 'citoyen@test.cd',
                'password': 'citoyen123',
                'first_name': 'Jean',
                'last_name': 'Mukendi',
                'phone': '+243 81 234 5678',
                'role': 'usager',
                'language': 'fr',
                'description': 'Citoyen congolais - Compte de test'
            },
            {
                'username': 'usager_test',
                'email': 'usager@test.cd',
                'password': 'usager123',
                'first_name': 'Marie',
                'last_name': 'Kalala',
                'phone': '+243 82 345 6789',
                'role': 'usager',
                'language': 'fr',
                'description': 'Usagère des services consulaires - Compte de test'
            },
            
            # PANEL ADMINISTRATION (/admin)
            {
                'username': 'superviseur_admin',
                'email': 'superviseur@test.cd',
                'password': 'superviseur123',
                'first_name': 'Paul',
                'last_name': 'Kabila',
                'phone': '+243 99 111 2233',
                'role': 'superviseur',
                'language': 'fr',
                'description': 'Superviseur administratif - Accès complet'
            },
            {
                'username': 'agent_admin',
                'email': 'agent@test.cd',
                'password': 'agent123',
                'first_name': 'Celine',
                'last_name': 'Tshisekedi',
                'phone': '+243 99 222 3344',
                'role': 'agent',
                'language': 'fr',
                'description': 'Agent administratif - Gestion des demandes'
            },
            
            # PANEL CONSULAIRE (/consulate)
            {
                'username': 'consul_principal',
                'email': 'consul@test.cd',
                'password': 'consul123',
                'first_name': 'Dr. Michel',
                'last_name': 'Mbuyu',
                'phone': '+243 99 333 4455',
                'role': 'agent',
                'language': 'fr',
                'description': 'Agent consulaire principal - Services diplomatiques'
            },
            {
                'username': 'attache_consulaire',
                'email': 'attache@test.cd',
                'password': 'attache123',
                'first_name': 'Sandrine',
                'last_name': 'Kasongo',
                'phone': '+243 99 444 5566',
                'role': 'agent',
                'language': 'fr',
                'description': 'Attachée consulaire - Support diplomatique'
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Créer le nouvel utilisateur
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone'],
                password_hash=generate_password_hash(user_data['password']),
                role=user_data['role'],
                language=user_data['language'],
                active=True,
                created_at=datetime.utcnow(),
                last_login=None,
                email_verified=True,  # Pré-vérifiés pour les tests
                mfa_enabled=False     # MFA désactivé pour simplifier les tests
            )
            
            db.session.add(user)
            created_users.append({
                'email': user_data['email'],
                'password': user_data['password'],
                'role': user_data['role'],
                'name': f"{user_data['first_name']} {user_data['last_name']}",
                'description': user_data['description']
            })
            
            print(f"✅ Création: {user_data['email']} ({user_data['role']})")
        
        # Sauvegarder dans la base de données
        db.session.commit()
        
        print("\n" + "="*60)
        print("🎉 UTILISATEURS DE TEST CRÉÉS AVEC SUCCÈS!")
        print("="*60)
        
        # Afficher les informations de connexion par panneau
        print("\n📋 IDENTIFIANTS DE CONNEXION PAR PANNEAU:")
        print("-"*60)
        
        # Panel Citoyens
        print("\n🔵 PANEL CITOYENS (/login)")
        print("="*40)
        for user in created_users:
            if user['role'] == 'usager':
                print(f"👤 {user['name']}")
                print(f"   Email: {user['email']}")
                print(f"   Mot de passe: {user['password']}")
                print(f"   Description: {user['description']}")
                print()
        
        # Panel Administration
        print("🔴 PANEL ADMINISTRATION (/admin)")
        print("="*40)
        for user in created_users:
            if user['role'] in ['superviseur', 'agent']:
                role_name = "Superviseur" if user['role'] == 'superviseur' else "Agent Admin"
                print(f"👨‍💼 {user['name']} - {role_name}")
                print(f"   Email: {user['email']}")
                print(f"   Mot de passe: {user['password']}")
                print(f"   Description: {user['description']}")
                print()
        
        # Panel Consulaire
        print("🟡 PANEL PERSONNEL CONSULAIRE (/consulate)")
        print("="*40)
        consular_users = [u for u in created_users if u['role'] == 'agent' and 'consul' in u['email']]
        for user in consular_users:
            role_name = "Agent Consulaire" if 'consul@' in user['email'] else "Attaché Consulaire"
            print(f"🏛️ {user['name']} - {role_name}")
            print(f"   Email: {user['email']}")
            print(f"   Mot de passe: {user['password']}")
            print(f"   Description: {user['description']}")
            print()
        
        print("="*60)
        print("🚀 L'application e-Consulaire RDC est prête pour les tests!")
        print("   URL de base: http://localhost:5000")
        print("   Portail Citoyens: http://localhost:5000/login")
        print("   Portail Administration: http://localhost:5000/admin")
        print("   Portail Consulaire: http://localhost:5000/consulate")
        print("="*60)
        
        return created_users

if __name__ == '__main__':
    try:
        users = create_test_users()
        print(f"\n✅ Script terminé avec succès! {len(users)} utilisateurs créés.")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création des utilisateurs: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)