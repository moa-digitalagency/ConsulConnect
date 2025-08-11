import os
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from flask_mail import Message
from app import mail, app
from models import AuditLog, db
from flask import request

def generate_pdf_document(application):
    """Generate official PDF document for approved applications"""
    try:
        # Create filename
        filename = f"document_{application.reference_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        story.append(Paragraph("RÉPUBLIQUE DÉMOCRATIQUE DU CONGO", title_style))
        story.append(Paragraph("MINISTÈRE DES AFFAIRES ÉTRANGÈRES", styles['Heading2']))
        story.append(Paragraph("SERVICES CONSULAIRES", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Document title based on service type
        service_titles = {
            'carte_consulaire': 'CARTE CONSULAIRE',
            'attestation_prise_charge': 'ATTESTATION DE PRISE EN CHARGE',
            'legalisations': 'CERTIFICAT DE LÉGALISATION',
            'passeport': 'REÇU DE PRÉ-DEMANDE DE PASSEPORT',
            'autres_documents': 'DOCUMENT OFFICIEL'
        }
        
        doc_title = service_titles.get(application.service_type, 'DOCUMENT OFFICIEL')
        story.append(Paragraph(doc_title, title_style))
        story.append(Spacer(1, 20))
        
        # Reference and date
        story.append(Paragraph(f"<b>Référence:</b> {application.reference_number}", styles['Normal']))
        story.append(Paragraph(f"<b>Date d'émission:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # User information
        user = application.user
        story.append(Paragraph("<b>INFORMATIONS DU DEMANDEUR</b>", styles['Heading3']))
        
        user_data = [
            ['Nom complet:', f"{user.first_name} {user.last_name}"],
            ['Email:', user.email],
            ['Téléphone:', user.phone or 'Non renseigné']
        ]
        
        user_table = Table(user_data, colWidths=[2*inch, 3*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(user_table)
        story.append(Spacer(1, 20))
        
        # Service-specific content
        if application.form_data:
            import json
            form_data = json.loads(application.form_data)
            
            story.append(Paragraph("<b>DÉTAILS DE LA DEMANDE</b>", styles['Heading3']))
            
            for key, value in form_data.items():
                if value:
                    readable_key = key.replace('_', ' ').title()
                    story.append(Paragraph(f"<b>{readable_key}:</b> {value}", styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Status and validation
        story.append(Paragraph("<b>STATUT</b>", styles['Heading3']))
        story.append(Paragraph(f"Statut: {application.get_status_display()}", styles['Normal']))
        story.append(Paragraph(f"Traité par: Agent consulaire", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Generate QR code for verification
        qr_data = f"REF:{application.reference_number}|USER:{user.email}|DATE:{datetime.now().strftime('%Y%m%d')}"
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f"qr_{application.reference_number}.png")
        qr_img.save(qr_path)
        
        # Add QR code to document
        story.append(Paragraph("<b>Code de vérification:</b>", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Image(qr_path, width=1*inch, height=1*inch))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Ce document est authentifié par un code QR de vérification.", styles['Italic']))
        story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Italic']))
        
        # Build PDF
        doc.build(story)
        
        # Clean up QR code file
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        return pdf_path
        
    except Exception as e:
        app.logger.error(f"Error generating PDF: {e}")
        return None

def send_notification_email(recipient, subject, body):
    """Send notification email to user"""
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        return False

def log_audit(user_id, action, resource, resource_id, details=None):
    """Log audit trail"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error logging audit: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except:
        return 0
