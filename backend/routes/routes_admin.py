# Routes spécialisées pour les ADMINS (Staff Diplomatique)
# Permissions: Gérer leur unité consulaire assignée, configurer services et tarifs

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import app, db
from backend.models import User, UniteConsulaire, Service, UniteConsulaire_Service, Application, AuditLog
import json
from datetime import datetime

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Accès réservé aux administrateurs diplomatiques.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_unit_access_required(f):
    """Décorateur pour vérifier que l'admin a accès à une unité consulaire"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.unite_consulaire_id:
            flash('Aucune unité consulaire assignée. Contactez votre superviseur.', 'error')
            return redirect('/admin/hierarchy')
        return f(*args, **kwargs)
    return decorated_function

# =============================
# TABLEAU DE BORD ADMIN
# =============================

@app.route('/admin/unit-dashboard')
@login_required
@admin_required
@admin_unit_access_required
def admin_unit_dashboard():
    """Tableau de bord de l'admin pour son unité consulaire"""
    unit = current_user.unite_consulaire
    
    # Statistiques de l'unité
    agents_count = unit.get_agents_count()
    services_actifs = unit.get_services_actifs()
    
    # Applications reçues
    recent_applications = Application.query.filter_by(unite_consulaire_id=unit.id)\
                                         .order_by(Application.created_at.desc())\
                                         .limit(5).all()
    
    # Statistiques par service
    services_stats = {}
    for service_config in services_actifs:
        service_name = service_config.service.nom
        apps_count = Application.query.filter_by(
            unite_consulaire_id=unit.id,
            service_type=service_config.service.code
        ).count()
        services_stats[service_name] = {
            'applications': apps_count,
            'tarif': service_config.get_tarif_avec_devise(),
            'actif': service_config.actif
        }
    
    stats = {
        'agents_count': agents_count,
        'services_count': len(services_actifs),
        'total_applications': len(unit.applications) if unit.applications else 0,
        'services_stats': services_stats
    }
    
    return render_template('admin/unit_dashboard.html', 
                         unit=unit, 
                         stats=stats,
                         recent_applications=recent_applications)

# ===============================
# GESTION DES SERVICES DE L'UNITÉ
# ===============================

@app.route('/admin/my-unit/services')
@login_required
@admin_required
@admin_unit_access_required
def admin_unit_services():
    """Gérer les services de mon unité consulaire"""
    unit = current_user.unite_consulaire
    
    # Récupérer tous les services disponibles
    all_services = Service.query.filter_by(actif=True).all()
    
    # Récupérer les configurations existantes
    configured_services = {us.service_id: us for us in unit.services_disponibles}
    
    services_data = []
    for service in all_services:
        config = configured_services.get(service.id)
        services_data.append({
            'service': service,
            'configured': config is not None,
            'config': config,
            'tarif_personnalise': config.tarif_personnalise if config else service.tarif_de_base,
            'devise': config.devise if config else 'USD',
            'actif': config.actif if config else False,
            'delai_personnalise': config.delai_personnalise if config else service.delai_traitement,
            'notes_admin': config.notes_admin if config else ''
        })
    
    return render_template('admin/unit_services.html', 
                         unit=unit, 
                         services_data=services_data)

@app.route('/admin/my-unit/services/<int:service_id>/configure', methods=['POST'])
@login_required
@admin_required
@admin_unit_access_required
def admin_configure_service(service_id):
    """Configurer un service pour mon unité consulaire"""
    unit = current_user.unite_consulaire
    service = Service.query.get_or_404(service_id)
    
    # Récupération des données du formulaire
    tarif_personnalise = float(request.form.get('tarif_personnalise', service.tarif_de_base))
    devise = request.form.get('devise', 'USD')
    actif = request.form.get('actif') == 'on'
    delai_personnalise = request.form.get('delai_personnalise')
    notes_admin = request.form.get('notes_admin', '')
    
    # Conversion du délai
    if delai_personnalise:
        delai_personnalise = int(delai_personnalise)
    else:
        delai_personnalise = None
    
    # Vérifier si une configuration existe déjà
    existing_config = UniteConsulaire_Service.query.filter_by(
        unite_consulaire_id=unit.id,
        service_id=service_id
    ).first()
    
    if existing_config:
        # Mettre à jour la configuration existante
        existing_config.tarif_personnalise = tarif_personnalise
        existing_config.devise = devise
        existing_config.actif = actif
        existing_config.delai_personnalise = delai_personnalise
        existing_config.notes_admin = notes_admin
        existing_config.updated_at = datetime.utcnow()
        action_msg = f'Service {service.nom} mis à jour'
    else:
        # Créer une nouvelle configuration
        new_config = UniteConsulaire_Service(
            unite_consulaire_id=unit.id,
            service_id=service_id,
            tarif_personnalise=tarif_personnalise,
            devise=devise,
            actif=actif,
            delai_personnalise=delai_personnalise,
            notes_admin=notes_admin,
            configured_by=current_user.id
        )
        db.session.add(new_config)
        action_msg = f'Service {service.nom} configuré'
    
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action='configure_service',
        table_name='unite_service',
        record_id=service_id,
        details=f'{action_msg} - Tarif: {tarif_personnalise} {devise}'
    )
    
    flash(f'{action_msg} avec succès.', 'success')
    return redirect(url_for('admin_unit_services'))

@app.route('/admin/my-unit/services/<int:service_id>/toggle', methods=['POST'])
@login_required
@admin_required
@admin_unit_access_required
def admin_toggle_service(service_id):
    """Activer/Désactiver un service pour mon unité"""
    unit = current_user.unite_consulaire
    
    config = UniteConsulaire_Service.query.filter_by(
        unite_consulaire_id=unit.id,
        service_id=service_id
    ).first()
    
    if not config:
        flash('Service non configuré.', 'error')
        return redirect(url_for('admin_unit_services'))
    
    config.actif = not config.actif
    config.updated_at = datetime.utcnow()
    db.session.commit()
    
    status = 'activé' if config.actif else 'désactivé'
    flash(f'Service {config.service.nom} {status}.', 'success')
    
    # Audit log
    AuditLog.log_action(
        user_id=current_user.id,
        action='toggle_service',
        table_name='unite_service',
        record_id=config.id,
        details=f'Service {config.service.nom} {status}'
    )
    
    return redirect(url_for('admin_unit_services'))

# ===============================
# GESTION DU PERSONNEL
# ===============================

@app.route('/admin/my-unit/personnel')
@login_required
@admin_required
@admin_unit_access_required
def admin_unit_personnel():
    """Gérer le personnel de mon unité consulaire"""
    unit = current_user.unite_consulaire
    
    # Récupérer tous les agents de l'unité
    personnel = User.query.filter_by(
        unite_consulaire_id=unit.id,
        active=True
    ).order_by(User.role, User.last_name).all()
    
    # Séparer par rôle
    admins = [u for u in personnel if u.role == 'admin']
    agents = [u for u in personnel if u.role == 'agent']
    
    return render_template('admin/unit_personnel.html', 
                         unit=unit,
                         admins=admins,
                         agents=agents)

# ===============================
# INFORMATIONS DE L'UNITÉ
# ===============================

@app.route('/admin/my-unit/info', methods=['GET', 'POST'])
@login_required
@admin_required
@admin_unit_access_required
def admin_unit_info():
    """Gérer les informations de mon unité consulaire"""
    unit = current_user.unite_consulaire
    
    if request.method == 'POST':
        # Mise à jour des informations de l'unité
        unit.chef_nom = request.form.get('chef_nom', '')
        unit.chef_titre = request.form.get('chef_titre', '')
        unit.email_principal = request.form.get('email_principal', unit.email_principal)
        unit.email_secondaire = request.form.get('email_secondaire', '')
        unit.telephone_principal = request.form.get('telephone_principal', unit.telephone_principal)
        unit.telephone_secondaire = request.form.get('telephone_secondaire', '')
        unit.adresse_rue = request.form.get('adresse_rue', '')
        unit.adresse_ville = request.form.get('adresse_ville', unit.ville)
        unit.adresse_code_postal = request.form.get('adresse_code_postal', '')
        unit.adresse_complement = request.form.get('adresse_complement', '')
        
        db.session.commit()
        
        # Audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='update_unit_info',
            table_name='unite_consulaire',
            record_id=unit.id,
            details=f'Informations de l\'unité {unit.nom} mises à jour'
        )
        
        flash('Informations de l\'unité mises à jour avec succès.', 'success')
        return redirect(url_for('admin_unit_info'))
    
    return render_template('admin/unit_info.html', unit=unit)