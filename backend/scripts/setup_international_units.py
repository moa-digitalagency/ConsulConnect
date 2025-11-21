#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

"""
Script simple pour ajouter les unités consulaires internationales et leurs configurations
"""

from app import app, db
from models import User, UniteConsulaire, Service, UniteConsulaire_Service
import json

def setup_international_units():
    """Créer les unités consulaires internationales avec les utilisateurs existants"""
    
    with app.app_context():
        print("🌍 Configuration des unités consulaires internationales...")
        
        # Utiliser l'admin existant
        admin = User.query.filter_by(email='admin@diplomatie.gouv.cd').first()
        if not admin:
            print("❌ Admin non trouvé, veuillez d'abord créer un admin")
            return
            
        print(f"✅ Admin trouvé: {admin.username} ({admin.role})")
        
        # Créer les unités internationales si elles n'existent pas
        units_to_create = [
            {
                'nom': 'Ambassade de la RD Congo au Maroc',
                'type': 'ambassade',
                'ville': 'Rabat',
                'pays': 'Maroc',
                'code_pays': 'MAR',
                'adresse_complete': 'Avenue Mehdi Ben Barka, Souissi, Rabat 10170, Maroc',
                'telephone': '+212 5 37-75-47-64',
                'email': 'info@amb-rdc-rabat.org',
                'timezone': 'Africa/Casablanca'
            },
            {
                'nom': 'Ambassade de la RD Congo en France', 
                'type': 'ambassade',
                'ville': 'Paris',
                'pays': 'France',
                'code_pays': 'FRA',
                'adresse_complete': '32 cours Albert 1er, 75008 Paris, France',
                'telephone': '+33 1-42-25-57-50',
                'email': 'info@amb-rdc-paris.org',
                'timezone': 'Europe/Paris'
            },
            {
                'nom': 'Consulat Général de la RD Congo à Bruxelles',
                'type': 'consulat', 
                'ville': 'Bruxelles',
                'pays': 'Belgique',
                'code_pays': 'BEL',
                'adresse_complete': 'Avenue de Tervuren 4, 1040 Bruxelles, Belgique',
                'telephone': '+32 2-743-96-60',
                'email': 'info@consulat-rdc-bruxelles.be',
                'timezone': 'Europe/Brussels'
            }
        ]
        
        created_units = []
        
        for unit_data in units_to_create:
            # Vérifier si l'unité existe déjà
            existing_unit = UniteConsulaire.query.filter_by(
                ville=unit_data['ville'], 
                pays=unit_data['pays']
            ).first()
            
            if not existing_unit:
                new_unit = UniteConsulaire(
                    nom=unit_data['nom'],
                    type=unit_data['type'],
                    ville=unit_data['ville'],
                    pays=unit_data['pays'],
                    code_pays=unit_data['code_pays'],
                    adresse_complete=unit_data['adresse_complete'],
                    telephone=unit_data['telephone'],
                    email=unit_data['email'],
                    timezone=unit_data['timezone'],
                    created_by=admin.id,
                    active=True
                )
                db.session.add(new_unit)
                created_units.append(new_unit)
                print(f"✅ Créé: {unit_data['nom']}")
            else:
                created_units.append(existing_unit)
                print(f"ℹ️  Existe déjà: {unit_data['nom']}")
        
        db.session.commit()
        
        # Configurer quelques services pour ces unités
        configure_services_for_units(created_units, admin)
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("🏛️  UNITÉS CONSULAIRES INTERNATIONALES")
        print("="*60)
        
        all_units = UniteConsulaire.query.all()
        for unit in all_units:
            services_count = len(unit.get_services_actifs())
            print(f"• {unit.nom} ({unit.ville}, {unit.pays})")
            print(f"  Services configurés: {services_count}")
        
        print(f"\n📊 Total: {len(all_units)} unités consulaires")
        print("✅ Configuration terminée!")

def configure_services_for_units(units, configurator):
    """Configurer des services de base pour les nouvelles unités"""
    
    services = Service.query.all()
    
    # Configuration différente par unité
    configurations = {
        'Rabat': [
            ('carte_consulaire', 45.0),
            ('attestation_prise_charge', 20.0),
            ('legalisations', 25.0),
            ('passeport', 95.0),
        ],
        'Paris': [
            ('carte_consulaire', 50.0),
            ('attestation_prise_charge', 25.0),
            ('legalisations', 35.0),
            ('passeport', 100.0),
            ('autres_documents', 20.0),
        ],
        'Bruxelles': [
            ('carte_consulaire', 55.0),
            ('legalisations', 40.0),
            ('passeport', 110.0),
            ('etat_civil', 40.0),
        ]
    }
    
    for unit in units:
        if unit.ville in configurations:
            for service_code, tarif in configurations[unit.ville]:
                # Trouver le service
                service = next((s for s in services if s.code == service_code), None)
                if service:
                    # Vérifier si la configuration existe déjà
                    existing = UniteConsulaire_Service.query.filter_by(
                        unite_consulaire_id=unit.id,
                        service_id=service.id
                    ).first()
                    
                    if not existing:
                        config = UniteConsulaire_Service(
                            unite_consulaire_id=unit.id,
                            service_id=service.id,
                            tarif_personnalise=tarif,
                            actif=True,
                            configured_by=configurator.id,
                            configuration=json.dumps({
                                'delai_specifique': service.delai_traitement,
                                'notes': f'Configuré pour {unit.ville}',
                                'devise': 'USD'
                            })
                        )
                        db.session.add(config)
            
            print(f"✅ Services configurés pour {unit.ville}")
    
    db.session.commit()

if __name__ == '__main__':
    setup_international_units()