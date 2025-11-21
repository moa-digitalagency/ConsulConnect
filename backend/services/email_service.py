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
        self.from_email = 'noreply@econsulaire-rdc.com'
        self.from_name = 'e-Consulaire RDC'
    
    def send_email(self, to_email, subject, html_content, text_content=None):
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
                </div>
                <p>Cordialement,<br><strong>L'équipe e-Consulaire RDC</strong></p>
            </div>
        </div>
        """
        return self.send_email(user.email, subject, html_content)
    
    def send_new_application_email_to_agent(self, agent, application):
        subject = f"Nouvelle demande reçue - {application.service_type}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">e-Consulaire RDC</h1>
            </div>
            <div style="padding: 30px; background: #f9fafb;">
                <h2 style="color: #1f2937;">📋 Nouvelle Demande à Traiter</h2>
                <p>Bonjour <strong>{agent.get_full_name()}</strong>,</p>
                <p>Une nouvelle demande vient d'être soumise et nécessite votre attention.</p>
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <p><strong>Référence :</strong> {application.reference_number}</p>
                    <p><strong>Service :</strong> {application.get_service_display()}</p>
                    <p><strong>Demandeur :</strong> {application.user.get_full_name()}</p>
                </div>
            </div>
        </div>
        """
        return self.send_email(agent.email, subject, html_content)
    
    def send_status_change_email(self, user, application, old_status, new_status, comment=None):
        subject = f"Mise à jour de votre demande - {application.reference_number}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="padding: 30px; background: #f9fafb;">
                <h2 style="color: #1f2937;">Mise à jour de statut</h2>
                <p>Bonjour <strong>{user.get_full_name()}</strong>,</p>
                <p>Le statut de votre demande <strong>{application.reference_number}</strong> a été mis à jour.</p>
                <p><strong>Nouveau Statut :</strong> {application.get_status_display()}</p>
                {f'<p><strong>Commentaire :</strong> {comment}</p>' if comment else ''}
                <p>Cordialement,<br><strong>L'équipe e-Consulaire RDC</strong></p>
            </div>
        </div>
        """
        return self.send_email(user.email, subject, html_content)

email_service = EmailService()
