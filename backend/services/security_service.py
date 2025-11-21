import os
import base64
import hashlib
import hmac
import secrets
from typing import Optional
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
        try:
            key_bytes = self.encryption_key.encode()[:32].ljust(32, b'\0')
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'e-consulaire-rdc-salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            return Fernet(key)
        except Exception as e:
            app.logger.error(f'Erreur configuration chiffrement: {e}')
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        if not self.fernet or not data:
            return data
        try:
            encrypted = self.fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            app.logger.error(f'Erreur chiffrement: {e}')
            return data
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
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
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password_secure(self, password: str, hashed: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    def generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        return hmac.compare_digest(token, session_token)
    
    def sanitize_input(self, input_data: str) -> str:
        if not input_data:
            return ""
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link', '<meta']
        cleaned = input_data
        for tag in dangerous_tags:
            cleaned = re.sub(tag, '&lt;' + tag[1:], cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&#x27;')
        return cleaned

security_service = SecurityService()
