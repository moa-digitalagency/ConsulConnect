# Service de sécurité avec chiffrement AES-256 et protection anti-attaques
import os
import base64
import hashlib
import hmac
import secrets
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app import app
import re

class SecurityService:
    def __init__(self):
        self.encryption_key = os.environ.get('ENCRYPTION_KEY')
        if not self.encryption_key:
            app.logger.error('ENCRYPTION_KEY non configurée - Génération automatique')
            self.encryption_key = Fernet.generate_key().decode()
            
        self.fernet = self._setup_encryption()
        
    def _setup_encryption(self):
        """Configuration du chiffrement AES-256"""
        try:
            # Dériver une clé Fernet à partir de la clé fournie
            key_bytes = self.encryption_key.encode()[:32].ljust(32, b'\0')
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'e-consulaire-rdc-salt',  # Salt fixe pour reproductibilité
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            return Fernet(key)
        except Exception as e:
            app.logger.error(f'Erreur configuration chiffrement: {e}')
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Chiffrer des données sensibles avec AES-256"""
        if not self.fernet or not data:
            return data
            
        try:
            encrypted = self.fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            app.logger.error(f'Erreur chiffrement: {e}')
            return data
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Déchiffrer des données avec AES-256"""
        if not self.fernet or not encrypted_data:
            return encrypted_data
            
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            app.logger.error(f'Erreur déchiffrement: {e}')
            return encrypted_data
    
    def hash_password_secure(self, password: str) -> str:
        """Hashage sécurisé des mots de passe avec bcrypt"""
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password_secure(self, password: str, hashed: str) -> bool:
        """Vérification sécurisée des mots de passe"""
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    def generate_csrf_token(self) -> str:
        """Générer un token CSRF sécurisé"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Valider un token CSRF"""
        return hmac.compare_digest(token, session_token)
    
    def sanitize_input(self, input_data: str) -> str:
        """Nettoyer les entrées utilisateur pour prévenir XSS"""
        if not input_data:
            return ""
            
        # Supprimer les balises HTML dangereuses
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link', '<meta']
        cleaned = input_data
        
        for tag in dangerous_tags:
            cleaned = re.sub(tag, '&lt;' + tag[1:], cleaned, flags=re.IGNORECASE)
        
        # Échapper les caractères spéciaux
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&#x27;')
        
        return cleaned
    
    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        """Validation sécurisée des fichiers uploadés"""
        result = {
            'valid': False,
            'error': None,
            'safe_filename': None
        }
        
        # Extensions autorisées
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
        
        # Vérifier l'extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            result['error'] = f'Extension {file_ext} non autorisée'
            return result
        
        # Taille max 16MB
        if len(content) > 16 * 1024 * 1024:
            result['error'] = 'Fichier trop volumineux (max 16MB)'
            return result
        
        # Nom de fichier sécurisé
        from werkzeug.utils import secure_filename
        safe_name = secure_filename(filename)
        
        # Ajouter un préfixe unique pour éviter les collisions
        import time
        unique_name = f"{int(time.time())}_{safe_name}"
        
        result.update({
            'valid': True,
            'safe_filename': unique_name
        })
        
        return result
    
    def log_security_event(self, event_type: str, user_id: int = None, details: str = None):
        """Logger les événements de sécurité"""
        from models import AuditLog
        from app import db
        
        AuditLog.log_action(
            user_id=user_id,
            action=f'security_{event_type}',
            table_name='security',
            record_id=None,
            details=details or f'Événement de sécurité: {event_type}'
        )
        
        app.logger.warning(f'SECURITY EVENT: {event_type} - User: {user_id} - {details}')
    
    def rate_limit_check(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Vérification des limites de taux pour prévenir les attaques brute force"""
        import time
        from datetime import datetime, timedelta
        
        # Utiliser un cache simple en mémoire (à remplacer par Redis en production)
        if not hasattr(self, '_rate_limit_cache'):
            self._rate_limit_cache = {}
        
        now = datetime.now()
        key = f"rate_limit_{identifier}"
        
        if key in self._rate_limit_cache:
            attempts = self._rate_limit_cache[key]
            # Nettoyer les tentatives expirées
            cutoff = now - timedelta(minutes=window_minutes)
            attempts = [t for t in attempts if t > cutoff]
            
            if len(attempts) >= max_attempts:
                return False
        else:
            attempts = []
        
        attempts.append(now)
        self._rate_limit_cache[key] = attempts
        return True
    
    def encrypt_file(self, file_path: str) -> bool:
        """Chiffrer un fichier sur le disque"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.fernet.encrypt(data)
            
            with open(file_path + '.enc', 'wb') as f:
                f.write(encrypted_data)
            
            # Supprimer le fichier original
            os.remove(file_path)
            return True
            
        except Exception as e:
            app.logger.error(f'Erreur chiffrement fichier {file_path}: {e}')
            return False
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> bool:
        """Déchiffrer un fichier"""
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
            
        except Exception as e:
            app.logger.error(f'Erreur déchiffrement fichier {encrypted_file_path}: {e}')
            return False

# Instance globale du service de sécurité
security_service = SecurityService()