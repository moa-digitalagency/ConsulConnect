# Service d'envoi d'emails avec SendGrid pour le système e-consulaire
import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app import app

class EmailService:
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not self.sendgrid_key:
            app.logger.warning('SENDGRID_API_KEY non configurée')
            self.enabled = False
        else:
            self.sg = SendGridAPIClient(self.sendgrid_key)
            self.enabled = True
            
        # Email par défaut pour les envois (configurable par super admin)
        self.from_email = 'noreply@econsulaire-rdc.com'
        self.from_name = 'e-Consulaire RDC'
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Envoyer un email via SendGrid"""
        if not self.enabled:
            app.logger.warning(f'Email non envoyé (SendGrid désactivé): {to_email} - {subject}')
            return False
            
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject
            )
            
            if html_content:
                message.content = Content("text/html", html_content)
            elif text_content:
                message.content = Content("text/plain", text_content)
            
            response = self.sg.send(message)
            app.logger.info(f'Email envoyé avec succès à {to_email}: {subject}')
            return True
            
        except Exception as e:
            app.logger.error(f'Erreur SendGrid: {e}')
            return False
    
    def send_application_received_email(self, user, application):
        """Email de confirmation de réception de demande pour l'usager"""
        subject = f"Demande reçue - Réf: {application.reference_number}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">e-Consulaire RDC</h1>
                <p style="color: #fecaca; margin: 5px 0;">République Démocratique du Congo</p>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2 style="color: #1f2937;">Demande Reçue avec Succès</h2>
                
                <p>Bonjour <strong>{user.get_full_name()}</strong>,</p>
                
                <p>Votre demande de <strong>{application.get_service_display()}</strong> a été reçue par nos services consulaires.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <h3 style="margin-top: 0; color: #dc2626;">Détails de votre demande</h3>
                    <p><strong>Numéro de référence :</strong> {application.reference_number}</p>
                    <p><strong>Type de service :</strong> {application.get_service_display()}</p>
                    <p><strong>Date de soumission :</strong> {application.created_at.strftime('%d/%m/%Y à %H:%M')}</p>
                    <p><strong>Statut actuel :</strong> {application.get_status_display()}</p>
                    <p><strong>Unité consulaire :</strong> {application.unite_consulaire.nom}</p>
                </div>
                
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #1e40af; margin-top: 0;">🔍 Suivi de votre demande</h4>
                    <p>Vous pouvez suivre l'évolution de votre demande en utilisant le numéro de référence <strong>{application.reference_number}</strong> sur notre portail en ligne.</p>
                </div>
                
                <p>Vous recevrez des notifications par email à chaque étape du traitement de votre dossier.</p>
                
                <p>Cordialement,<br>
                <strong>L'équipe e-Consulaire RDC</strong></p>
            </div>
            
            <div style="background: #374151; padding: 15px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">
                    Cet email a été envoyé automatiquement. Ne pas répondre à cette adresse.
                </p>
            </div>
        </div>
        """
        
        return self.send_email(user.email, subject, html_content)
    
    def send_new_application_email_to_agent(self, agent, application):
        """Email de notification de nouvelle demande pour l'agent"""
        subject = f"Nouvelle demande reçue - {application.service_type}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">e-Consulaire RDC</h1>
                <p style="color: #fecaca; margin: 5px 0;">Notification Agent</p>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2 style="color: #1f2937;">📋 Nouvelle Demande à Traiter</h2>
                
                <p>Bonjour <strong>{agent.get_full_name()}</strong>,</p>
                
                <p>Une nouvelle demande vient d'être soumise et nécessite votre attention.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <h3 style="margin-top: 0; color: #dc2626;">Détails de la demande</h3>
                    <p><strong>Référence :</strong> {application.reference_number}</p>
                    <p><strong>Service :</strong> {application.get_service_display()}</p>
                    <p><strong>Demandeur :</strong> {application.user.get_full_name()}</p>
                    <p><strong>Email :</strong> {application.user.email}</p>
                    <p><strong>Date :</strong> {application.created_at.strftime('%d/%m/%Y à %H:%M')}</p>
                    <p><strong>Unité :</strong> {application.unite_consulaire.nom}</p>
                </div>
                
                <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #92400e; margin-top: 0;">⚡ Action Requise</h4>
                    <p>Connectez-vous à votre interface agent pour prendre en charge cette demande et commencer le traitement.</p>
                </div>
                
                <p>Cordialement,<br>
                <strong>Système e-Consulaire RDC</strong></p>
            </div>
        </div>
        """
        
        return self.send_email(agent.email, subject, html_content)
    
    def send_status_change_email(self, user, application, old_status, new_status, comment=None):
        """Email de changement de statut pour l'usager"""
        status_messages = {
            'soumise': {'title': 'Demande Soumise', 'color': '#3b82f6', 'icon': '📝'},
            'en_traitement': {'title': 'En Cours de Traitement', 'color': '#f59e0b', 'icon': '⏳'},
            'validee': {'title': 'Demande Approuvée', 'color': '#10b981', 'icon': '✅'},
            'rejetee': {'title': 'Demande Rejetée', 'color': '#ef4444', 'icon': '❌'},
            'documents_requis': {'title': 'Documents Supplémentaires Requis', 'color': '#f59e0b', 'icon': '📎'},
            'pret_pour_retrait': {'title': 'Prêt pour Retrait', 'color': '#10b981', 'icon': '🎉'},
            'cloture': {'title': 'Dossier Clôturé', 'color': '#6b7280', 'icon': '🔒'}
        }
        
        status_info = status_messages.get(new_status, {'title': new_status, 'color': '#6b7280', 'icon': '📋'})
        
        subject = f"Mise à jour de votre demande - {application.reference_number}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">e-Consulaire RDC</h1>
                <p style="color: #fecaca; margin: 5px 0;">Mise à jour de statut</p>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <h2 style="color: #1f2937;">{status_info['icon']} {status_info['title']}</h2>
                
                <p>Bonjour <strong>{user.get_full_name()}</strong>,</p>
                
                <p>Le statut de votre demande <strong>{application.reference_number}</strong> a été mis à jour.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {status_info['color']};">
                    <h3 style="margin-top: 0; color: {status_info['color']};">Nouveau Statut</h3>
                    <p style="font-size: 18px; font-weight: bold; color: {status_info['color']};">{status_info['title']}</p>
                    <p><strong>Service :</strong> {application.get_service_display()}</p>
                    <p><strong>Date de mise à jour :</strong> {application.updated_at.strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
        """
        
        if comment:
            html_content += f"""
                <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #374151; margin-top: 0;">💬 Commentaire de l'agent</h4>
                    <p style="font-style: italic;">{comment}</p>
                </div>
            """
        
        # Messages spécifiques selon le statut
        if new_status == 'validee':
            html_content += """
                <div style="background: #d1fae5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #065f46; margin-top: 0;">🎉 Félicitations !</h4>
                    <p>Votre demande a été approuvée. Vous recevrez bientôt des instructions pour la suite des démarches.</p>
                </div>
            """
        elif new_status == 'rejetee':
            html_content += """
                <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #b91c1c; margin-top: 0;">ℹ️ Demande Rejetée</h4>
                    <p>Votre demande n'a pas pu être traitée favorablement. Consultez le commentaire ci-dessus pour plus de détails.</p>
                </div>
            """
        elif new_status == 'documents_requis':
            html_content += """
                <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #92400e; margin-top: 0;">📎 Documents Requis</h4>
                    <p>Des documents supplémentaires sont nécessaires pour traiter votre demande. Consultez votre espace personnel pour plus d'informations.</p>
                </div>
            """
        
        html_content += f"""
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #1e40af; margin-top: 0;">🔍 Suivi de demande</h4>
                    <p>Numéro de référence : <strong>{application.reference_number}</strong></p>
                    <p>Utilisez ce numéro pour suivre votre demande sur notre portail.</p>
                </div>
                
                <p>Cordialement,<br>
                <strong>L'équipe e-Consulaire RDC</strong></p>
            </div>
            
            <div style="background: #374151; padding: 15px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">
                    Cet email a été envoyé automatiquement. Ne pas répondre à cette adresse.
                </p>
            </div>
        </div>
        """
        
        return self.send_email(user.email, subject, html_content)

# Instance globale du service email
email_service = EmailService()