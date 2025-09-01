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
    recent_actions = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('superviseur/dashboard.html', 
                         stats=stats, 
                         roles_stats=roles_stats,
                         recent_actions=recent_actions)