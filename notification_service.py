# Service de gestion des notifications pour le système e-consulaire
from app import db
from models import Notification, User, Application, UniteConsulaire
from datetime import datetime
from email_service import email_service

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, type_notification, title, message, reference_id=None):
        """Créer une nouvelle notification"""
        notification = Notification(
            user_id=user_id,
            type_notification=type_notification,
            title=title,
            message=message,
            reference_id=reference_id
        )
        db.session.add(notification)
        return notification
    
    @staticmethod
    def notify_new_application(application):
        """Notifier tous les agents de l'unité consulaire qu'une nouvelle demande est arrivée"""
        # Envoyer email de confirmation à l'usager
        email_service.send_application_received_email(application.user, application)
        
        # Récupérer tous les agents de l'unité consulaire
        agents = User.query.filter_by(
            unite_consulaire_id=application.unite_consulaire_id,
            role='agent',
            active=True
        ).all()
        
        for agent in agents:
            # Notification dans l'interface
            NotificationService.create_notification(
                user_id=agent.id,
                type_notification='nouvelle_demande',
                title=f'Nouvelle demande: {application.service_type}',
                message=f'Demande {application.reference_number} reçue de {application.user.get_full_name()}',
                reference_id=application.id
            )
            
            # Email à l'agent
            email_service.send_new_application_email_to_agent(agent, application)
        
        # Notifier aussi l'admin de l'unité s'il existe
        admin = User.query.filter_by(
            unite_consulaire_id=application.unite_consulaire_id,
            role='admin',
            active=True
        ).first()
        
        if admin:
            NotificationService.create_notification(
                user_id=admin.id,
                type_notification='nouvelle_demande_admin',
                title=f'Nouvelle demande dans votre unité',
                message=f'Demande {application.reference_number} pour {application.service_type}',
                reference_id=application.id
            )
    
    @staticmethod
    def notify_application_status_change(application, old_status, new_status, comment=None):
        """Notifier l'usager d'un changement de statut de sa demande"""
        status_messages = {
            'en_traitement': 'Votre demande est maintenant en cours de traitement.',
            'validee': 'Votre demande a été approuvée !',
            'rejetee': 'Votre demande a été rejetée.',
            'documents_requis': 'Des documents supplémentaires sont requis.',
            'pret_pour_retrait': 'Votre document est prêt pour retrait.',
            'cloture': 'Votre dossier a été clôturé.'
        }
        
        message = status_messages.get(new_status, f'Statut de votre demande changé: {new_status}')
        
        if comment:
            message += f' Commentaire: {comment}'
        
        # Notification dans l'interface
        NotificationService.create_notification(
            user_id=application.user_id,
            type_notification='demande_traitee',
            title=f'Demande {application.reference_number}',
            message=message,
            reference_id=application.id
        )
        
        # Email à l'usager
        email_service.send_status_change_email(
            application.user, 
            application, 
            old_status, 
            new_status, 
            comment
        )
    
    @staticmethod
    def notify_payment_required(application):
        """Notifier l'usager qu'un paiement est requis"""
        NotificationService.create_notification(
            user_id=application.user_id,
            type_notification='paiement_requis',
            title=f'Paiement requis - {application.reference_number}',
            message=f'Votre demande nécessite un paiement de {application.payment_amount}.',
            reference_id=application.id
        )
    
    @staticmethod
    def notify_document_ready(application):
        """Notifier l'usager que son document est prêt"""
        NotificationService.create_notification(
            user_id=application.user_id,
            type_notification='document_pret',
            title=f'Document prêt - {application.reference_number}',
            message='Votre document consulaire est prêt pour récupération.',
            reference_id=application.id
        )
    
    @staticmethod
    def notify_admin_service_configured(admin_id, service_name, unit_name):
        """Notifier qu'un service a été configuré dans l'unité"""
        NotificationService.create_notification(
            user_id=admin_id,
            type_notification='service_configure',
            title=f'Service configuré',
            message=f'Le service "{service_name}" a été configuré pour {unit_name}.',
            reference_id=None
        )
    
    @staticmethod
    def mark_notification_as_read(notification_id, user_id):
        """Marquer une notification comme lue"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.lu = True
            notification.lu_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_notifications_as_read(user_id):
        """Marquer toutes les notifications d'un utilisateur comme lues"""
        Notification.query.filter_by(
            user_id=user_id,
            lu=False
        ).update({
            'lu': True,
            'lu_at': datetime.utcnow()
        })
        db.session.commit()
    
    @staticmethod
    def get_unread_count(user_id):
        """Obtenir le nombre de notifications non lues pour un utilisateur"""
        return Notification.query.filter_by(
            user_id=user_id,
            lu=False
        ).count()
    
    @staticmethod
    def clean_old_notifications(days=30):
        """Nettoyer les anciennes notifications (par défaut 30 jours)"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_notifications = Notification.query.filter(
            Notification.created_at < cutoff_date,
            Notification.lu.is_(True)
        ).all()
        
        for notif in old_notifications:
            db.session.delete(notif)
        
        db.session.commit()
        return len(old_notifications)