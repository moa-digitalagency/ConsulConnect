# Service de mise à jour automatique via Git avec migration de base de données
import os
import subprocess
import json
import shutil
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional
from git import Repo, InvalidGitRepositoryError
from app import app, db
from models import AuditLog

class UpdateService:
    def __init__(self):
        self.repo_path = '.'
        self.backup_before_update = True
        self.migration_scripts_dir = 'migrations'
        self.ensure_migration_directory()
        
    def ensure_migration_directory(self):
        """S'assurer que le répertoire de migrations existe"""
        if not os.path.exists(self.migration_scripts_dir):
            os.makedirs(self.migration_scripts_dir)
    
    def check_for_updates(self) -> Dict[str, any]:
        """Vérifier s'il y a des mises à jour disponibles"""
        result = {
            'updates_available': False,
            'current_commit': None,
            'latest_commit': None,
            'commits_behind': 0,
            'changes': []
        }
        
        try:
            # Initialiser ou ouvrir le repository Git
            if os.path.exists('.git'):
                repo = Repo(self.repo_path)
            else:
                app.logger.warning('Repository Git non initialisé')
                return result
            
            # Récupérer les dernières informations du remote
            origin = repo.remotes.origin
            origin.fetch()
            
            # Comparer les commits
            current_commit = repo.head.commit
            remote_commit = origin.refs.main.commit  # ou master selon votre branche
            
            result['current_commit'] = str(current_commit)
            result['latest_commit'] = str(remote_commit)
            
            if current_commit != remote_commit:
                result['updates_available'] = True
                
                # Compter les commits en retard
                commits_behind = list(repo.iter_commits(f'{current_commit}..{remote_commit}'))
                result['commits_behind'] = len(commits_behind)
                
                # Lister les changements
                for commit in commits_behind[:10]:  # Limiter à 10 commits récents
                    result['changes'].append({
                        'hash': str(commit),
                        'message': commit.message.strip(),
                        'author': str(commit.author),
                        'date': commit.committed_datetime.isoformat()
                    })
            
        except Exception as e:
            app.logger.error(f'Erreur vérification mises à jour: {e}')
            result['error'] = str(e)
        
        return result
    
    def perform_update(self, create_backup: bool = True) -> Dict[str, any]:
        """Effectuer la mise à jour du système"""
        result = {
            'success': False,
            'backup_created': False,
            'code_updated': False,
            'database_migrated': False,
            'services_restarted': False,
            'rollback_available': False
        }
        
        try:
            # Étape 1: Créer une sauvegarde avant la mise à jour
            if create_backup:
                from backup_service import backup_service
                backup_result = backup_service.create_full_backup(include_files=True)
                result['backup_created'] = backup_result['success']
                result['rollback_available'] = backup_result['success']
                
                if not backup_result['success']:
                    app.logger.error('Échec de la sauvegarde - Annulation de la mise à jour')
                    result['error'] = 'Sauvegarde échouée'
                    return result
            
            # Étape 2: Récupérer les modifications depuis Git
            repo = Repo(self.repo_path)
            
            # Sauvegarder les fichiers de configuration critiques
            config_backup = self._backup_critical_configs()
            
            # Pull des dernières modifications
            origin = repo.remotes.origin
            pull_result = origin.pull()
            result['code_updated'] = True
            
            # Étape 3: Restaurer les configurations critiques
            self._restore_critical_configs(config_backup)
            
            # Étape 4: Installer les nouvelles dépendances si nécessaire
            self._update_dependencies()
            
            # Étape 5: Exécuter les migrations de base de données
            migration_result = self._run_database_migrations()
            result['database_migrated'] = migration_result['success']
            
            # Étape 6: Redémarrer les services (recharger l'application)
            self._restart_services()
            result['services_restarted'] = True
            
            result['success'] = True
            
            # Logger l'événement
            AuditLog.log_action(
                user_id=None,
                action='system_update_completed',
                table_name='system',
                record_id=None,
                details=f'Mise à jour système effectuée avec succès'
            )
            
            app.logger.info('Mise à jour système réussie')
            
        except Exception as e:
            app.logger.error(f'Erreur lors de la mise à jour: {e}')
            result['error'] = str(e)
            
            # En cas d'erreur, proposer un rollback
            if result['backup_created']:
                result['rollback_suggested'] = True
        
        return result
    
    def _backup_critical_configs(self) -> Dict[str, str]:
        """Sauvegarder les fichiers de configuration critiques"""
        configs = {}
        critical_files = ['.env', 'config.py', 'replit.toml']
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    with open(file, 'r') as f:
                        configs[file] = f.read()
                except Exception as e:
                    app.logger.warning(f'Impossible de sauvegarder {file}: {e}')
        
        return configs
    
    def _restore_critical_configs(self, configs: Dict[str, str]):
        """Restaurer les fichiers de configuration critiques"""
        for file, content in configs.items():
            try:
                with open(file, 'w') as f:
                    f.write(content)
            except Exception as e:
                app.logger.warning(f'Impossible de restaurer {file}: {e}')
    
    def _update_dependencies(self):
        """Mettre à jour les dépendances Python"""
        try:
            # Vérifier si requirements.txt a changé
            if os.path.exists('requirements.txt'):
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                             check=True, capture_output=True)
                app.logger.info('Dépendances mises à jour')
        except subprocess.CalledProcessError as e:
            app.logger.warning(f'Erreur mise à jour dépendances: {e}')
    
    def _run_database_migrations(self) -> Dict[str, any]:
        """Exécuter les migrations de base de données"""
        result = {'success': True, 'migrations_run': []}
        
        try:
            # Rechercher les fichiers de migration non exécutés
            migration_files = self._get_pending_migrations()
            
            for migration_file in migration_files:
                try:
                    # Exécuter chaque migration
                    self._execute_migration(migration_file)
                    result['migrations_run'].append(migration_file)
                    
                    # Marquer la migration comme exécutée
                    self._mark_migration_as_executed(migration_file)
                    
                except Exception as e:
                    app.logger.error(f'Erreur migration {migration_file}: {e}')
                    result['success'] = False
                    result['error'] = f'Migration {migration_file} échouée: {e}'
                    break
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _get_pending_migrations(self) -> List[str]:
        """Récupérer la liste des migrations en attente"""
        pending = []
        
        if not os.path.exists(self.migration_scripts_dir):
            return pending
        
        # Créer la table de suivi des migrations si elle n'existe pas
        self._ensure_migration_table()
        
        # Lister tous les fichiers de migration
        for filename in sorted(os.listdir(self.migration_scripts_dir)):
            if filename.endswith('.py') and filename.startswith('migration_'):
                # Vérifier si la migration a déjà été exécutée
                if not self._is_migration_executed(filename):
                    pending.append(filename)
        
        return pending
    
    def _ensure_migration_table(self):
        """S'assurer que la table de suivi des migrations existe"""
        try:
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db.session.commit()
        except Exception as e:
            app.logger.warning(f'Erreur création table migrations: {e}')
    
    def _is_migration_executed(self, migration_name: str) -> bool:
        """Vérifier si une migration a déjà été exécutée"""
        try:
            result = db.engine.execute(
                'SELECT COUNT(*) FROM schema_migrations WHERE migration_name = %s',
                (migration_name,)
            ).scalar()
            return result > 0
        except:
            return False
    
    def _execute_migration(self, migration_file: str):
        """Exécuter un fichier de migration"""
        migration_path = os.path.join(self.migration_scripts_dir, migration_file)
        
        # Charger et exécuter le module de migration
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Exécuter la fonction up() de la migration
        if hasattr(migration_module, 'up'):
            migration_module.up(db)
            db.session.commit()
        else:
            raise Exception(f'Migration {migration_file} ne contient pas de fonction up()')
    
    def _mark_migration_as_executed(self, migration_name: str):
        """Marquer une migration comme exécutée"""
        try:
            db.engine.execute(
                'INSERT INTO schema_migrations (migration_name) VALUES (%s)',
                (migration_name,)
            )
            db.session.commit()
        except Exception as e:
            app.logger.error(f'Erreur marquage migration {migration_name}: {e}')
    
    def _restart_services(self):
        """Redémarrer les services (recharger l'application)"""
        try:
            # Dans Replit, on peut redémarrer en touchant un fichier
            with open('.reload_trigger', 'w') as f:
                f.write(str(datetime.now()))
            
            app.logger.info('Signal de redémarrage envoyé')
            
        except Exception as e:
            app.logger.warning(f'Impossible de redémarrer automatiquement: {e}')
    
    def create_migration(self, name: str, sql_up: str, sql_down: str = None) -> str:
        """Créer un nouveau fichier de migration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'migration_{timestamp}_{name}.py'
        filepath = os.path.join(self.migration_scripts_dir, filename)
        
        migration_content = f'''# Migration: {name}
# Créée le: {datetime.now().isoformat()}

def up(db):
    """Appliquer la migration"""
    {self._format_sql_for_python(sql_up)}

def down(db):
    """Annuler la migration"""
    {self._format_sql_for_python(sql_down) if sql_down else "pass"}
'''
        
        with open(filepath, 'w') as f:
            f.write(migration_content)
        
        return filename
    
    def _format_sql_for_python(self, sql: str) -> str:
        """Formater le SQL pour inclusion dans un fichier Python"""
        lines = sql.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                formatted_lines.append(f'    db.engine.execute("{line.strip()}")')
        
        return '\n'.join(formatted_lines) if formatted_lines else 'pass'
    
    def rollback_to_backup(self, backup_filename: str) -> Dict[str, any]:
        """Effectuer un rollback vers une sauvegarde"""
        from backup_service import backup_service
        
        app.logger.warning(f'Début du rollback vers: {backup_filename}')
        
        result = backup_service.restore_backup(backup_filename)
        
        if result['success']:
            # Redémarrer les services
            self._restart_services()
            
            # Logger l'événement
            AuditLog.log_action(
                user_id=None,
                action='system_rollback_completed',
                table_name='system',
                record_id=None,
                details=f'Rollback effectué vers: {backup_filename}'
            )
        
        return result
    
    def schedule_automatic_updates(self, check_frequency_hours: int = 24):
        """Programmer les vérifications automatiques de mise à jour"""
        import schedule
        
        schedule.every(check_frequency_hours).hours.do(self._check_and_notify_updates)
        
        app.logger.info(f'Vérifications automatiques programmées toutes les {check_frequency_hours}h')
    
    def _check_and_notify_updates(self):
        """Vérifier les mises à jour et notifier les administrateurs"""
        updates = self.check_for_updates()
        
        if updates['updates_available']:
            # Notifier les superviseurs qu'une mise à jour est disponible
            from models import User, Notification
            superviseurs = User.query.filter_by(role='superviseur', active=True).all()
            
            for superviseur in superviseurs:
                notification = Notification(
                    user_id=superviseur.id,
                    type_notification='system_update',
                    title='Mise à jour système disponible',
                    message=f'{updates["commits_behind"]} nouveaux commits disponibles',
                    reference_id=None
                )
                db.session.add(notification)
            
            db.session.commit()

# Instance globale du service de mise à jour
update_service = UpdateService()