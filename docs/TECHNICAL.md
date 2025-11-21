# Documentation Technique - e-Consulaire RDC

## Architecture du Projet

### Vue d'ensemble

e-Consulaire RDC est une application web Flask permettant la gestion des services consulaires de la République Démocratique du Congo. Le système permet aux citoyens de soumettre des demandes de documents consulaires en ligne et aux agents consulaires de traiter ces demandes.

### Stack Technologique

- **Backend**: Python 3.11+ avec Flask
- **Base de données**: PostgreSQL (Neon pour Replit)
- **ORM**: SQLAlchemy avec Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Email**: Flask-Mail avec SendGrid
- **PDF Generation**: ReportLab
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Tailwind CSS
- **Déploiement**: Gunicorn (WSGI server)

## Structure du Projet

```
workspace/
├── app.py                      # Point d'entrée de l'application Flask
├── main.py                     # Script principal pour lancer le serveur
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py          # Modèles SQLAlchemy
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── routes.py          # Routes publiques et auth
│   │   ├── routes_admin.py    # Routes administrateur
│   │   ├── routes_agent.py    # Routes agent consulaire
│   │   ├── routes_superviseur.py # Routes superviseur
│   │   └── routes_crud.py     # API CRUD
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py   # Service d'envoi d'emails
│   │   ├── notification_service.py # Service de notifications
│   │   └── security_service.py # Service de sécurité
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py         # Fonctions utilitaires
│   │   └── middleware.py      # Middleware de sécurité
│   ├── scripts/
│   │   ├── init_db.py         # Initialisation de la BD
│   │   └── demo_data.py       # Données de démonstration
│   ├── forms.py               # Formulaires WTForms
│   └── config.py              # Configuration
├── templates/                  # Templates Jinja2
├── static/                     # Fichiers statiques (CSS, JS, images)
├── uploads/                    # Fichiers uploadés
└── docs/                       # Documentation

```

## Modèles de Données

### User
Représente un utilisateur du système (citoyens, agents, superviseurs)

**Champs principaux:**
- `id`: Identifiant unique
- `username`: Nom d'utilisateur unique
- `email`: Email unique
- `password_hash`: Hash du mot de passe
- `role`: Type d'utilisateur (usager, agent, superviseur, admin)
- `active`: Statut actif/inactif
- `unite_consulaire_id`: Unité consulaire de rattachement (pour agents)

**Rôles:**
- `usager`: Citoyen demandeur
- `agent`: Agent consulaire
- `superviseur`: Superviseur système
- `admin`: Administrateur unité

### Application
Représente une demande de service consulaire

**Champs principaux:**
- `id`: Identifiant unique
- `user_id`: Utilisateur demandeur
- `unite_consulaire_id`: Unité consulaire traitante
- `service_type`: Type de service demandé
- `reference_number`: Numéro de référence unique
- `status`: Statut de la demande
- `form_data`: Données du formulaire (JSON)
- `payment_status`: Statut du paiement

**Statuts possibles:**
- `soumise`: Demande soumise
- `en_traitement`: En cours de traitement
- `validee`: Demande validée
- `rejetee`: Demande rejetée
- `documents_requis`: Documents supplémentaires requis
- `pret_pour_retrait`: Prêt pour retrait
- `cloture`: Dossier clôturé

### UniteConsulaire
Représente une ambassade ou un consulat

**Champs principaux:**
- `id`: Identifiant unique
- `nom`: Nom de l'unité
- `type`: Type (ambassade, consulat)
- `ville`: Ville
- `pays`: Pays
- `email_principal`: Email de contact
- `telephone_principal`: Téléphone de contact
- `active`: Statut actif/inactif

### Service
Représente un type de service consulaire

**Services disponibles:**
- Carte Consulaire
- Attestation de Prise en Charge
- Légalisations
- Passeport
- État Civil
- Procuration
- Autres Documents

### Document
Fichiers attachés à une demande

### StatusHistory
Historique des changements de statut d'une demande

### AuditLog
Journal d'audit des actions dans le système

### Notification
Notifications pour les utilisateurs

## Services

### EmailService
Gestion de l'envoi d'emails via SendGrid

**Méthodes principales:**
- `send_email()`: Envoi d'email simple
- `send_template_email()`: Envoi avec template
- `send_notification_email()`: Email de notification

### NotificationService
Création et gestion des notifications utilisateur

**Méthodes principales:**
- `create_notification()`: Créer une notification
- `mark_as_read()`: Marquer comme lue
- `get_user_notifications()`: Récupérer les notifications d'un utilisateur

### SecurityService
Services de sécurité

**Fonctionnalités:**
- Protection CSRF
- Rate limiting
- Sanitization des entrées
- Logging des événements de sécurité
- Génération de tokens sécurisés

## Routes et Endpoints

### Routes Publiques (`/`)
- `GET /`: Page d'accueil (redirige vers login)
- `GET /login`: Page de connexion utilisateur
- `POST /login`: Traitement de connexion
- `GET /register`: Page d'inscription
- `POST /register`: Traitement d'inscription
- `GET /logout`: Déconnexion

### Routes Usager (`/dashboard`)
- `GET /dashboard`: Tableau de bord utilisateur
- `GET /profile`: Profil utilisateur
- `POST /profile/update`: Mise à jour du profil
- `GET /applications`: Liste des demandes
- `GET /applications/<id>`: Détail d'une demande
- `POST /services/*`: Soumission de demandes

### Routes Agent (`/agent/*`)
- `GET /agent/my-unit`: Tableau de bord agent
- `GET /agent/applications`: Demandes à traiter
- `POST /agent/process/<id>`: Traiter une demande

### Routes Superviseur (`/superviseur/*`)
- `GET /superviseur/dashboard`: Tableau de bord superviseur
- `GET /superviseur/users`: Gestion des utilisateurs
- `POST /superviseur/users/create`: Créer un utilisateur
- `GET /superviseur/unites`: Gestion des unités
- `GET /superviseur/services`: Configuration des services
- `GET /superviseur/security`: Tableau de bord sécurité

### API CRUD (`/api/*`)
- Endpoints RESTful pour la gestion des données
- Format: JSON
- Authentification requise

## Sécurité

### Authentification
- Utilisation de Flask-Login pour la gestion des sessions
- Mots de passe hashés avec Werkzeug (PBKDF2)
- Sessions sécurisées avec secret key

### Protection CSRF
- Token CSRF sur tous les formulaires
- Validation automatique via Flask-WTF
- Headers de sécurité configurés

### Rate Limiting
- Limitation du nombre de requêtes par IP
- Protection contre les attaques par force brute

### Sanitization
- Nettoyage automatique des entrées utilisateur
- Protection contre XSS et injection SQL
- Validation des données avec WTForms

### Headers de Sécurité
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'...
```

## Configuration

### Variables d'Environnement

**Base de données:**
- `DATABASE_URL`: URL de connexion PostgreSQL

**Email:**
- `MAIL_SERVER`: Serveur SMTP (défaut: smtp.gmail.com)
- `MAIL_PORT`: Port SMTP (défaut: 587)
- `MAIL_USERNAME`: Nom d'utilisateur email
- `MAIL_PASSWORD`: Mot de passe email
- `MAIL_DEFAULT_SENDER`: Expéditeur par défaut
- `SENDGRID_API_KEY`: Clé API SendGrid

**Sécurité:**
- `SESSION_SECRET`: Clé secrète pour les sessions
- `ENCRYPTION_KEY`: Clé de chiffrement

**Application:**
- `FLASK_ENV`: Environnement (development, production)
- `ENVIRONMENT`: Environnement système

## Base de Données

### Initialisation
```bash
python backend/scripts/init_db.py
```

Cette commande:
1. Crée toutes les tables
2. Initialise les services par défaut
3. Crée un compte administrateur par défaut

### Données de Démonstration
```bash
python backend/scripts/demo_data.py
```

Cette commande crée:
- 3 unités consulaires (Maroc, France, Belgique)
- Agents et utilisateurs de test
- Demandes exemple avec différents statuts
- Notifications de démonstration

### Migrations

Pour les modifications de schéma en production, utiliser un outil de migration comme Flask-Migrate ou Alembic.

## Tests

### Tests Manuels
1. Créer les données de test: `python backend/scripts/demo_data.py`
2. Connexion avec différents rôles
3. Vérifier les workflows complets

### Comptes de Test
Après exécution de `demo_data.py`:
- **Superviseur**: admin@diplomatie.gouv.cd / admin123
- **Agent Rabat**: agent.rabat@diplomatie.gouv.cd / agent123
- **Agent Paris**: agent.paris@diplomatie.gouv.cd / agent123
- **Usager 1**: demo.user1@example.com / user123
- **Usager 2**: demo.user2@example.com / user123

## Performance

### Optimisations Base de Données
- Pool de connexions configuré (10 connexions, 20 overflow)
- Pre-ping activé pour vérifier les connexions
- Pool recycling après 300 secondes

### Optimisations Frontend
- Fichiers CSS/JS minifiés
- Images optimisées
- Lazy loading des ressources

## Maintenance

### Logs
Les logs sont générés automatiquement et incluent:
- Logs d'application (app.log)
- Logs d'erreur
- Journal d'audit (AuditLog table)

### Sauvegarde
- Sauvegardes automatiques de la base de données
- Export régulier des données critiques

### Monitoring
- Surveillance des erreurs
- Suivi des performances
- Alertes de sécurité

## Dépannage

### Problèmes Courants

**Erreur de connexion à la base de données:**
- Vérifier DATABASE_URL
- Vérifier que PostgreSQL est accessible
- Vérifier les credentials

**Emails non envoyés:**
- Vérifier SENDGRID_API_KEY
- Vérifier les paramètres SMTP
- Consulter les logs d'erreur

**Erreurs 500:**
- Consulter les logs d'application
- Vérifier les variables d'environnement
- Vérifier les migrations de BD

**Sessions perdues:**
- Vérifier SESSION_SECRET
- Vérifier la configuration des cookies
- Vérifier le stockage de session

## Support et Contact

Pour toute question technique:
- Documentation: /docs
- Logs: Consulter les fichiers de log
- Support: Contacter l'équipe technique
