import os
import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, send_file, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import app, db, mail
from backend.models import User, Application, Document, StatusHistory, AuditLog, Notification, UniteConsulaire, Service, UniteConsulaire_Service
from backend.services import NotificationService, email_service
from sqlalchemy import func
from backend.forms import (LoginForm, RegisterForm, ConsularCardForm, CareAttestationForm, 
                   LegalizationsForm, PassportForm, OtherDocumentsForm, ApplicationStatusForm,
                   EmergencyPassForm, CivilStatusForm, PowerAttorneyForm)
from backend.utils import generate_pdf_document, send_notification_email, log_audit

# Redirect root to user login by default
@app.route('/')
def index():
    return redirect(url_for('auth.user_login'))

# Create auth blueprint for better organization
from flask import Blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        if current_user.role == 'usager':
            return redirect(url_for('user_dashboard'))
        # Rediriger selon le rôle spécifique
        if current_user.role == 'superviseur':
            return redirect('/superviseur/dashboard')
        elif current_user.role == 'admin':
            return redirect('/admin/hierarchy') 
        elif current_user.role == 'agent':
            return redirect('/agent/my-unit')
        return redirect('/admin/hierarchy')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.active and user.role == 'usager':
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_audit(user.id, 'login', 'user', user.id, 'User logged in')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Accès non autorisé pour ce type de compte.', 'error')
        else:
            flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('auth/user_login.html', form=form)

@auth.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        # Rediriger selon le rôle spécifique
        if current_user.role == 'superviseur':
            return redirect('/superviseur/dashboard')
        elif current_user.role == 'admin':
            return redirect('/admin/hierarchy') 
        elif current_user.role == 'agent':
            return redirect('/agent/my-unit')
        return redirect(url_for('user_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.active and user.role in ['admin', 'agent', 'superviseur']:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_audit(user.id, 'admin_login', 'user', user.id, 'Admin logged in')
                
                # Rediriger selon le rôle spécifique
                if user.role == 'superviseur':
                    return redirect('/superviseur/dashboard')
                elif user.role == 'admin':
                    return redirect('/admin/hierarchy') 
                elif user.role == 'agent':
                    return redirect('/agent/my-unit')
                    
            else:
                flash('Accès administrateur non autorisé.', 'error')
        else:
            flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('auth/admin_login.html', form=form)

@auth.route('/consulate', methods=['GET', 'POST'])
def consulate_login():
    if current_user.is_authenticated:
        if current_user.role == 'agent':
            return redirect(url_for('consulate_dashboard'))
        return redirect('/admin/hierarchy')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.active and user.role == 'agent':
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                log_audit(user.id, 'consulate_login', 'user', user.id, 'Consulate staff logged in')
                return redirect(url_for('consulate_dashboard'))
            else:
                flash('Accès consulaire non autorisé.', 'error')
        else:
            flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('auth/consulate_login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.password_hash = generate_password_hash(form.password.data)
        user.language = form.language.data
        user.role = 'usager'  # Default role for new users
        
        db.session.add(user)
        db.session.commit()
        
        log_audit(None, 'register', 'user', user.id, f'New user registered: {user.email}')
        
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.user_login'))
    
    return render_template('auth/register.html', form=form)

# Register the auth blueprint
app.register_blueprint(auth)

# Import superviseur routes
from backend.routes import routes_superviseur

# Import admin routes  
from backend.routes import routes_admin

# Import agent routes
from backend.routes import routes_agent

# Route publique pour le suivi de demande
@app.route('/track', methods=['GET', 'POST'])
def track_application():
    """Suivi de demande par numéro de référence (accessible sans connexion)"""
    application = None
    status_history = None
    
    if request.method == 'POST':
        reference_number = request.form.get('reference_number', '').strip()
        if reference_number:
            # Rechercher l'application par numéro de référence
            application = Application.query.filter_by(reference_number=reference_number).first()
            
            if application:
                # Récupérer l'historique des statuts
                status_history = StatusHistory.query.filter_by(
                    application_id=application.id
                ).order_by(StatusHistory.timestamp.desc()).all()
    
    return render_template('public/track_application.html', 
                         application=application,
                         status_history=status_history)

@app.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'logout', 'user', current_user.id, 'User logged out')
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/user-dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'usager':
        if current_user.role in ['admin', 'agent', 'superviseur']:
            return redirect('/admin/hierarchy')
        abort(403)
    
    # Check if profile is complete
    if not current_user.profile_complete:
        flash('Veuillez compléter votre profil pour accéder à tous les services.', 'info')
    
    # User dashboard
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/user.html', applications=applications, notifications=notifications)

@app.route('/admin-dashboard')
@login_required
def admin_dashboard_legacy():
    if not current_user.is_admin():
        abort(403)
    
    # Statistics for admin dashboard
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='soumise').count()
    processing_applications = Application.query.filter_by(status='en_traitement').count()
    approved_applications = Application.query.filter_by(status='validee').count()
    rejected_applications = Application.query.filter_by(status='rejetee').count()
    
    # Recent applications
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
    
    # Consular units stats
    total_units = UniteConsulaire.query.count()
    total_services = Service.query.count()
    
    return render_template('dashboard/admin_simple.html', 
                         total_applications=total_applications,
                         pending_applications=pending_applications,
                         processing_applications=processing_applications,
                         approved_applications=approved_applications,
                         rejected_applications=rejected_applications,
                         recent_applications=recent_applications,
                         total_units=total_units,
                         total_services=total_services)

@app.route('/admin')
@login_required
def admin_dashboard_redirect():
    """Redirect from /admin to admin_dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
@login_required
def admin_users_page():
    if not current_user.is_admin():
        abort(403)
    
    users = User.query.all()
    return render_template('dashboard/admin_users.html', users=users)

@app.route('/admin/config')
@login_required
def admin_config_page():
    if not current_user.is_admin():
        abort(403)
    
    return render_template('dashboard/admin_config.html')

@app.route('/consulate-dashboard')
@login_required  
def consulate_dashboard():
    if current_user.role != 'agent':
        abort(403)
    
    # Statistics
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='soumise').count()
    processing_applications = Application.query.filter_by(status='en_traitement').count()
    approved_applications = Application.query.filter_by(status='validee').count()
    rejected_applications = Application.query.filter_by(status='rejetee').count()
    
    # Recent applications
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
    
    return render_template('dashboard/admin.html', 
                         total_applications=total_applications,
                         pending_applications=pending_applications,
                         processing_applications=processing_applications,
                         approved_applications=approved_applications,
                         rejected_applications=rejected_applications,
                         recent_applications=recent_applications)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.role != 'usager':
        abort(403)
    
    if request.method == 'POST':
        # Update profile
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.middle_name = request.form.get('middle_name')
        current_user.phone = request.form.get('phone')
        current_user.genre = request.form.get('genre')
        current_user.lieu_naissance = request.form.get('lieu_naissance')
        current_user.etat_civil = request.form.get('etat_civil')
        current_user.profession = request.form.get('profession')
        current_user.adresse_rue = request.form.get('adresse_rue')
        current_user.adresse_ville = request.form.get('adresse_ville')
        current_user.adresse_pays = request.form.get('adresse_pays')
        current_user.code_postal = request.form.get('code_postal')
        current_user.numero_passeport = request.form.get('numero_passeport')
        current_user.ambassade_ville = request.form.get('ambassade_ville')
        current_user.ambassade_pays = request.form.get('ambassade_pays')
        
        # Parse dates
        date_naissance = request.form.get('date_naissance')
        if date_naissance:
            from datetime import datetime
            current_user.date_naissance = datetime.strptime(date_naissance, '%Y-%m-%d').date()
        
        # Check if profile is complete
        required_fields = [
            current_user.first_name, current_user.last_name, current_user.genre,
            current_user.date_naissance, current_user.lieu_naissance,
            current_user.adresse_ville, current_user.adresse_pays
        ]
        current_user.profile_complete = all(required_fields)
        
        db.session.commit()
        flash('Votre profil a été mis à jour avec succès.', 'success')
        return redirect(url_for('user_profile'))
    
    return render_template('profile/user_profile.html')

@app.route('/services/consular-card', methods=['GET', 'POST'])
@login_required
def consular_card():
    form = ConsularCardForm()
    if form.validate_on_submit():
        # Create application
        application = Application(
            user_id=current_user.id,
            service_type='carte_consulaire',
            form_data=json.dumps({
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'birth_date': form.birth_date.data.isoformat(),
                'birth_place': form.birth_place.data,
                'nationality': form.nationality.data,
                'address': form.address.data,
                'city': form.city.data,
                'country': form.country.data,
                'phone': form.phone.data,
                'emergency_contact': form.emergency_contact.data,
                'profession': form.profession.data,
                'employer': form.employer.data
            }),
            payment_amount=50.0  # Example fee
        )
        db.session.add(application)
        db.session.flush()  # Get the ID
        
        # Save uploaded files
        file_fields = [
            ('photo', form.photo.data),
            ('identity_document', form.identity_document.data),
            ('proof_of_residence', form.proof_of_residence.data)
        ]
        
        for doc_type, file in file_fields:
            if file:
                filename = secure_filename(file.filename)
                unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                document = Document(
                    application_id=application.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    document_type=doc_type
                )
                db.session.add(document)
        
        # Add status history
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id,
            comment='Demande soumise par l\'utilisateur'
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        # Déclencher les notifications pour les agents de l'unité consulaire
        NotificationService.notify_new_application(application)
        
        log_audit(current_user.id, 'create_application', 'application', application.id, 'Consular card application submitted')
        
        # Send notification email
        send_notification_email(current_user.email, 
                               'Demande de carte consulaire soumise',
                               f'Votre demande de carte consulaire (réf: {application.reference_number}) a été soumise avec succès.')
        
        flash(f'Votre demande a été soumise avec succès. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/consular_card_corporate.html', form=form)



@app.route('/services/care-attestation', methods=['GET', 'POST'])
@login_required
def care_attestation():
    form = CareAttestationForm()
    if form.validate_on_submit():
        application = Application(
            user_id=current_user.id,
            service_type='attestation_prise_charge',
            form_data=json.dumps({
                'beneficiary_first_name': form.beneficiary_first_name.data,
                'beneficiary_last_name': form.beneficiary_last_name.data,
                'beneficiary_birth_date': form.beneficiary_birth_date.data.isoformat(),
                'beneficiary_nationality': form.beneficiary_nationality.data,
                'guarantor_profession': form.guarantor_profession.data,
                'guarantor_income': form.guarantor_income.data,
                'purpose': form.purpose.data,
                'purpose_other': form.purpose_other.data,
                'duration': form.duration.data,
                'relationship': form.relationship.data
            }),
            payment_amount=25.0
        )
        db.session.add(application)
        db.session.flush()
        
        # Save documents
        file_fields = [
            ('guarantor_identity', form.guarantor_identity.data),
            ('income_proof', form.income_proof.data),
            ('beneficiary_identity', form.beneficiary_identity.data)
        ]
        
        for doc_type, file in file_fields:
            if file:
                filename = secure_filename(file.filename)
                unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                document = Document(
                    application_id=application.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    document_type=doc_type
                )
                db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        log_audit(current_user.id, 'create_application', 'application', application.id, 'Care attestation application submitted')
        
        flash(f'Votre demande a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/care_attestation_corporate.html', form=form)

@app.route('/services/legalizations', methods=['GET', 'POST'])
@login_required
def legalizations():
    form = LegalizationsForm()
    if form.validate_on_submit():
        application = Application(
            user_id=current_user.id,
            service_type='legalisations',
            form_data=json.dumps({
                'document_type': form.document_type.data,
                'document_type_other': form.document_type_other.data,
                'quantity': form.quantity.data,
                'urgency': form.urgency.data,
                'notes': form.notes.data,
                'preferred_date': form.preferred_date.data.isoformat(),
                'preferred_time': form.preferred_time.data
            }),
            payment_amount=30.0 if form.urgency.data == 'normal' else 50.0,
            appointment_date=datetime.combine(form.preferred_date.data, datetime.strptime(form.preferred_time.data, '%H:%M').time())
        )
        db.session.add(application)
        db.session.flush()
        
        # Save documents
        if form.documents.data:
            file = form.documents.data
            filename = secure_filename(file.filename)
            unique_filename = f"{application.id}_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            document = Document(
                application_id=application.id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                document_type='documents'
            )
            db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        log_audit(current_user.id, 'create_application', 'application', application.id, 'Legalizations application submitted')
        
        flash(f'Votre rendez-vous a été pris. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/legalizations_corporate.html', form=form)

@app.route('/services/passport', methods=['GET', 'POST'])
@login_required
def passport():
    form = PassportForm()
    if form.validate_on_submit():
        application = Application(
            user_id=current_user.id,
            service_type='passeport',
            form_data=json.dumps({
                'request_type': form.request_type.data,
                'old_passport_number': form.old_passport_number.data,
                'preferred_date': form.preferred_date.data.isoformat(),
                'preferred_time': form.preferred_time.data
            }),
            payment_amount=100.0,
            appointment_date=datetime.combine(form.preferred_date.data, datetime.strptime(form.preferred_time.data, '%H:%M').time())
        )
        db.session.add(application)
        db.session.flush()
        
        # Save documents
        file_fields = [
            ('birth_certificate', form.birth_certificate.data),
            ('identity_document', form.identity_document.data),
            ('proof_of_residence', form.proof_of_residence.data)
        ]
        
        if form.loss_declaration.data:
            file_fields.append(('loss_declaration', form.loss_declaration.data))
        
        for doc_type, file in file_fields:
            if file:
                filename = secure_filename(file.filename)
                unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                document = Document(
                    application_id=application.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    document_type=doc_type
                )
                db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        log_audit(current_user.id, 'create_application', 'application', application.id, 'Passport application submitted')
        
        flash(f'Votre pré-demande a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/passport_corporate.html', form=form)

@app.route('/services/other-documents', methods=['GET', 'POST'])
@login_required
def other_documents():
    form = OtherDocumentsForm()
    if form.validate_on_submit():
        application = Application(
            user_id=current_user.id,
            service_type='autres_documents',
            form_data=json.dumps({
                'document_type': form.document_type.data,
                'document_type_other': form.document_type_other.data,
                'purpose': form.purpose.data
            }),
            payment_amount=20.0
        )
        db.session.add(application)
        db.session.flush()
        
        # Save documents
        if form.supporting_documents.data:
            file = form.supporting_documents.data
            filename = secure_filename(file.filename)
            unique_filename = f"{application.id}_supporting_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            document = Document(
                application_id=application.id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                document_type='supporting'
            )
            db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        log_audit(current_user.id, 'create_application', 'application', application.id, 'Other documents application submitted')
        
        flash(f'Votre demande a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/other_documents_corporate.html', form=form)

@app.route('/services/emergency-pass', methods=['GET', 'POST'])
@login_required
def emergency_pass():
    form = EmergencyPassForm()
    if form.validate_on_submit():
        # Create application
        application = Application(
            user_id=current_user.id,
            service_type='laissez_passer',
            form_data=json.dumps({
                'emergency_reason': request.form.get('emergency_reason'),
                'emergency_description': request.form.get('emergency_description'),
                'travel_date': request.form.get('travel_date'),
                'emergency_phone': request.form.get('emergency_phone'),
                'emergency_email': request.form.get('emergency_email')
            }),
            payment_amount=75.0,  # Emergency fee
            status='urgent'
        )
        db.session.add(application)
        db.session.flush()
        
        # Save uploaded files with simplified handling
        files_to_save = [
            ('photo', request.files.get('photo')),
            ('identity_document', request.files.get('identity_document')),
            ('emergency_proof', request.files.getlist('emergency_proof'))
        ]
        
        for doc_type, file_data in files_to_save:
            if file_data:
                if isinstance(file_data, list):
                    for i, file in enumerate(file_data):
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{application.id}_{doc_type}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            file.save(file_path)
                            
                            document = Document(
                                application_id=application.id,
                                filename=unique_filename,
                                original_filename=filename,
                                file_path=file_path,
                                file_size=os.path.getsize(file_path),
                                document_type=f"{doc_type}_{i}"
                            )
                            db.session.add(document)
                else:
                    if file_data.filename:
                        filename = secure_filename(file_data.filename)
                        unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file_data.save(file_path)
                        
                        document = Document(
                            application_id=application.id,
                            filename=unique_filename,
                            original_filename=filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            document_type=doc_type
                        )
                        db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='urgent',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        flash(f'Votre demande d\'urgence a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/emergency_pass_corporate.html', form=form)

@app.route('/services/civil-status', methods=['GET', 'POST'])
@login_required
def civil_status():
    form = CivilStatusForm()
    if form.validate_on_submit():
        # Create application
        application = Application(
            user_id=current_user.id,
            service_type='etat_civil',
            form_data=json.dumps({
                'document_type': request.form.get('document_type'),
                'relationship': request.form.get('relationship'),
                'subject_name': request.form.get('subject_name'),
                'event_date': request.form.get('event_date'),
                'event_place': request.form.get('event_place'),
                'copies_count': request.form.get('copies_count')
            }),
            payment_amount=35.0
        )
        db.session.add(application)
        db.session.flush()
        
        # Save uploaded files
        files_to_save = [
            ('identity_document', request.files.get('identity_document')),
            ('relationship_proof', request.files.get('relationship_proof')),
            ('reference_documents', request.files.getlist('reference_documents'))
        ]
        
        for doc_type, file_data in files_to_save:
            if file_data:
                if isinstance(file_data, list):
                    for i, file in enumerate(file_data):
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{application.id}_{doc_type}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            file.save(file_path)
                            
                            document = Document(
                                application_id=application.id,
                                filename=unique_filename,
                                original_filename=filename,
                                file_path=file_path,
                                file_size=os.path.getsize(file_path),
                                document_type=f"{doc_type}_{i}"
                            )
                            db.session.add(document)
                else:
                    if file_data.filename:
                        filename = secure_filename(file_data.filename)
                        unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file_data.save(file_path)
                        
                        document = Document(
                            application_id=application.id,
                            filename=unique_filename,
                            original_filename=filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            document_type=doc_type
                        )
                        db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        flash(f'Votre demande d\'état civil a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/civil_status_corporate.html', form=form)

@app.route('/services/power-attorney', methods=['GET', 'POST'])
@login_required
def power_attorney():
    form = PowerAttorneyForm()
    if form.validate_on_submit():
        # Create application
        application = Application(
            user_id=current_user.id,
            service_type='procuration',
            form_data=json.dumps({
                'power_type': request.form.get('power_type'),
                'agent_name': request.form.get('agent_name'),
                'agent_birth_date': request.form.get('agent_birth_date'),
                'agent_address': request.form.get('agent_address'),
                'agent_profession': request.form.get('agent_profession'),
                'agent_phone': request.form.get('agent_phone'),
                'agent_email': request.form.get('agent_email'),
                'powers_description': request.form.get('powers_description'),
                'validity_duration': request.form.get('validity_duration')
            }),
            payment_amount=40.0
        )
        db.session.add(application)
        db.session.flush()
        
        # Save uploaded files
        files_to_save = [
            ('mandant_identity', request.files.get('mandant_identity')),
            ('agent_identity', request.files.get('agent_identity')),
            ('supporting_documents', request.files.getlist('supporting_documents'))
        ]
        
        for doc_type, file_data in files_to_save:
            if file_data:
                if isinstance(file_data, list):
                    for i, file in enumerate(file_data):
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{application.id}_{doc_type}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            file.save(file_path)
                            
                            document = Document(
                                application_id=application.id,
                                filename=unique_filename,
                                original_filename=filename,
                                file_path=file_path,
                                file_size=os.path.getsize(file_path),
                                document_type=f"{doc_type}_{i}"
                            )
                            db.session.add(document)
                else:
                    if file_data.filename:
                        filename = secure_filename(file_data.filename)
                        unique_filename = f"{application.id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file_data.save(file_path)
                        
                        document = Document(
                            application_id=application.id,
                            filename=unique_filename,
                            original_filename=filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            document_type=doc_type
                        )
                        db.session.add(document)
        
        status_history = StatusHistory(
            application_id=application.id,
            new_status='soumise',
            changed_by=current_user.id
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        flash(f'Votre demande de procuration a été soumise. Référence: {application.reference_number}', 'success')
        return redirect(url_for('view_application', id=application.id))
    
    return render_template('services/power_attorney_corporate.html', form=form)

@app.route('/application/<int:id>')
@login_required
def view_application(id):
    application = Application.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and application.user_id != current_user.id:
        abort(403)
    
    form_data = json.loads(application.form_data) if application.form_data else {}
    
    return render_template('applications/view.html', application=application, form_data=form_data)

@app.route('/applications')
@login_required
def list_applications():
    if current_user.is_admin():
        applications = Application.query.order_by(Application.created_at.desc()).all()
    else:
        applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    
    return render_template('applications/list.html', applications=applications)

@app.route('/admin/application/<int:id>/status', methods=['POST'])
@login_required
def update_application_status(id):
    if not current_user.is_admin():
        abort(403)
    
    application = Application.query.get_or_404(id)
    form = ApplicationStatusForm()
    
    if form.validate_on_submit():
        old_status = application.status
        application.status = form.status.data
        application.processed_by = current_user.id
        
        if form.rejection_reason.data:
            application.rejection_reason = form.rejection_reason.data
        
        # Add status history
        status_history = StatusHistory(
            application_id=application.id,
            old_status=old_status,
            new_status=form.status.data,
            changed_by=current_user.id,
            comment=form.comment.data
        )
        db.session.add(status_history)
        
        # Generate PDF if approved
        if form.status.data == 'validee':
            try:
                pdf_path = generate_pdf_document(application)
                if pdf_path:
                    # Create document record
                    document = Document(
                        application_id=application.id,
                        filename=os.path.basename(pdf_path),
                        original_filename=f"document_officiel_{application.reference_number}.pdf",
                        file_path=pdf_path,
                        file_size=os.path.getsize(pdf_path),
                        document_type='official_document'
                    )
                    db.session.add(document)
            except Exception as e:
                app.logger.error(f"Error generating PDF: {e}")
        
        db.session.commit()
        
        log_audit(current_user.id, 'update_status', 'application', application.id, 
                 f'Status changed from {old_status} to {form.status.data}')
        
        # Send notification
        send_notification_email(application.user.email,
                               f'Mise à jour de votre demande {application.reference_number}',
                               f'Le statut de votre demande a été mis à jour: {application.get_status_display()}')
        
        flash('Statut mis à jour avec succès.', 'success')
    
    return redirect(url_for('view_application', id=id))

@app.route('/download/<int:document_id>')
@login_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    application = document.application
    
    # Check permissions
    if not current_user.is_admin() and application.user_id != current_user.id:
        abort(403)
    
    if not os.path.exists(document.file_path):
        abort(404)
    
    return send_file(document.file_path, 
                     as_attachment=True, 
                     download_name=document.original_filename)

@app.route('/payment/simulate/<int:application_id>', methods=['POST'])
@login_required
def simulate_payment(application_id):
    application = Application.query.get_or_404(application_id)
    
    if application.user_id != current_user.id:
        abort(403)
    
    # Simulate payment processing
    application.payment_status = 'paid'
    db.session.commit()
    
    log_audit(current_user.id, 'payment', 'application', application.id, 'Payment processed')
    
    flash('Paiement effectué avec succès.', 'success')
    return redirect(url_for('view_application', id=application_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    try:
        db.session.rollback()
    except Exception as e:
        app.logger.warning(f'Erreur lors du rollback DB: {e}')
        # Fermer la session et en créer une nouvelle
        db.session.close()
    return render_template('errors/500.html'), 500

# Nouvelles routes pour le système hiérarchique des unités consulaires

@app.route('/admin/units')
@login_required
def list_consular_units():
    """Liste toutes les unités consulaires pour les admins"""
    if not current_user.is_admin():
        abort(403)
    
    units = UniteConsulaire.query.order_by(UniteConsulaire.pays, UniteConsulaire.ville).all()
    
    # Enrichir avec les statistiques
    units_data = []
    for unit in units:
        units_data.append({
            'unit': unit,
            'agents_count': unit.get_agents_count(),
            'services_count': len(unit.get_services_actifs()),
            'applications_count': len(unit.applications) if unit.applications else 0
        })
    
    return render_template('dashboard/admin_units.html', units_data=units_data)

@app.route('/admin/units/<int:unit_id>/services')
@login_required
def unit_services(unit_id):
    """Voir les services configurés pour une unité consulaire"""
    if not current_user.is_admin():
        abort(403)
    
    unit = UniteConsulaire.query.get_or_404(unit_id)
    configured_services = unit.get_services_actifs()
    all_services = Service.query.all()
    
    # Préparer les données des services avec tarifs
    services_data = []
    for service in all_services:
        # Trouver si ce service est configuré pour cette unité
        unit_service = next((us for us in configured_services if us.service_id == service.id), None)
        services_data.append({
            'service': service,
            'configured': unit_service is not None,
            'tarif': unit_service.tarif_personnalise if unit_service else service.tarif_de_base,
            'actif': unit_service.actif if unit_service else False
        })
    
    return render_template('admin/unit_services.html', unit=unit, services_data=services_data)

@app.route('/admin/hierarchy')
@login_required
def system_hierarchy():
    """Vue d'ensemble de la hiérarchie du système"""
    if not current_user.is_admin():
        abort(403)
    
    # Statistiques générales
    stats = {
        'total_units': UniteConsulaire.query.count(),
        'total_agents': User.query.filter_by(role='agent').count(),
        'total_services': Service.query.count(),
        'total_configurations': UniteConsulaire_Service.query.filter_by(actif=True).count(),
        'total_applications': Application.query.count(),
        'users_by_role': dict(db.session.query(User.role, func.count(User.id)).group_by(User.role).all())
    }
    
    # Unités par pays
    units_by_country = {}
    units = UniteConsulaire.query.all()
    for unit in units:
        country = unit.pays
        if country not in units_by_country:
            units_by_country[country] = []
        units_by_country[country].append({
            'unit': unit,
            'agents': [agent for agent in unit.agents if agent.role == 'agent'],
            'services_count': len(unit.get_services_actifs())
        })
    
    return render_template('admin/hierarchy.html', stats=stats, units_by_country=units_by_country)

@app.route('/agent/my-unit')
@login_required
def agent_unit_dashboard():
    """Interface pour les agents pour gérer leur unité"""
    if current_user.role != 'agent':
        abort(403)
    
    if not current_user.unite_consulaire_id:
        flash('Vous n\'êtes pas encore assigné à une unité consulaire.', 'warning')
        return redirect('/admin/hierarchy')
    
    unit = current_user.unite_consulaire
    configured_services = unit.get_services_actifs()
    recent_applications = Application.query.filter_by(unite_consulaire_id=unit.id).order_by(Application.created_at.desc()).limit(10).all()
    
    return render_template('agent/unit_dashboard.html', 
                         unit=unit, 
                         configured_services=configured_services,
                         recent_applications=recent_applications)

@app.route('/api/units-by-location')
def api_units_by_location():
    """API pour récupérer les unités consulaires par localisation (pour les formulaires)"""
    country = request.args.get('country', '')
    city = request.args.get('city', '')
    
    query = UniteConsulaire.query.filter_by(active=True)
    
    if country:
        query = query.filter(UniteConsulaire.pays.ilike(f'%{country}%'))
    if city:
        query = query.filter(UniteConsulaire.ville.ilike(f'%{city}%'))
    
    units = query.all()
    
    return jsonify([{
        'id': unit.id,
        'nom': unit.nom,
        'type': unit.type,
        'ville': unit.ville,
        'pays': unit.pays,
        'services_count': len(unit.get_services_actifs())
    } for unit in units])

@app.route('/api/unit-services/<int:unit_id>')
def api_unit_services(unit_id):
    """API pour récupérer les services disponibles pour une unité"""
    unit = UniteConsulaire.query.get_or_404(unit_id)
    configured_services = unit.get_services_actifs()
    
    return jsonify([{
        'service_code': us.service.code,
        'service_name': us.service.nom,
        'tarif': us.tarif_personnalise,
        'delai': us.service.delai_traitement
    } for us in configured_services])

# API Routes pour l'administration
@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def api_admin_users():
    """API pour gérer les utilisateurs"""
    if not current_user.is_admin():
        abort(403)
    
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'active': user.active,
            'unite_consulaire_id': user.unite_consulaire_id,
            'unite_consulaire_nom': user.unite_consulaire.nom if user.unite_consulaire else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        } for user in users])
    
    elif request.method == 'POST':
        try:
            email = request.form.get('email')
            full_name = request.form.get('full_name')
            role = request.form.get('role')
            unit_id = request.form.get('unit_id')
            
            # Vérifier si l'email existe déjà
            if User.query.filter_by(email=email).first():
                return jsonify({'success': False, 'error': 'Email déjà utilisé'})
            
            # Séparer nom et prénom
            if full_name:
                name_parts = full_name.strip().split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
            else:
                first_name = ''
                last_name = ''
            
            # Créer l'utilisateur
            user = User()
            user.email = email
            user.username = email.split('@')[0]  # Utiliser la partie avant @ comme username
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.active = True
            user.profile_complete = True
            user.password_hash = generate_password_hash('motdepasse123')  # Mot de passe temporaire
            
            if role == 'agent' and unit_id:
                user.unite_consulaire_id = int(unit_id)
            
            db.session.add(user)
            db.session.commit()
            
            log_audit(current_user.id, 'create_user', 'user', user.id, f'Utilisateur créé: {user.email}')
            
            return jsonify({'success': True, 'user_id': user.id})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/units', methods=['GET', 'POST'])
@login_required
def api_admin_units():
    """API pour gérer les unités consulaires"""
    if not current_user.is_admin():
        abort(403)
    
    if request.method == 'GET':
        role_filter = request.args.get('role')
        if role_filter == 'agent':
            # Retourner seulement les agents
            agents = User.query.filter_by(role='agent').all()
            return jsonify([{
                'id': agent.id,
                'username': agent.username,
                'email': agent.email,
                'first_name': agent.first_name,
                'last_name': agent.last_name,
                'role': agent.role,
                'active': agent.active,
                'unite_consulaire_id': agent.unite_consulaire_id,
                'unite_consulaire_nom': agent.unite_consulaire.nom if agent.unite_consulaire else None
            } for agent in agents])
        
        units = UniteConsulaire.query.all()
        return jsonify([{
            'id': unit.id,
            'nom': unit.nom,
            'type': unit.type,
            'pays': unit.pays,
            'ville': unit.ville,
            'active': unit.active,
            'agents_count': len([agent for agent in unit.agents if agent.role == 'agent']),
            'services_count': len(unit.get_services_actifs()),
            'applications_count': len(unit.applications) if unit.applications else 0,
            'created_at': unit.created_at.isoformat() if unit.created_at else None
        } for unit in units])
    
    elif request.method == 'POST':
        try:
            # Informations générales
            nom = request.form.get('nom')
            type_unite = request.form.get('type')
            pays = request.form.get('pays')
            ville = request.form.get('ville')
            
            # Chef d'unité
            chef_nom = request.form.get('chef_nom')
            chef_titre = request.form.get('chef_titre')
            
            # Contacts (premier email et téléphone obligatoires)
            email_principal = request.form.get('email_principal')
            email_secondaire = request.form.get('email_secondaire')
            telephone_principal = request.form.get('telephone_principal')
            telephone_secondaire = request.form.get('telephone_secondaire')
            
            # Adresse complète
            adresse_rue = request.form.get('adresse_rue')
            adresse_ville = request.form.get('adresse_ville')
            adresse_code_postal = request.form.get('adresse_code_postal')
            adresse_complement = request.form.get('adresse_complement')
            
            # Créer l'unité consulaire
            unit = UniteConsulaire()
            unit.nom = nom
            unit.type = type_unite
            unit.pays = pays
            unit.ville = ville
            unit.active = True
            unit.created_by = current_user.id
            
            # Chef d'unité
            unit.chef_nom = chef_nom
            unit.chef_titre = chef_titre
            
            # Contacts
            unit.email_principal = email_principal
            unit.email_secondaire = email_secondaire
            unit.telephone_principal = telephone_principal
            unit.telephone_secondaire = telephone_secondaire
            
            # Adresse
            unit.adresse_rue = adresse_rue
            unit.adresse_ville = adresse_ville
            unit.adresse_code_postal = adresse_code_postal
            unit.adresse_complement = adresse_complement
            
            # Compatibilité avec les anciens champs
            unit.email = email_principal
            unit.telephone = telephone_principal
            
            db.session.add(unit)
            db.session.commit()
            
            log_audit(current_user.id, 'create_unit', 'unite_consulaire', unit.id, f'Unité créée: {unit.nom}')
            
            return jsonify({'success': True, 'unit_id': unit.id})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/units/<int:unit_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_admin_unit_detail(unit_id):
    """API pour gérer une unité consulaire spécifique"""
    if not current_user.is_admin():
        abort(403)
    
    unit = UniteConsulaire.query.get_or_404(unit_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': unit.id,
            'nom': unit.nom,
            'type': unit.type,
            'pays': unit.pays,
            'ville': unit.ville,
            'active': unit.active,
            
            # Chef d'unité
            'chef_nom': unit.chef_nom,
            'chef_titre': unit.chef_titre,
            
            # Contacts
            'email_principal': unit.email_principal,
            'email_secondaire': unit.email_secondaire,
            'telephone_principal': unit.telephone_principal,
            'telephone_secondaire': unit.telephone_secondaire,
            
            # Adresse
            'adresse_rue': unit.adresse_rue,
            'adresse_ville': unit.adresse_ville,
            'adresse_code_postal': unit.adresse_code_postal,
            'adresse_complement': unit.adresse_complement,
            
            # Compatibilité
            'email': unit.email,
            'telephone': unit.telephone,
            
            # Statistiques
            'agents_count': len([agent for agent in unit.agents if agent.role == 'agent']),
            'services_count': len(unit.get_services_actifs()),
            'applications_count': len(unit.applications) if unit.applications else 0,
            'created_at': unit.created_at.isoformat() if unit.created_at else None
        })
    
    elif request.method == 'PUT':
        try:
            # Informations générales
            unit.nom = request.form.get('nom', unit.nom)
            unit.type = request.form.get('type', unit.type)
            unit.pays = request.form.get('pays', unit.pays)
            unit.ville = request.form.get('ville', unit.ville)
            
            # Chef d'unité
            unit.chef_nom = request.form.get('chef_nom', unit.chef_nom)
            unit.chef_titre = request.form.get('chef_titre', unit.chef_titre)
            
            # Contacts
            unit.email_principal = request.form.get('email_principal', unit.email_principal)
            unit.email_secondaire = request.form.get('email_secondaire', unit.email_secondaire)
            unit.telephone_principal = request.form.get('telephone_principal', unit.telephone_principal)
            unit.telephone_secondaire = request.form.get('telephone_secondaire', unit.telephone_secondaire)
            
            # Adresse
            unit.adresse_rue = request.form.get('adresse_rue', unit.adresse_rue)
            unit.adresse_ville = request.form.get('adresse_ville', unit.adresse_ville)
            unit.adresse_code_postal = request.form.get('adresse_code_postal', unit.adresse_code_postal)
            unit.adresse_complement = request.form.get('adresse_complement', unit.adresse_complement)
            
            # Mettre à jour les anciens champs pour compatibilité
            if unit.email_principal:
                unit.email = unit.email_principal
            if unit.telephone_principal:
                unit.telephone = unit.telephone_principal
            
            db.session.commit()
            
            log_audit(current_user.id, 'update_unit', 'unite_consulaire', unit.id, f'Unité modifiée: {unit.nom}')
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'DELETE':
        try:
            # Vérifier s'il y a des agents assignés
            if any(agent.role == 'agent' for agent in unit.agents):
                return jsonify({'success': False, 'error': 'Impossible de supprimer une unité avec des agents assignés'})
            
            # Vérifier s'il y a des applications
            if unit.applications:
                return jsonify({'success': False, 'error': 'Impossible de supprimer une unité avec des demandes existantes'})
            
            db.session.delete(unit)
            db.session.commit()
            
            log_audit(current_user.id, 'delete_unit', 'unite_consulaire', unit.id, f'Unité supprimée: {unit.nom}')
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/units/<int:unit_id>/toggle', methods=['POST'])
@login_required
def api_toggle_unit_status(unit_id):
    """API pour activer/désactiver une unité consulaire"""
    if not current_user.is_admin():
        abort(403)
    
    try:
        unit = UniteConsulaire.query.get_or_404(unit_id)
        unit.active = not unit.active
        db.session.commit()
        
        status = 'activée' if unit.active else 'désactivée'
        log_audit(current_user.id, 'toggle_unit_status', 'unite_consulaire', unit.id, f'Unité {status}: {unit.nom}')
        
        return jsonify({'success': True, 'active': unit.active})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/users/<int:user_id>/assign-unit', methods=['POST'])
@login_required
def api_assign_user_unit(user_id):
    """API pour assigner un utilisateur à une unité"""
    if not current_user.is_admin():
        abort(403)
    
    try:
        user = User.query.get_or_404(user_id)
        unit_id = request.form.get('unit_id')
        unit_name = "Aucune"
        
        if unit_id:
            unit = UniteConsulaire.query.get_or_404(int(unit_id))
            user.unite_consulaire_id = unit.id
            unit_name = unit.nom
        else:
            user.unite_consulaire_id = None
        
        db.session.commit()
        
        log_audit(current_user.id, 'assign_unit', 'user', user.id, f'Unité assignée: {unit_name}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/system-overview')
def system_overview():
    """Vue publique du système e-consulaire hiérarchique (sans données sensibles)"""
    
    # Statistiques générales (non-sensibles)
    stats = {
        'total_units': UniteConsulaire.query.count(),
        'total_services_types': Service.query.count(),
        'countries_served': len(set([unit.pays for unit in UniteConsulaire.query.all()]))
    }
    
    # Unités consulaires publiques
    units = UniteConsulaire.query.filter_by(active=True).all()
    units_data = []
    for unit in units:
        units_data.append({
            'nom': unit.nom,
            'type': unit.type,
            'ville': unit.ville,
            'pays': unit.pays,
            'services_count': len(unit.get_services_actifs()),
            'contact_public': {
                'email': unit.email,
                'telephone': unit.telephone
            }
        })
    
    return render_template('public/system_overview.html', stats=stats, units=units_data)

# Logout route already exists elsewhere

# Auth blueprint already registered in app.py
