# Routes spécialisées pour les AGENTS (Personnel Diplomatique)
# Permissions: Recevoir notifications de demandes et les valider

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import app, db
from models import User, UniteConsulaire, Application, StatusHistory, Notification, AuditLog
from datetime import datetime

def agent_required(f):
    """Décorateur pour vérifier que l'utilisateur est agent"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'agent':
            flash('Accès réservé aux agents diplomatiques.', 'error')
            return redirect(url_for('auth.consulate_login'))
        return f(*args, **kwargs)
    return decorated_function

def agent_unit_access_required(f):
    """Décorateur pour vérifier que l'agent a accès à une unité consulaire"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.unite_consulaire_id:
            flash('Aucune unité consulaire assignée. Contactez votre administrateur.', 'error')
            return redirect(url_for('agent_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# =============================
# TABLEAU DE BORD AGENT
# =============================

@app.route('/agent/dashboard')
@login_required
@agent_required
@agent_unit_access_required
def agent_dashboard():
    """Tableau de bord de l'agent"""
    unit = current_user.unite_consulaire
    
    # Applications à traiter (nouvelles et en cours)
    pending_applications = Application.query.filter_by(
        unite_consulaire_id=unit.id,
        status='soumise'
    ).order_by(Application.created_at.desc()).all()
    
    processing_applications = Application.query.filter_by(
        unite_consulaire_id=unit.id,
        status='en_traitement',
        processed_by=current_user.id
    ).order_by(Application.updated_at.desc()).all()
    
    # Applications récemment traitées par cet agent
    recently_processed = Application.query.filter_by(
        processed_by=current_user.id
    ).filter(Application.status.in_(['validee', 'rejetee']))\
     .order_by(Application.updated_at.desc()).limit(5).all()
    
    # Notifications non lues
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        lu=False
    ).order_by(Notification.created_at.desc()).all()
    
    stats = {
        'pending_count': len(pending_applications),
        'processing_count': len(processing_applications),
        'notifications_count': len(unread_notifications),
        'unit_name': unit.nom
    }
    
    return render_template('agent/dashboard.html',
                         stats=stats,
                         pending_applications=pending_applications,
                         processing_applications=processing_applications,
                         recently_processed=recently_processed,
                         unread_notifications=unread_notifications)

# =============================
# GESTION DES DEMANDES
# =============================

@app.route('/agent/applications/pending')
@login_required
@agent_required
@agent_unit_access_required
def agent_pending_applications():
    """Liste des demandes en attente de traitement"""
    unit = current_user.unite_consulaire
    
    applications = Application.query.filter_by(
        unite_consulaire_id=unit.id,
        status='soumise'
    ).order_by(Application.created_at.desc()).all()
    
    return render_template('agent/pending_applications.html',
                         applications=applications,
                         unit=unit)

@app.route('/agent/applications/<int:app_id>/take', methods=['POST'])
@login_required
@agent_required
@agent_unit_access_required
def agent_take_application(app_id):
    """Prendre en charge une demande"""
    application = Application.query.get_or_404(app_id)
    
    # Vérifier que l'application appartient à l'unité de l'agent
    if application.unite_consulaire_id != current_user.unite_consulaire_id:
        flash('Cette demande n\'appartient pas à votre unité.', 'error')
        return redirect(url_for('agent_pending_applications'))
    
    # Vérifier que l'application n'est pas déjà prise
    if application.status != 'soumise':
        flash('Cette demande est déjà en cours de traitement.', 'error')
        return redirect(url_for('agent_pending_applications'))
    
    # Mettre à jour le statut
    application.status = 'en_traitement'
    application.processed_by = current_user.id
    application.updated_at = datetime.utcnow()
    
    # Ajouter l'historique
    status_history = StatusHistory(
        application_id=application.id,
        old_status='soumise',
        new_status='en_traitement',
        changed_by=current_user.id,
        comment=f'Demande prise en charge par {current_user.get_full_name()}'
    )
    db.session.add(status_history)
    
    # Marquer la notification comme lue si elle existe
    notification = Notification.query.filter_by(
        user_id=current_user.id,
        type_notification='nouvelle_demande',
        reference_id=application.id,
        lu=False
    ).first()
    if notification:
        notification.lu = True
        notification.lu_at = datetime.utcnow()
    
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action='take_application',
        table_name='application',
        record_id=application.id,
        details=f'Demande {application.reference_number} prise en charge'
    )
    
    flash(f'Demande {application.reference_number} prise en charge.', 'success')
    return redirect(url_for('agent_process_application', app_id=application.id))

@app.route('/agent/applications/<int:app_id>/process', methods=['GET', 'POST'])
@login_required
@agent_required
@agent_unit_access_required
def agent_process_application(app_id):
    """Traiter une demande (approuver/rejeter)"""
    application = Application.query.get_or_404(app_id)
    
    # Vérifications de sécurité
    if (application.unite_consulaire_id != current_user.unite_consulaire_id or 
        application.processed_by != current_user.id):
        flash('Vous n\'êtes pas autorisé à traiter cette demande.', 'error')
        return redirect(url_for('agent_dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment = request.form.get('comment', '').strip()
        
        # Validation du commentaire obligatoire
        if not comment:
            flash('Un commentaire est obligatoire pour traiter la demande.', 'error')
            return redirect(request.url)
        
        old_status = application.status
        
        if action == 'approve':
            application.status = 'validee'
            flash_message = f'Demande {application.reference_number} approuvée.'
            audit_action = 'approve_application'
        elif action == 'reject':
            application.status = 'rejetee'
            application.rejection_reason = comment
            flash_message = f'Demande {application.reference_number} rejetée.'
            audit_action = 'reject_application'
        elif action == 'request_documents':
            application.status = 'documents_requis'
            flash_message = f'Documents supplémentaires requis pour {application.reference_number}.'
            audit_action = 'request_documents'
        elif action == 'ready_for_pickup':
            application.status = 'pret_pour_retrait'
            flash_message = f'Demande {application.reference_number} prête pour retrait.'
            audit_action = 'ready_for_pickup'
        elif action == 'close':
            application.status = 'cloture'
            flash_message = f'Dossier {application.reference_number} clôturé.'
            audit_action = 'close_application'
        else:
            flash('Action invalide.', 'error')
            return redirect(request.url)
        
        application.updated_at = datetime.utcnow()
        
        # Ajouter l'historique avec commentaire obligatoire
        status_history = StatusHistory(
            application_id=application.id,
            old_status=old_status,
            new_status=application.status,
            changed_by=current_user.id,
            comment=comment
        )
        db.session.add(status_history)
        
        # Créer une notification pour l'utilisateur
        notification = Notification(
            user_id=application.user_id,
            type_notification='demande_traitee',
            title=f'Demande {application.reference_number}',
            message=f'Statut mis à jour: {application.get_status_display()}',
            reference_id=application.id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        # Envoyer les notifications (interface + email)
        from notification_service import NotificationService
        NotificationService.notify_application_status_change(
            application, old_status, application.status, comment
        )
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action=audit_action,
            table_name='application',
            record_id=application.id,
            details=f'Demande {application.reference_number} {application.status}'
        )
        
        flash(flash_message, 'success')
        return redirect(url_for('agent_dashboard'))
    
    # GET - Afficher les détails de la demande
    form_data = json.loads(application.form_data) if application.form_data else {}
    documents = application.documents
    
    return render_template('agent/process_application.html',
                         application=application,
                         form_data=form_data,
                         documents=documents)

@app.route('/agent/applications/my')
@login_required
@agent_required
@agent_unit_access_required
def agent_my_applications():
    """Mes demandes en cours et traitées"""
    # Applications actuellement en traitement
    current_applications = Application.query.filter_by(
        processed_by=current_user.id,
        status='en_traitement'
    ).order_by(Application.updated_at.desc()).all()
    
    # Applications déjà traitées
    completed_applications = Application.query.filter_by(
        processed_by=current_user.id
    ).filter(Application.status.in_(['validee', 'rejetee']))\
     .order_by(Application.updated_at.desc()).limit(20).all()
    
    return render_template('agent/my_applications.html',
                         current_applications=current_applications,
                         completed_applications=completed_applications)

# =============================
# NOTIFICATIONS
# =============================

@app.route('/agent/notifications')
@login_required
@agent_required
def agent_notifications():
    """Liste des notifications de l'agent"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('agent/notifications.html',
                         notifications=notifications)

@app.route('/agent/notifications/<int:notif_id>/mark-read', methods=['POST'])
@login_required
@agent_required
def agent_mark_notification_read(notif_id):
    """Marquer une notification comme lue"""
    notification = Notification.query.filter_by(
        id=notif_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.lu = True
    notification.lu_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/agent/notifications/mark-all-read', methods=['POST'])
@login_required
@agent_required
def agent_mark_all_notifications_read():
    """Marquer toutes les notifications comme lues"""
    Notification.query.filter_by(
        user_id=current_user.id,
        lu=False
    ).update({
        'lu': True,
        'lu_at': datetime.utcnow()
    })
    
    db.session.commit()
    
    flash('Toutes les notifications marquées comme lues.', 'success')
    return redirect(url_for('agent_notifications'))

# =============================
# API POUR NOTIFICATIONS EN TEMPS RÉEL
# =============================

@app.route('/api/agent/notifications/count')
@login_required
@agent_required
def api_agent_notifications_count():
    """API pour obtenir le nombre de notifications non lues"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        lu=False
    ).count()
    
    return jsonify({'count': count})

@app.route('/api/agent/pending-applications/count')
@login_required
@agent_required  
@agent_unit_access_required
def api_agent_pending_count():
    """API pour obtenir le nombre de demandes en attente"""
    count = Application.query.filter_by(
        unite_consulaire_id=current_user.unite_consulaire_id,
        status='soumise'
    ).count()
    
    return jsonify({'count': count})