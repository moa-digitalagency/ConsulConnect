"""
Routes CRUD pour la gestion complète des entités
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from backend.models import User, UniteConsulaire, Service, UniteConsulaire_Service
from backend.routes.routes_superviseur import superviseur_required
import json
from datetime import datetime

crud_bp = Blueprint('crud', __name__)

# =================== CRUD UTILISATEURS ===================

@crud_bp.route('/superviseur/users')
@login_required
@superviseur_required
def manage_users():
    """Page de gestion des utilisateurs"""
    users = User.query.all()
    unites = UniteConsulaire.query.filter_by(active=True).all()
    return render_template('superviseur/users.html', users=users, unites=unites)

@crud_bp.route('/superviseur/users/<int:user_id>/edit', methods=['GET'])
@login_required
@superviseur_required
def edit_user(user_id):
    """Formulaire d'édition utilisateur"""
    user = User.query.get_or_404(user_id)
    unites = UniteConsulaire.query.filter_by(active=True).all()
    return render_template('superviseur/edit_user.html', user=user, unites=unites)

@crud_bp.route('/superviseur/users/<int:user_id>/update', methods=['POST'])
@login_required
@superviseur_required
def update_user(user_id):
    """Mise à jour d'un utilisateur"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Mise à jour des champs
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.nom = request.form.get('nom')
        user.prenom = request.form.get('prenom')
        user.role = request.form.get('role')
        user.active = request.form.get('active') == 'on'
        
        # Unité consulaire pour les agents
        if user.role == 'agent':
            unite_id = request.form.get('unite_consulaire_id')
            user.unite_consulaire_id = int(unite_id) if unite_id else None
        else:
            user.unite_consulaire_id = None
            
        # Nouveau mot de passe si fourni
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Utilisateur mis à jour avec succès!', 'success')
        return redirect(url_for('crud.manage_users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
        return redirect(url_for('crud.edit_user', user_id=user_id))

@crud_bp.route('/superviseur/users/<int:user_id>/delete', methods=['POST'])
@login_required
@superviseur_required
def delete_user(user_id):
    """Suppression d'un utilisateur"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Vérifier qu'on ne supprime pas le superadmin
        if user.role == 'superviseur':
            flash('Impossible de supprimer un superviseur!', 'error')
            return redirect(url_for('crud.manage_users'))
            
        db.session.delete(user)
        db.session.commit()
        flash('Utilisateur supprimé avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        
    return redirect(url_for('crud.manage_users'))

@crud_bp.route('/superviseur/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@superviseur_required
def toggle_user_status(user_id):
    """Activer/désactiver un utilisateur"""
    try:
        user = User.query.get_or_404(user_id)
        user.active = not user.active
        db.session.commit()
        
        status = "activé" if user.active else "désactivé"
        return jsonify({'success': True, 'message': f'Utilisateur {status} avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# =================== CRUD UNITÉS CONSULAIRES ===================

@crud_bp.route('/superviseur/unites/<int:unite_id>/edit', methods=['GET'])
@login_required
@superviseur_required
def edit_unite(unite_id):
    """Formulaire d'édition d'unité consulaire"""
    unite = UniteConsulaire.query.get_or_404(unite_id)
    return render_template('superviseur/edit_unite.html', unite=unite)

@crud_bp.route('/superviseur/unites/<int:unite_id>/update', methods=['POST'])
@login_required
@superviseur_required
def update_unite(unite_id):
    """Mise à jour d'une unité consulaire"""
    try:
        unite = UniteConsulaire.query.get_or_404(unite_id)
        
        # Mise à jour des champs
        unite.nom = request.form.get('nom')
        unite.type = request.form.get('type')
        unite.ville = request.form.get('ville')
        unite.pays = request.form.get('pays')
        unite.chef_nom = request.form.get('chef_nom')
        unite.chef_titre = request.form.get('chef_titre')
        unite.email_principal = request.form.get('email_principal')
        unite.email_secondaire = request.form.get('email_secondaire')
        unite.telephone_principal = request.form.get('telephone_principal')
        unite.telephone_secondaire = request.form.get('telephone_secondaire')
        unite.adresse_rue = request.form.get('adresse_rue')
        unite.adresse_ville = request.form.get('adresse_ville')
        unite.adresse_code_postal = request.form.get('adresse_code_postal')
        unite.adresse_complement = request.form.get('adresse_complement')
        unite.active = request.form.get('active') == 'on'
        
        db.session.commit()
        flash('Unité consulaire mise à jour avec succès!', 'success')
        return redirect(url_for('superviseur_unites'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
        return redirect(url_for('superviseur_unites'))

@crud_bp.route('/superviseur/unites/create', methods=['POST'])
@login_required
@superviseur_required
def create_unite():
    """Création d'une nouvelle unité consulaire"""
    try:
        unite = UniteConsulaire(
            nom=request.form.get('nom'),
            type=request.form.get('type'),
            ville=request.form.get('ville'),
            pays=request.form.get('pays'),
            chef_nom=request.form.get('chef_nom'),
            chef_titre=request.form.get('chef_titre'),
            email_principal=request.form.get('email_principal'),
            email_secondaire=request.form.get('email_secondaire'),
            telephone_principal=request.form.get('telephone_principal'),
            telephone_secondaire=request.form.get('telephone_secondaire'),
            adresse_rue=request.form.get('adresse_rue'),
            adresse_ville=request.form.get('adresse_ville'),
            adresse_code_postal=request.form.get('adresse_code_postal'),
            adresse_complement=request.form.get('adresse_complement'),
            active=request.form.get('active') == 'on',
            created_by=current_user.id
        )
        
        db.session.add(unite)
        db.session.commit()
        flash('Nouvelle unité consulaire créée avec succès!', 'success')
        return redirect(url_for('superviseur_unites'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création: {str(e)}', 'error')
        return redirect(url_for('superviseur_unites'))

@crud_bp.route('/superviseur/unites/<int:unite_id>/toggle', methods=['POST'])
@login_required
@superviseur_required
def toggle_unite_status(unite_id):
    """Activer/désactiver une unité consulaire"""
    try:
        unite = UniteConsulaire.query.get_or_404(unite_id)
        unite.active = not unite.active
        db.session.commit()
        
        status = "activée" if unite.active else "désactivée"
        return jsonify({'success': True, 'message': f'Unité {status} avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@crud_bp.route('/superviseur/unites/<int:unite_id>/delete', methods=['POST'])
@login_required
@superviseur_required
def delete_unite(unite_id):
    """Suppression d'une unité consulaire"""
    try:
        unite = UniteConsulaire.query.get_or_404(unite_id)
        
        # Vérifier qu'il n'y a pas d'agents assignés
        if unite.agents:
            flash('Impossible de supprimer une unité avec des agents assignés!', 'error')
            return redirect(url_for('superviseur_unites'))
            
        db.session.delete(unite)
        db.session.commit()
        flash('Unité consulaire supprimée avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        
    return redirect(url_for('superviseur_unites'))

# =================== CRUD SERVICES ===================

@crud_bp.route('/superviseur/services/create', methods=['POST'])
@login_required
@superviseur_required
def create_service():
    """Création d'un nouveau service"""
    try:
        service = Service(
            code=request.form.get('code'),
            nom=request.form.get('nom'),
            description=request.form.get('description'),
            tarif_de_base=float(request.form.get('tarif_de_base', 0)),
            delai_traitement=int(request.form.get('delai_traitement', 7)),
            documents_requis=request.form.get('documents_requis'),
            actif=request.form.get('actif') == 'on'
        )
        
        db.session.add(service)
        db.session.commit()
        flash('Nouveau service créé avec succès!', 'success')
        return redirect(url_for('superviseur_services'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création: {str(e)}', 'error')
        return redirect(url_for('superviseur_services'))

@crud_bp.route('/superviseur/services/<int:service_id>/update', methods=['POST'])
@login_required
@superviseur_required
def update_service(service_id):
    """Mise à jour d'un service"""
    try:
        service = Service.query.get_or_404(service_id)
        
        service.code = request.form.get('code')
        service.nom = request.form.get('nom')
        service.description = request.form.get('description')
        service.tarif_de_base = float(request.form.get('tarif_de_base', 0))
        service.delai_traitement = int(request.form.get('delai_traitement', 7))
        service.documents_requis = request.form.get('documents_requis')
        service.actif = request.form.get('actif') == 'on'
        
        db.session.commit()
        flash('Service mis à jour avec succès!', 'success')
        return redirect(url_for('superviseur_services'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
        return redirect(url_for('superviseur_services'))

@crud_bp.route('/superviseur/services/<int:service_id>/toggle', methods=['POST'])
@login_required
@superviseur_required
def toggle_service_status(service_id):
    """Activer/désactiver un service"""
    try:
        service = Service.query.get_or_404(service_id)
        service.actif = not service.actif
        db.session.commit()
        
        status = "activé" if service.actif else "désactivé"
        return jsonify({'success': True, 'message': f'Service {status} avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# =================== PAGE PARAMÈTRES ===================

@crud_bp.route('/superviseur/settings')
@login_required
@superviseur_required
def settings():
    """Page des paramètres système"""
    import os
    sendgrid_enabled = bool(os.environ.get('SENDGRID_API_KEY'))
    return render_template('superviseur/settings.html', sendgrid_enabled=sendgrid_enabled)

@crud_bp.route('/superviseur/test-sendgrid', methods=['POST'])
@login_required
@superviseur_required
def test_sendgrid():
    """Test de la configuration SendGrid"""
    try:
        from email_service import EmailService
        
        email_service = EmailService()
        if not email_service.enabled:
            return jsonify({
                'success': False, 
                'message': 'SendGrid non configuré. Ajoutez SENDGRID_API_KEY dans les secrets.'
            })
        
        # Envoi d'un email de test
        test_email = current_user.email or 'test@econsulaire-rdc.com'
        success = email_service.send_email(
            to_email=test_email,
            subject="Test SendGrid - e-Consulaire RDC",
            html_content="""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Test SendGrid</h1>
                    <p style="color: #fecaca; margin: 5px 0;">e-Consulaire RDC</p>
                </div>
                <div style="padding: 30px; background: #f9fafb;">
                    <p>Ceci est un email de test pour vérifier la configuration SendGrid.</p>
                    <p>Si vous recevez cet email, la configuration est correcte !</p>
                    <p><strong>Envoyé le:</strong> {datetime}</p>
                </div>
            </div>
            """.format(datetime=datetime.now().strftime('%d/%m/%Y à %H:%M'))
        )
        
        if success:
            return jsonify({'success': True, 'message': f'Email de test envoyé à {test_email}'})
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de l\'envoi de l\'email'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})