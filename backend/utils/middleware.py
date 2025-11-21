# Middleware de sécurité pour Flask e-consulaire
from flask import request, session, abort, g
from functools import wraps
import time
from backend.services.security_service import security_service
from app import app

# Cache pour le rate limiting
rate_limit_cache = {}

def security_middleware():
    """Middleware principal de sécurité"""
    # 1. Protection CSRF pour les requêtes POST/PUT/DELETE
    if request.method in ['POST', 'PUT', 'DELETE']:
        if not validate_csrf_token():
            app.logger.warning(f'Tentative CSRF détectée depuis {request.remote_addr}')
            security_service.log_security_event('csrf_attempt', None, f'IP: {request.remote_addr}')
            abort(403)
    
    # 2. Rate limiting
    client_ip = request.remote_addr
    if not rate_limit_check(client_ip):
        app.logger.warning(f'Rate limit dépassé pour {client_ip}')
        security_service.log_security_event('rate_limit_exceeded', None, f'IP: {client_ip}')
        abort(429)  # Too Many Requests
    
    # 3. Validation des en-têtes de sécurité
    add_security_headers()
    
    # 4. Nettoyage automatique des données d'entrée
    sanitize_request_data()

def validate_csrf_token():
    """Valider le token CSRF"""
    if request.is_json:
        token = request.headers.get('X-CSRFToken')
    else:
        token = request.form.get('csrf_token')
    
    session_token = session.get('csrf_token')
    
    if not token or not session_token:
        return False
    
    return security_service.validate_csrf_token(token, session_token)

def rate_limit_check(identifier, max_requests=100, window_seconds=3600):
    """Vérification simple du rate limiting"""
    now = time.time()
    window_start = now - window_seconds
    
    if identifier not in rate_limit_cache:
        rate_limit_cache[identifier] = []
    
    # Nettoyer les anciennes requêtes
    rate_limit_cache[identifier] = [
        req_time for req_time in rate_limit_cache[identifier] 
        if req_time > window_start
    ]
    
    # Vérifier la limite
    if len(rate_limit_cache[identifier]) >= max_requests:
        return False
    
    # Ajouter la requête actuelle
    rate_limit_cache[identifier].append(now)
    return True

def add_security_headers():
    """Ajouter des en-têtes de sécurité"""
    @app.after_request
    def set_security_headers(response):
        # Protection XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS stricte (en production)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Politique de contenu sécurisée
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "font-src 'self' cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
        )
        
        return response

def sanitize_request_data():
    """Nettoyer automatiquement les données d'entrée"""
    if request.is_json:
        # Nettoyer les données JSON
        if hasattr(request, 'json') and request.json:
            sanitized_data = {}
            for key, value in request.json.items():
                if isinstance(value, str):
                    sanitized_data[key] = security_service.sanitize_input(value)
                else:
                    sanitized_data[key] = value
            # Remplacer les données dans la requête
            request.json = sanitized_data
    
    elif request.form:
        # Nettoyer les données de formulaire
        sanitized_form = {}
        for key, value in request.form.items():
            if isinstance(value, str):
                sanitized_form[key] = security_service.sanitize_input(value)
            else:
                sanitized_form[key] = value
        # Remplacer les données dans la requête
        request.form = sanitized_form

def require_2fa(f):
    """Décorateur pour exiger l'authentification à deux facteurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # Vérifier si l'utilisateur a activé 2FA (à implémenter)
        if hasattr(current_user, 'two_factor_enabled') and current_user.two_factor_enabled:
            if not session.get('2fa_verified'):
                return redirect(url_for('verify_2fa'))
        
        return f(*args, **kwargs)
    return decorated_function

def log_suspicious_activity():
    """Logger automatiquement les activités suspectes"""
    @app.before_request
    def check_suspicious_patterns():
        suspicious_patterns = [
            'union select',  # Injection SQL
            '<script',       # XSS
            'javascript:',   # XSS
            '../',          # Directory traversal
            'eval(',        # Code injection
            'system(',      # Command injection
        ]
        
        # Vérifier l'URL
        for pattern in suspicious_patterns:
            if pattern.lower() in request.url.lower():
                security_service.log_security_event(
                    'suspicious_url',
                    None,
                    f'Pattern suspect dans URL: {pattern} - IP: {request.remote_addr}'
                )
        
        # Vérifier les paramètres
        if request.args:
            for key, value in request.args.items():
                for pattern in suspicious_patterns:
                    if pattern.lower() in str(value).lower():
                        security_service.log_security_event(
                            'suspicious_parameter',
                            None,
                            f'Pattern suspect dans paramètre {key}: {pattern} - IP: {request.remote_addr}'
                        )

# Initialiser le middleware
def init_security_middleware(app):
    """Initialiser tous les middleware de sécurité"""
    app.before_request(security_middleware)
    add_security_headers()
    log_suspicious_activity()
    
    # Générer un token CSRF pour chaque session
    @app.before_request
    def generate_csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = security_service.generate_csrf_token()
    
    # Rendre le token CSRF disponible dans tous les templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=session.get('csrf_token'))
    
    app.logger.info('Middleware de sécurité initialisé')