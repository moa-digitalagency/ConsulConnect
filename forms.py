from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class RegisterForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Prénom', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Nom', validators=[DataRequired(), Length(max=64)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmer le mot de passe', validators=[DataRequired()])
    language = SelectField('Langue', choices=[('fr', 'Français'), ('en', 'English')], default='fr')
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cette adresse email est déjà utilisée.')
    
    def validate_password2(self, password2):
        if self.password.data != password2.data:
            raise ValidationError('Les mots de passe ne correspondent pas.')

class ConsularCardForm(FlaskForm):
    # Identité
    first_name = StringField('Prénom', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Nom', validators=[DataRequired(), Length(max=64)])
    birth_date = DateField('Date de naissance', validators=[DataRequired()])
    birth_place = StringField('Lieu de naissance', validators=[DataRequired(), Length(max=100)])
    nationality = StringField('Nationalité', validators=[DataRequired(), Length(max=50)])
    
    # Contact
    address = TextAreaField('Adresse', validators=[DataRequired(), Length(max=500)])
    city = StringField('Ville', validators=[DataRequired(), Length(max=100)])
    country = StringField('Pays', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Téléphone', validators=[DataRequired(), Length(max=20)])
    emergency_contact = StringField('Contact d\'urgence', validators=[DataRequired(), Length(max=100)])
    
    # Situation
    profession = StringField('Profession', validators=[DataRequired(), Length(max=100)])
    employer = StringField('Employeur', validators=[Optional(), Length(max=100)])
    
    # Documents
    photo = FileField('Photo d\'identité', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement!')])
    identity_document = FileField('Pièce d\'identité', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images ou PDF uniquement!')])
    proof_of_residence = FileField('Justificatif de domicile', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images ou PDF uniquement!')])
    
    submit = SubmitField('Soumettre la demande')

class CareAttestationForm(FlaskForm):
    # Bénéficiaire
    beneficiary_first_name = StringField('Prénom du bénéficiaire', validators=[DataRequired(), Length(max=64)])
    beneficiary_last_name = StringField('Nom du bénéficiaire', validators=[DataRequired(), Length(max=64)])
    beneficiary_birth_date = DateField('Date de naissance', validators=[DataRequired()])
    beneficiary_nationality = StringField('Nationalité', validators=[DataRequired(), Length(max=50)])
    
    # Garant (utilisateur connecté)
    guarantor_profession = StringField('Votre profession', validators=[DataRequired(), Length(max=100)])
    guarantor_income = FloatField('Vos revenus mensuels (USD)', validators=[DataRequired()])
    
    # Détails de la prise en charge
    purpose = SelectField('Motif', choices=[
        ('visite', 'Visite familiale'),
        ('tourisme', 'Tourisme'),
        ('affaires', 'Affaires'),
        ('medical', 'Médical'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    purpose_other = StringField('Autre motif (précisez)', validators=[Optional(), Length(max=200)])
    duration = StringField('Durée du séjour', validators=[DataRequired(), Length(max=50)])
    relationship = StringField('Lien avec le bénéficiaire', validators=[DataRequired(), Length(max=100)])
    
    # Documents
    guarantor_identity = FileField('Votre pièce d\'identité', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    income_proof = FileField('Justificatif de revenus', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    beneficiary_identity = FileField('Pièce d\'identité du bénéficiaire', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    
    submit = SubmitField('Générer l\'attestation')

class LegalizationsForm(FlaskForm):
    document_type = SelectField('Type de document', choices=[
        ('diplome', 'Diplôme'),
        ('acte_naissance', 'Acte de naissance'),
        ('acte_mariage', 'Acte de mariage'),
        ('casier_judiciaire', 'Casier judiciaire'),
        ('contrat', 'Contrat'),
        ('autre', 'Autre')
    ], validators=[DataRequired()])
    document_type_other = StringField('Autre type (précisez)', validators=[Optional(), Length(max=200)])
    
    quantity = SelectField('Nombre d\'exemplaires', choices=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], default='1', validators=[DataRequired()])
    
    urgency = SelectField('Urgence', choices=[
        ('normal', 'Normal (5-7 jours)'),
        ('urgent', 'Urgent (2-3 jours) - Frais supplémentaires')
    ], default='normal', validators=[DataRequired()])
    
    notes = TextAreaField('Observations particulières', validators=[Optional(), Length(max=500)])
    
    # Appointment
    preferred_date = DateField('Date de rendez-vous souhaitée', validators=[DataRequired()])
    preferred_time = SelectField('Heure préférée', choices=[
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00')
    ], validators=[DataRequired()])
    
    # Documents
    documents = FileField('Documents à légaliser', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    
    submit = SubmitField('Prendre rendez-vous')

class PassportForm(FlaskForm):
    request_type = SelectField('Type de demande', choices=[
        ('premiere', 'Première demande'),
        ('renouvellement', 'Renouvellement'),
        ('perte_vol', 'Perte ou vol')
    ], validators=[DataRequired()])
    
    # Si renouvellement
    old_passport_number = StringField('Numéro de l\'ancien passeport', validators=[Optional(), Length(max=20)])
    
    # Si perte/vol
    loss_declaration = FileField('Déclaration de perte/vol', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    
    # Informations personnelles
    birth_certificate = FileField('Acte de naissance', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    identity_document = FileField('Pièce d\'identité', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    proof_of_residence = FileField('Justificatif de domicile', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    
    # Rendez-vous biométrique
    preferred_date = DateField('Date souhaitée pour la biométrie', validators=[DataRequired()])
    preferred_time = SelectField('Heure préférée', choices=[
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Soumettre la pré-demande')

class OtherDocumentsForm(FlaskForm):
    document_type = SelectField('Type de document', choices=[
        ('attestation_residence', 'Attestation de résidence'),
        ('certificat_vie', 'Certificat de vie'),
        ('attestation_nationalite', 'Attestation de nationalité'),
        ('duplicata_carte', 'Duplicata de carte consulaire'),
        ('autre', 'Autre attestation')
    ], validators=[DataRequired()])
    
    document_type_other = StringField('Autre type (précisez)', validators=[Optional(), Length(max=200)])
    purpose = TextAreaField('Objet/Finalité', validators=[DataRequired(), Length(max=500)])
    
    # Documents justificatifs
    supporting_documents = FileField('Documents justificatifs', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'pdf'])])
    
    submit = SubmitField('Soumettre la demande')

class ApplicationStatusForm(FlaskForm):
    status = SelectField('Statut', choices=[
        ('soumise', 'Soumise'),
        ('en_traitement', 'En traitement'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée')
    ], validators=[DataRequired()])
    
    comment = TextAreaField('Commentaire', validators=[Optional(), Length(max=1000)])
    rejection_reason = TextAreaField('Motif de rejet', validators=[Optional(), Length(max=1000)])
    
    submit = SubmitField('Mettre à jour')
