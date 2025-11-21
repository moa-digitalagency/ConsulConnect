# Service de sauvegarde et restauration automatique pour e-consulaire
import os
import shutil
import subprocess
import json
import zipfile
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app import app, db
from models import AuditLog

class BackupService:
    def __init__(self):
        self.backup_dir = 'backups'
        self.max_backups = 30  # Conserver 30 sauvegardes
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """S'assurer que le répertoire de sauvegarde existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
    def create_full_backup(self, include_files: bool = True) -> Dict[str, any]:
        """Créer une sauvegarde complète du système"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_econsulaire_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        result = {
            'success': False,
            'backup_name': backup_name,
            'backup_path': backup_path,
            'timestamp': timestamp,
            'size_mb': 0,
            'components': {}
        }
        
        try:
            os.makedirs(backup_path)
            
            # 1. Sauvegarde de la base de données
            db_backup = self._backup_database(backup_path)
            result['components']['database'] = db_backup
            
            # 2. Sauvegarde des fichiers uploadés (si demandé)
            if include_files:
                files_backup = self._backup_uploaded_files(backup_path)
                result['components']['files'] = files_backup
            
            # 3. Sauvegarde de la configuration
            config_backup = self._backup_configuration(backup_path)
            result['components']['configuration'] = config_backup
            
            # 4. Sauvegarde des logs critiques
            logs_backup = self._backup_logs(backup_path)
            result['components']['logs'] = logs_backup
            
            # 5. Créer l'archive ZIP
            zip_path = f"{backup_path}.zip"
            self._create_zip_archive(backup_path, zip_path)
            
            # Supprimer le dossier temporaire
            shutil.rmtree(backup_path)
            
            # Calculer la taille
            result['size_mb'] = round(os.path.getsize(zip_path) / (1024 * 1024), 2)
            result['success'] = True
            
            # Logger l'événement
            AuditLog.log_action(
                user_id=None,
                action='system_backup_created',
                table_name='system',
                record_id=None,
                details=f'Sauvegarde créée: {backup_name} ({result["size_mb"]} MB)'
            )
            
            app.logger.info(f'Sauvegarde créée avec succès: {backup_name}')
            
        except Exception as e:
            app.logger.error(f'Erreur lors de la sauvegarde: {e}')
            result['error'] = str(e)
            
            # Nettoyer en cas d'erreur
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
        
        return result
    
    def _backup_database(self, backup_path: str) -> Dict[str, any]:
        """Sauvegarde de la base de données PostgreSQL"""
        result = {'success': False, 'file': None, 'size_mb': 0}
        
        try:
            db_file = os.path.join(backup_path, 'database.sql')
            
            # Utiliser pg_dump pour PostgreSQL
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                cmd = f'pg_dump "{database_url}" > "{db_file}"'
                subprocess.run(cmd, shell=True, check=True)
                
                result['success'] = True
                result['file'] = 'database.sql'
                result['size_mb'] = round(os.path.getsize(db_file) / (1024 * 1024), 2)
            else:
                result['error'] = 'DATABASE_URL non configurée'
                
        except Exception as e:
            result['error'] = str(e)
            app.logger.error(f'Erreur sauvegarde DB: {e}')
        
        return result
    
    def _backup_uploaded_files(self, backup_path: str) -> Dict[str, any]:
        """Sauvegarde des fichiers uploadés"""
        result = {'success': False, 'files_count': 0, 'size_mb': 0}
        
        try:
            uploads_dir = 'uploads'
            if os.path.exists(uploads_dir):
                backup_uploads = os.path.join(backup_path, 'uploads')
                shutil.copytree(uploads_dir, backup_uploads)
                
                # Compter les fichiers et calculer la taille
                files_count = 0
                total_size = 0
                for root, dirs, files in os.walk(backup_uploads):
                    files_count += len(files)
                    for file in files:
                        total_size += os.path.getsize(os.path.join(root, file))
                
                result['success'] = True
                result['files_count'] = files_count
                result['size_mb'] = round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            result['error'] = str(e)
            app.logger.error(f'Erreur sauvegarde fichiers: {e}')
        
        return result
    
    def _backup_configuration(self, backup_path: str) -> Dict[str, any]:
        """Sauvegarde de la configuration système"""
        result = {'success': False, 'files': []}
        
        try:
            config_files = ['app.py', 'models.py', 'requirements.txt', '.replit', 'replit.nix']
            
            for file in config_files:
                if os.path.exists(file):
                    shutil.copy2(file, backup_path)
                    result['files'].append(file)
            
            # Créer un manifest avec les informations système
            manifest = {
                'backup_date': datetime.now().isoformat(),
                'python_version': os.sys.version,
                'environment_vars': {
                    'DATABASE_URL': 'CONFIGURED' if os.environ.get('DATABASE_URL') else 'NOT_SET',
                    'SENDGRID_API_KEY': 'CONFIGURED' if os.environ.get('SENDGRID_API_KEY') else 'NOT_SET',
                    'ENCRYPTION_KEY': 'CONFIGURED' if os.environ.get('ENCRYPTION_KEY') else 'NOT_SET'
                }
            }
            
            with open(os.path.join(backup_path, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            result['success'] = True
            result['files'].append('manifest.json')
            
        except Exception as e:
            result['error'] = str(e)
            app.logger.error(f'Erreur sauvegarde config: {e}')
        
        return result
    
    def _backup_logs(self, backup_path: str) -> Dict[str, any]:
        """Sauvegarde des logs critiques"""
        result = {'success': False, 'files': []}
        
        try:
            # Récupérer les logs d'audit récents (30 derniers jours)
            from models import AuditLog
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_logs = AuditLog.query.filter(
                AuditLog.created_at >= thirty_days_ago
            ).all()
            
            if recent_logs:
                logs_data = []
                for log in recent_logs:
                    logs_data.append({
                        'id': log.id,
                        'user_id': log.user_id,
                        'action': log.action,
                        'table_name': log.table_name,
                        'record_id': log.record_id,
                        'details': log.details,
                        'ip_address': log.ip_address,
                        'user_agent': log.user_agent,
                        'created_at': log.created_at.isoformat() if log.created_at else None
                    })
                
                logs_file = os.path.join(backup_path, 'audit_logs.json')
                with open(logs_file, 'w', encoding='utf-8') as f:
                    json.dump(logs_data, f, indent=2, ensure_ascii=False)
                
                result['success'] = True
                result['files'].append('audit_logs.json')
                result['logs_count'] = len(logs_data)
            
        except Exception as e:
            result['error'] = str(e)
            app.logger.error(f'Erreur sauvegarde logs: {e}')
        
        return result
    
    def _create_zip_archive(self, source_dir: str, zip_path: str):
        """Créer une archive ZIP de la sauvegarde"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arc_name)
    
    def list_backups(self) -> List[Dict[str, any]]:
        """Lister toutes les sauvegardes disponibles"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_econsulaire_') and filename.endswith('.zip'):
                backup_path = os.path.join(self.backup_dir, filename)
                stat = os.stat(backup_path)
                
                # Extraire la date du nom du fichier
                date_str = filename.replace('backup_econsulaire_', '').replace('.zip', '')
                try:
                    backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                except:
                    backup_date = datetime.fromtimestamp(stat.st_mtime)
                
                backups.append({
                    'filename': filename,
                    'path': backup_path,
                    'date': backup_date,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'age_days': (datetime.now() - backup_date).days
                })
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)
    
    def restore_backup(self, backup_filename: str) -> Dict[str, any]:
        """Restaurer une sauvegarde"""
        result = {'success': False, 'restored_components': []}
        
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                result['error'] = 'Sauvegarde non trouvée'
                return result
            
            # Extraire l'archive
            restore_dir = f'restore_temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            # Restaurer la base de données
            db_file = os.path.join(restore_dir, 'database.sql')
            if os.path.exists(db_file):
                database_url = os.environ.get('DATABASE_URL')
                if database_url:
                    cmd = f'psql "{database_url}" < "{db_file}"'
                    subprocess.run(cmd, shell=True, check=True)
                    result['restored_components'].append('database')
            
            # Restaurer les fichiers (optionnel - nécessite confirmation)
            uploads_backup = os.path.join(restore_dir, 'uploads')
            if os.path.exists(uploads_backup):
                if os.path.exists('uploads'):
                    shutil.rmtree('uploads')
                shutil.copytree(uploads_backup, 'uploads')
                result['restored_components'].append('files')
            
            # Nettoyer
            shutil.rmtree(restore_dir)
            
            result['success'] = True
            
            # Logger l'événement
            AuditLog.log_action(
                user_id=None,
                action='system_backup_restored',
                table_name='system',
                record_id=None,
                details=f'Sauvegarde restaurée: {backup_filename}'
            )
            
        except Exception as e:
            result['error'] = str(e)
            app.logger.error(f'Erreur restauration: {e}')
            
            # Nettoyer en cas d'erreur
            if 'restore_dir' in locals() and os.path.exists(restore_dir):
                shutil.rmtree(restore_dir)
        
        return result
    
    def cleanup_old_backups(self):
        """Supprimer les anciennes sauvegardes"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            old_backups = backups[self.max_backups:]
            
            for backup in old_backups:
                try:
                    os.remove(backup['path'])
                    app.logger.info(f'Ancienne sauvegarde supprimée: {backup["filename"]}')
                except Exception as e:
                    app.logger.error(f'Erreur suppression sauvegarde {backup["filename"]}: {e}')
    
    def schedule_automatic_backups(self):
        """Programmer les sauvegardes automatiques"""
        # Sauvegarde quotidienne à 2h du matin
        schedule.every().day.at("02:00").do(self._daily_backup)
        
        # Sauvegarde hebdomadaire complète le dimanche à 3h
        schedule.every().sunday.at("03:00").do(self._weekly_backup)
        
        app.logger.info('Sauvegardes automatiques programmées')
    
    def _daily_backup(self):
        """Sauvegarde quotidienne (base de données seulement)"""
        self.create_full_backup(include_files=False)
        self.cleanup_old_backups()
    
    def _weekly_backup(self):
        """Sauvegarde hebdomadaire complète"""
        self.create_full_backup(include_files=True)
        self.cleanup_old_backups()

# Instance globale du service de sauvegarde
backup_service = BackupService()