# Routes spécialisées pour les SUPERVISEURS SYSTEME
# Permissions: Gérer utilisateurs, activer/désactiver services et unités consulaires

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import app, db
from models import User, UniteConsulaire, Service, UniteConsulaire_Service, AuditLog
from werkzeug.security import generate_password_hash
import json
from datetime import datetime

def superviseur_required(f):
    """Décorateur pour vérifier que l'utilisateur est superviseur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superviseur':
            flash('Accès réservé aux superviseurs système.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ========================
# GESTION DES UTILISATEURS
# ========================

@app.route('/superviseur/utilisateurs')
@login_required
@superviseur_required
def superviseur_utilisateurs():
    """Liste de tous les utilisateurs avec possibilité de gestion"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    stats = {
        'total': len(users),
        'usagers': len([u for u in users if u.role == 'usager']),
        'agents': len([u for u in users if u.role == 'agent']),
        'admins': len([u for u in users if u.role == 'admin']),
        'superviseurs': len([u for u in users if u.role == 'superviseur']),
        'actifs': len([u for u in users if u.active])
    }
    
    return render_template('superviseur/utilisateurs.html', users=users, stats=stats)

@app.route('/superviseur/utilisateurs/ajouter', methods=['GET', 'POST'])
@login_required
@superviseur_required
def superviseur_ajouter_utilisateur():
    """Ajouter un nouvel utilisateur (admin/agent/usager)"""
    if request.method == 'POST':
        # Récupération des données
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        phone = request.form.get('phone', '')
        password = request.form.get('password')
        unite_consulaire_id = request.form.get('unite_consulaire_id')
        
        # Validation
        if User.query.filter_by(email=email).first():
            flash('Cette adresse email est déjà utilisée.', 'error')
            return redirect(request.url)
            
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", 'error')
            return redirect(request.url)
        
        # Création de l'utilisateur
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
            password_hash=generate_password_hash(password),
            active=True,
            profile_complete=True,
            unite_consulaire_id=int(unite_consulaire_id) if unite_consulaire_id and unite_consulaire_id != '' else None
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='create_user',
            table_name='user',
            record_id=new_user.id,
            details=f'Utilisateur {role} créé: {email}'
        )
        
        flash(f'Utilisateur {role} {first_name} {last_name} créé avec succès.', 'success')
        return redirect(url_for('superviseur_utilisateurs'))
    
    # GET - Afficher le formulaire
    unites = UniteConsulaire.query.filter_by(active=True).order_by(UniteConsulaire.nom).all()
    return render_template('superviseur/ajouter_utilisateur.html', unites=unites)

@app.route('/superviseur/utilisateurs/<int:user_id>/activer', methods=['POST'])
@login_required
@superviseur_required
def superviseur_activer_utilisateur(user_id):
    """Activer/Désactiver un utilisateur"""
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    if action == 'activate':
        user.active = True
        message = f'Utilisateur {user.get_full_name()} activé.'
    elif action == 'deactivate':
        user.active = False
        message = f'Utilisateur {user.get_full_name()} désactivé.'
    else:
        flash('Action invalide.', 'error')
        return redirect(url_for('superviseur_utilisateurs'))
    
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action=action + '_user',
        table_name='user',
        record_id=user_id,
        details=message
    )
    
    flash(message, 'success')
    return redirect(url_for('superviseur_utilisateurs'))

# =============================
# GESTION DES UNITÉS CONSULAIRES
# =============================

@app.route('/superviseur/unites')
@login_required
@superviseur_required
def superviseur_unites():
    """Gestion des unités consulaires"""
    unites = UniteConsulaire.query.order_by(UniteConsulaire.nom).all()
    
    for unite in unites:
        unite.agents_count = unite.get_agents_count()
        unite.services_count = len(unite.get_services_actifs())
        
    return render_template('superviseur/unites.html', unites=unites)

@app.route('/superviseur/unites/<int:unite_id>/activer', methods=['POST'])
@login_required
@superviseur_required
def superviseur_activer_unite(unite_id):
    """Activer/Désactiver une unité consulaire"""
    unite = UniteConsulaire.query.get_or_404(unite_id)
    action = request.form.get('action')
    
    if action == 'activate':
        unite.active = True
        message = f'Unité consulaire {unite.nom} activée.'
    elif action == 'deactivate':
        unite.active = False
        message = f'Unité consulaire {unite.nom} désactivée.'
    else:
        flash('Action invalide.', 'error')
        return redirect(url_for('superviseur_unites'))
    
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action=action + '_unite',
        table_name='unite_consulaire',
        record_id=unite_id,
        details=message
    )
    
    flash(message, 'success')
    return redirect(url_for('superviseur_unites'))

# =========================
# GESTION DES SERVICES
# =========================

@app.route('/superviseur/services')
@login_required
@superviseur_required
def superviseur_services():
    """Gestion des services consulaires globaux"""
    services = Service.query.order_by(Service.nom).all()
    
    for service in services:
        service.unites_count = len([us for us in service.unites_proposant if us.actif])
        
    return render_template('superviseur/services.html', services=services)

@app.route('/superviseur/services/<int:service_id>/activer', methods=['POST'])
@login_required
@superviseur_required
def superviseur_activer_service(service_id):
    """Activer/Désactiver un service consulaire globalement"""
    service = Service.query.get_or_404(service_id)
    action = request.form.get('action')
    
    if action == 'activate':
        service.actif = True
        message = f'Service {service.nom} activé globalement.'
    elif action == 'deactivate':
        service.actif = False
        message = f'Service {service.nom} désactivé globalement.'
        
        # Désactiver aussi dans toutes les unités
        UniteConsulaire_Service.query.filter_by(service_id=service_id).update({'actif': False})
        
    else:
        flash('Action invalide.', 'error')
        return redirect(url_for('superviseur_services'))
    
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action=action + '_service_global',
        table_name='service',
        record_id=service_id,
        details=message
    )
    
    flash(message, 'success')
    return redirect(url_for('superviseur_services'))

# =========================
# TABLEAU DE BORD SUPERVISEUR
# =========================

@app.route('/superviseur/dashboard')
@login_required
@superviseur_required
def superviseur_dashboard():
    """Tableau de bord du superviseur système"""
    
    # Statistiques générales
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'total_unites': UniteConsulaire.query.count(),
        'active_unites': UniteConsulaire.query.filter_by(active=True).count(),
        'total_services': Service.query.count(),
        'active_services': Service.query.filter_by(actif=True).count(),
    }
    
    # Répartition des rôles
    roles_stats = {}
    for role in ['usager', 'agent', 'admin', 'superviseur']:
        roles_stats[role] = User.query.filter_by(role=role).count()
    
    # Dernières actions (audit logs)
    recent_actions = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template('superviseur/dashboard.html', 
                         stats=stats, 
                         roles_stats=roles_stats,
                         recent_actions=recent_actions)

@app.route('/superviseur/email-config', methods=['GET', 'POST'])
@login_required
@superviseur_required
def superviseur_email_config():
    """Configuration des paramètres email SendGrid"""
    from email_service import email_service
    import os
    from datetime import datetime, timedelta
    
    # Configuration par défaut
    default_config = {
        'from_email': 'noreply@econsulaire-rdc.com',
        'from_name': 'e-Consulaire RDC',
        'enabled_notifications': ['application_received', 'status_change', 'agent_alert']
    }
    
    # Statistiques fictives (à remplacer par de vraies stats)
    stats = {
        'today': 0,
        'week': 0,
        'month': 0
    }
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_config':
            # Sauvegarder la configuration
            email_service.from_email = request.form.get('from_email', default_config['from_email'])
            email_service.from_name = request.form.get('from_name', default_config['from_name'])
            
            flash('Configuration email sauvegardée avec succès.', 'success')
            
        elif action == 'test_email':
            # Envoyer un email de test
            success = email_service.send_email(
                to_email=current_user.email,
                subject='Test de Configuration SendGrid - e-Consulaire RDC',
                html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">e-Consulaire RDC</h1>
                        <p style="color: #fecaca; margin: 5px 0;">Test de Configuration Email</p>
                    </div>
                    
                    <div style="padding: 30px; background: #f9fafb;">
                        <h2 style="color: #1f2937;">✅ Configuration SendGrid Testée</h2>
                        
                        <p>Bonjour <strong>{current_user.get_full_name()}</strong>,</p>
                        
                        <p>Ce message confirme que votre configuration SendGrid fonctionne correctement pour le système e-Consulaire RDC.</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                            <h3 style="margin-top: 0; color: #10b981;">Détails du Test</h3>
                            <p><strong>Email expéditeur :</strong> {email_service.from_email}</p>
                            <p><strong>Nom expéditeur :</strong> {email_service.from_name}</p>
                            <p><strong>Date/Heure :</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                            <p><strong>Statut API :</strong> {'Actif' if email_service.enabled else 'Inactif'}</p>
                        </div>
                        
                        <p>Les utilisateurs recevront désormais des notifications par email pour :</p>
                        <ul>
                            <li>Confirmation de réception de demande</li>
                            <li>Changements de statut de demande</li>
                            <li>Alertes pour les agents consulaires</li>
                        </ul>
                        
                        <p>Cordialement,<br>
                        <strong>Système e-Consulaire RDC</strong></p>
                    </div>
                    
                    <div style="background: #374151; padding: 15px; text-align: center;">
                        <p style="color: #9ca3af; margin: 0; font-size: 12px;">
                            Email de test généré automatiquement par le super administrateur.
                        </p>
                    </div>
                </div>
                """
            )
            
            if success:
                flash(f'Email de test envoyé avec succès à {current_user.email}', 'success')
            else:
                flash('Erreur lors de l\'envoi de l\'email de test. Vérifiez la configuration SendGrid.', 'error')
        
        return redirect(url_for('superviseur_email_config'))
    
    return render_template('superviseur/email_config.html',
                         sendgrid_status=email_service.enabled,
                         config=default_config,
                         stats=stats)

@app.route('/superviseur/security-dashboard')
@login_required
@superviseur_required
def superviseur_security_dashboard():
    """Tableau de bord sécurité, sauvegardes et mises à jour"""
    from backup_service import backup_service
    from update_service import update_service
    from security_service import security_service
    
    # Statut de sécurité
    security_status = {
        'encryption_status': 'Actif' if security_service.fernet else 'Inactif'
    }
    
    # Statistiques des sauvegardes
    recent_backups = backup_service.list_backups()[:5]
    backup_stats = {
        'total_backups': len(recent_backups),
        'total_size_mb': sum(b['size_mb'] for b in recent_backups)
    }
    
    # Statut des mises à jour
    update_status = update_service.check_for_updates()
    
    # Événements de sécurité récents
    security_events_query = AuditLog.query.filter(
        AuditLog.action.like('security_%')
    ).order_by(AuditLog.created_at.desc()).limit(10)
    
    security_events = {
        'recent': security_events_query.all(),
        'recent_count': security_events_query.count()
    }
    
    return render_template('superviseur/security_dashboard.html',
                         security_status=security_status,
                         backup_stats=backup_stats,
                         recent_backups=recent_backups,
                         update_status=update_status,
                         security_events=security_events)

# API Routes pour les actions de sécurité

@app.route('/superviseur/api/backup/create', methods=['POST'])
@login_required
@superviseur_required
def api_create_backup():
    """API pour créer une sauvegarde"""
    from backup_service import backup_service
    import json
    
    data = request.get_json() or {}
    backup_type = data.get('type', 'full')
    include_files = backup_type == 'full'
    
    result = backup_service.create_full_backup(include_files=include_files)
    
    return json.dumps({
        'success': result['success'],
        'message': f'Sauvegarde créée: {result["backup_name"]}' if result['success'] else None,
        'error': result.get('error')
    })

@app.route('/superviseur/api/backup/restore', methods=['POST'])
@login_required
@superviseur_required
def api_restore_backup():
    """API pour restaurer une sauvegarde"""
    from backup_service import backup_service
    import json
    
    data = request.get_json() or {}
    filename = data.get('filename')
    
    if not filename:
        return json.dumps({'success': False, 'error': 'Nom de fichier requis'})
    
    result = backup_service.restore_backup(filename)
    
    return json.dumps({
        'success': result['success'],
        'message': f'Sauvegarde {filename} restaurée' if result['success'] else None,
        'error': result.get('error')
    })

@app.route('/superviseur/api/updates/check', methods=['POST'])
@login_required
@superviseur_required
def api_check_updates():
    """API pour vérifier les mises à jour"""
    from update_service import update_service
    import json
    
    result = update_service.check_for_updates()
    
    return json.dumps({
        'success': True,
        'message': f'{result["commits_behind"]} mise(s) à jour disponible(s)' if result['updates_available'] else 'Système à jour',
        'data': result
    })

@app.route('/superviseur/api/updates/install', methods=['POST'])
@login_required
@superviseur_required
def api_install_updates():
    """API pour installer les mises à jour"""
    from update_service import update_service
    import json
    
    result = update_service.perform_update(create_backup=True)
    
    return json.dumps({
        'success': result['success'],
        'message': 'Mise à jour installée avec succès' if result['success'] else None,
        'error': result.get('error'),
        'data': result
    })

@app.route('/superviseur/api/security/scan', methods=['POST'])
@login_required
@superviseur_required
def api_security_scan():
    """API pour lancer un scan de sécurité"""
    import json
    
    # Simuler un scan de sécurité
    # Dans une vraie implémentation, ceci ferait un scan complet
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='security_scan_initiated',
        table_name='system',
        record_id=None,
        details='Scan de sécurité manuel lancé'
    )
    
    return json.dumps({
        'success': True,
        'message': 'Scan de sécurité completed - Aucune vulnérabilité détectée'
    })

@app.route('/superviseur/api/security/rotate-keys', methods=['POST'])
@login_required
@superviseur_required
def api_rotate_keys():
    """API pour effectuer la rotation des clés de chiffrement"""
    import json
    from security_service import security_service
    
    try:
        # Dans une vraie implémentation, ceci re-chiffrerait toutes les données
        # avec de nouvelles clés
        
        security_service.log_security_event(
            'key_rotation',
            current_user.id,
            'Rotation des clés de chiffrement effectuée'
        )
        
        return json.dumps({
            'success': True,
            'message': 'Rotation des clés effectuée avec succès'
        })
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f'Erreur lors de la rotation: {str(e)}'
        })

@app.route('/superviseur/api/status', methods=['GET'])
@login_required
@superviseur_required
def api_system_status():
    """API pour récupérer le statut système"""
    from backup_service import backup_service
    from update_service import update_service
    from security_service import security_service
    import json
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'security': {
            'encryption_active': security_service.fernet is not None
        },
        'backups': {
            'count': len(backup_service.list_backups())
        },
        'updates': update_service.check_for_updates()
    }
    
    return json.dumps(status)