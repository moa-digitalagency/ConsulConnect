# Initialisation des services de sécurité, sauvegarde et mise à jour
from app import app
from security_service import security_service
from backup_service import backup_service
from update_service import update_service
import schedule
import threading
import time

def initialize_security_system():
    """Initialiser tous les systèmes de sécurité"""
    with app.app_context():
        app.logger.info('Initialisation du système de sécurité e-consulaire...')
        
        # 1. Vérifier le chiffrement
        if security_service.fernet:
            app.logger.info('✓ Chiffrement AES-256 initialisé')
        else:
            app.logger.error('✗ Échec initialisation chiffrement')
        
        # 2. Programmer les sauvegardes automatiques
        backup_service.schedule_automatic_backups()
        app.logger.info('✓ Sauvegardes automatiques programmées')
        
        # 3. Programmer les vérifications de mise à jour
        update_service.schedule_automatic_updates(check_frequency_hours=24)
        app.logger.info('✓ Vérifications de mise à jour programmées')
        
        # 4. Démarrer le scheduler en arrière-plan
        start_scheduler()
        app.logger.info('✓ Scheduler automatique démarré')
        
        # 5. Créer la première sauvegarde si nécessaire
        backups = backup_service.list_backups()
        if len(backups) == 0:
            app.logger.info('Création de la première sauvegarde système...')
            result = backup_service.create_full_backup(include_files=True)
            if result['success']:
                app.logger.info('✓ Première sauvegarde créée avec succès')
            else:
                app.logger.warning('⚠ Échec création première sauvegarde')
        
        app.logger.info('Système de sécurité e-consulaire initialisé avec succès')

def start_scheduler():
    """Démarrer le scheduler en arrière-plan"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def create_example_migration():
    """Créer un exemple de migration pour la sécurité"""
    migration_content = '''# Migration: Add encryption support to user data
# Créée le: 2025-09-01

def up(db):
    """Ajouter le support du chiffrement aux données utilisateur"""
    # Ajouter colonne pour les données chiffrées
    db.engine.execute("ALTER TABLE user ADD COLUMN encrypted_data TEXT")
    
    # Créer index pour les recherches sécurisées
    db.engine.execute("CREATE INDEX idx_user_encrypted ON user(encrypted_data)")
    
    # Ajouter table de suivi des clés de chiffrement
    db.engine.execute("""
        CREATE TABLE encryption_keys (
            id SERIAL PRIMARY KEY,
            key_version INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)

def down(db):
    """Supprimer le support du chiffrement"""
    db.engine.execute("DROP TABLE IF EXISTS encryption_keys")
    db.engine.execute("DROP INDEX IF EXISTS idx_user_encrypted")
    db.engine.execute("ALTER TABLE user DROP COLUMN IF EXISTS encrypted_data")
'''
    
    import os
    migrations_dir = 'migrations'
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    example_file = os.path.join(migrations_dir, 'migration_20250901_000001_add_encryption_support.py')
    if not os.path.exists(example_file):
        with open(example_file, 'w') as f:
            f.write(migration_content)
        app.logger.info('Exemple de migration créé: add_encryption_support')

# Initialiser le système au démarrage de l'application
if __name__ == '__main__':
    initialize_security_system()
    create_example_migration()