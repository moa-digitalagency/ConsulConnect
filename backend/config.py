import os

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///econsular.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    
    # File uploads
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@diplomatie.gouv.cd')
    
    # Languages
    LANGUAGES = {
        'fr': 'Français',
        'en': 'English'
    }
    
    # Application settings
    ITEMS_PER_PAGE = 20
    
    # Payment settings (for simulation)
    PAYMENT_METHODS = ['card', 'bank_transfer', 'mobile_money']
    
    # Service fees (USD)
    SERVICE_FEES = {
        'carte_consulaire': 50.0,
        'attestation_prise_charge': 25.0,
        'legalisations': 30.0,
        'legalisations_urgent': 50.0,
        'passeport': 100.0,
        'autres_documents': 20.0
    }
