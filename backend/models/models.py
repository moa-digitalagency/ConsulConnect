from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='usager')
    active = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(2), default='fr')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    photo_url = db.Column(db.String(500))
    genre = db.Column(db.String(10))
    date_naissance = db.Column(db.Date)
    lieu_naissance = db.Column(db.String(100))
    etat_civil = db.Column(db.String(20))
    nationalite = db.Column(db.String(50), default='Congolaise')
    profession = db.Column(db.String(100))
    adresse_rue = db.Column(db.String(200))
    adresse_ville = db.Column(db.String(100))
    adresse_pays = db.Column(db.String(100))
    code_postal = db.Column(db.String(20))
    numero_passeport = db.Column(db.String(50))
    passeport_date_emission = db.Column(db.Date)
    passeport_date_expiration = db.Column(db.Date)
    unite_consulaire_id = db.Column(db.Integer, db.ForeignKey('unite_consulaire.id'), nullable=True)
    profile_complete = db.Column(db.Boolean, default=False)
    applications = db.relationship('Application', foreign_keys='Application.user_id', backref='user', lazy=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role in ['agent', 'superviseur', 'admin']
        
    def is_super_admin(self):
        return self.role == 'superviseur'
    
    def is_supervisor(self):
        return self.role == 'superviseur'
    
    @property
    def is_active(self):
        return self.active

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unite_consulaire_id = db.Column(db.Integer, db.ForeignKey('unite_consulaire.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='soumise')
    form_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    rejection_reason = db.Column(db.Text)
    appointment_date = db.Column(db.DateTime)
    payment_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    documents = db.relationship('Document', backref='application', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('StatusHistory', backref='application', lazy=True, cascade='all, delete-orphan')
    processor = db.relationship('User', foreign_keys=[processed_by], backref='processed_applications')
    unite_consulaire = db.relationship('UniteConsulaire', foreign_keys=[unite_consulaire_id], backref='applications')
    
    def __init__(self, **kwargs):
        super(Application, self).__init__(**kwargs)
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
    
    def generate_reference_number(self):
        import random
        import string
        year = datetime.now().year
        prefix = self.service_type.upper()[:3]
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{year}{suffix}"
    
    def get_status_display(self):
        status_map = {
            'soumise': 'Soumise',
            'en_traitement': 'En traitement',
            'validee': 'Validée',
            'rejetee': 'Rejetée'
        }
        return status_map.get(self.status, self.status)
    
    def get_service_display(self):
        service_map = {
            'carte_consulaire': 'Carte Consulaire',
            'attestation_prise_charge': 'Attestation de Prise en Charge',
            'legalisations': 'Légalisations',
            'passeport': 'Passeport',
            'autres_documents': 'Autres Documents'
        }
        return service_map.get(self.service_type, self.service_type)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    document_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

class StatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[changed_by], backref='status_changes')
    changed_by_user = db.relationship('User', foreign_keys=[changed_by], overlaps="status_changes,user")
    
    @staticmethod
    def get_status_display_map():
        return {
            'soumise': 'Demande Soumise',
            'en_traitement': 'En Cours de Traitement', 
            'validee': 'Demande Approuvée',
            'rejetee': 'Demande Rejetée',
            'documents_requis': 'Documents Supplémentaires Requis',
            'pret_pour_retrait': 'Prêt pour Retrait',
            'cloture': 'Dossier Clôturé'
        }

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id], backref='audit_logs')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')

class UniteConsulaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    pays = db.Column(db.String(100), nullable=False)
    chef_nom = db.Column(db.String(100))
    chef_titre = db.Column(db.String(100))
    email_principal = db.Column(db.String(120), nullable=False)
    email_secondaire = db.Column(db.String(120))
    telephone_principal = db.Column(db.String(20), nullable=False)
    telephone_secondaire = db.Column(db.String(20))
    adresse_rue = db.Column(db.String(200))
    adresse_ville = db.Column(db.String(100))
    adresse_code_postal = db.Column(db.String(20))
    adresse_complement = db.Column(db.String(200))
    adresse_complete = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    code_pays = db.Column(db.String(3))
    timezone = db.Column(db.String(50), default='UTC')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agents = db.relationship('User', foreign_keys='User.unite_consulaire_id', backref='unite_consulaire', lazy=True)
    services_disponibles = db.relationship('UniteConsulaire_Service', backref='unite_consulaire', lazy=True, cascade='all, delete-orphan')
    createur = db.relationship('User', foreign_keys=[created_by], backref='unites_crees')
    
    def __repr__(self):
        return f'<UniteConsulaire {self.nom}>'
    
    def get_agents_count(self):
        return db.session.query(func.count(User.id)).filter(
            User.unite_consulaire_id == self.id, 
            User.role == 'agent'
        ).scalar() or 0
    
    def get_services_actifs(self):
        return db.session.query(UniteConsulaire_Service).filter(
            UniteConsulaire_Service.unite_consulaire_id == self.id,
            UniteConsulaire_Service.actif == True
        ).all()

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    tarif_de_base = db.Column(db.Float, default=0.0)
    documents_requis = db.Column(db.Text)
    delai_traitement = db.Column(db.Integer, default=7)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unites_proposant = db.relationship('UniteConsulaire_Service', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.nom}>'

class UniteConsulaire_Service(db.Model):
    __tablename__ = 'unite_service'
    
    id = db.Column(db.Integer, primary_key=True)
    unite_consulaire_id = db.Column(db.Integer, db.ForeignKey('unite_consulaire.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    tarif_personnalise = db.Column(db.Float, nullable=False)
    devise = db.Column(db.String(3), default='USD')
    actif = db.Column(db.Boolean, default=True)
    configuration = db.Column(db.Text)
    delai_personnalise = db.Column(db.Integer)
    notes_admin = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    configured_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    configurateur = db.relationship('User', foreign_keys=[configured_by], backref='services_configures')
    __table_args__ = (db.UniqueConstraint('unite_consulaire_id', 'service_id', name='uq_unite_service'),)
    
    def get_tarif_avec_devise(self):
        return f"{self.tarif_personnalise} {self.devise}"
