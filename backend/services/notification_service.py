from app import db
from backend.models import Notification, User, Application
from datetime import datetime
from .email_service import email_service

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, type_notification, title, message, reference_id=None):
        notification = Notification(
            user_id=user_id,
            type=type_notification,
            title=title,
            message=message
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def notify_new_application(application):
        email_service.send_application_received_email(application.user, application)
        agents = User.query.filter_by(
            unite_consulaire_id=application.unite_consulaire_id,
            role='agent',
            active=True
        ).all()
        
        for agent in agents:
            NotificationService.create_notification(
                user_id=agent.id,
                type_notification='nouvelle_demande',
                title=f'Nouvelle demande: {application.service_type}',
                message=f'Demande {application.reference_number} reçue de {application.user.get_full_name()}',
                reference_id=application.id
            )
            email_service.send_new_application_email_to_agent(agent, application)
    
    @staticmethod
    def notify_application_status_change(application, old_status, new_status, comment=None):
        status_messages = {
            'en_traitement': 'Votre demande est maintenant en cours de traitement.',
            'validee': 'Votre demande a été approuvée !',
            'rejetee': 'Votre demande a été rejetée.',
        }
        
        message = status_messages.get(new_status, f'Statut de votre demande changé: {new_status}')
        
        NotificationService.create_notification(
            user_id=application.user_id,
            type_notification='demande_traitee',
            title=f'Demande {application.reference_number}',
            message=message,
            reference_id=application.id
        )
        
        email_service.send_status_change_email(
            application.user, 
            application, 
            old_status, 
            new_status, 
            comment
        )
        
        db.session.commit()
