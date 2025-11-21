# e-Consulaire RDC - Système de Services Consulaires

[![🇺🇸 English](https://img.shields.io/badge/🇺🇸-English-blue?style=for-the-badge)](README_EN.md) [![🇫🇷 Français](https://img.shields.io/badge/🇫🇷-Français-red?style=for-the-badge&color=red)](README.md)

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API](#api)
- [Sécurité](#sécurité)
- [Contribution](#contribution)
- [Licence](#licence)

## 🌍 Vue d'ensemble

**e-Consulaire RDC** est une plateforme numérique complète pour les services consulaires de la République Démocratique du Congo. Cette application permet aux citoyens d'accéder en ligne à divers services consulaires et aux agents diplomatiques de gérer efficacement les demandes.

### ✨ Caractéristiques principales

- **🏛️ Système hiérarchique** : Gestion multi-niveaux (Superviseur → Admin → Agent → Usager)
- **🌐 Multi-unités** : Support pour ambassades, consulats et missions diplomatiques
- **🔐 Sécurité renforcée** : Chiffrement AES-256, authentification multi-facteurs
- **📧 Notifications automatiques** : SendGrid pour les communications
- **💳 Paiements intégrés** : Support pour les transactions sécurisées
- **📊 Tableau de bord avancé** : Statistiques et suivi en temps réel

## 🎯 Fonctionnalités

### 👥 Gestion des utilisateurs
- **Superviseur Système** : Gestion globale, création d'unités consulaires
- **Administrateur** : Gestion locale, configuration des services
- **Agent Consulaire** : Traitement des demandes, validation des documents
- **Usager** : Soumission de demandes, suivi du statut

### 📄 Services consulaires
- **Carte consulaire** ($50 USD)
- **Attestation de prise en charge** ($25 USD)
- **Légalisation de documents** ($30-50 USD selon urgence)
- **Pré-demande de passeport** ($100 USD)
- **Autres documents officiels** ($20 USD)

### 🏢 Gestion des unités
- Création et configuration d'ambassades/consulats
- Assignation d'agents par unité géographique
- Tarification variable par unité consulaire
- Routage automatique basé sur la géolocalisation

## 🏗️ Architecture

### Stack technologique
- **Backend** : Flask (Python 3.11)
- **Base de données** : PostgreSQL avec SQLAlchemy ORM
- **Frontend** : HTML5, Tailwind CSS, JavaScript
- **Email** : SendGrid API
- **Sécurité** : bcrypt, cryptography, JWT
- **Serveur** : Gunicorn avec support de rechargement

### Structure de la base de données

```sql
-- Modèles principaux
User                    -- Utilisateurs du système
UniteConsulaire        -- Ambassades/Consulats
Service               -- Services consulaires
Application           -- Demandes des usagers
Document              -- Fichiers joints
AuditLog              -- Journal d'audit
Notification          -- Notifications utilisateur

-- Relations
UniteConsulaire_Service -- Services par unité avec tarifs
StatusHistory          -- Historique des statuts
```

### Architecture de sécurité
- **Chiffrement** : AES-256 pour les données sensibles
- **Authentification** : Sessions sécurisées avec Flask-Login
- **Autorisation** : RBAC (Role-Based Access Control)
- **Audit** : Traçabilité complète des actions utilisateur

## 🚀 Installation

### Prérequis
- Python 3.11+
- PostgreSQL 12+
- Git

### Installation rapide

```bash
# Cloner le dépôt
git clone https://github.com/votre-org/e-consulaire-rdc.git
cd e-consulaire-rdc

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Initialiser la base de données
python backend/scripts/init_db.py

# (Optionnel) Créer des données de démonstration
python backend/scripts/demo_data.py

# Démarrer l'application
python main.py
# Ou en production:
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## ⚙️ Configuration

### Variables d'environnement requises

```bash
# Base de données
DATABASE_URL=postgresql://user:password@localhost/e_consulaire

# Sécurité
SESSION_SECRET=votre_clé_secrète_très_sécurisée
ENCRYPTION_KEY=votre_clé_chiffrement_32_caractères

# Email (SendGrid)
SENDGRID_API_KEY=votre_clé_sendgrid

# PostgreSQL (auto-configuré sur Replit)
PGHOST=localhost
PGPORT=5432
PGUSER=votre_utilisateur
PGPASSWORD=votre_mot_de_passe
PGDATABASE=e_consulaire
```

### Configuration des unités consulaires

```python
# Exemples d'unités pré-configurées
unites = [
    {
        "nom": "Ambassade de la RD Congo au Maroc",
        "type_unite": "Ambassade",
        "pays": "Maroc",
        "ville": "Rabat",
        "email": "ambassade@rdcongo-maroc.org"
    },
    {
        "nom": "Consulat Général à Bruxelles",
        "type_unite": "Consulat",
        "pays": "Belgique", 
        "ville": "Bruxelles",
        "email": "consulat@rdcongo-belgique.be"
    }
]
```

## 💻 Utilisation

### Accès aux interfaces

- **Usagers** : `/login` - Interface citoyens
- **Agents** : `/consulate` - Interface consulaire
- **Admins/Superviseurs** : `/admin` - Interface administration

### Workflow de demande

1. **Soumission** : L'usager remplit le formulaire en ligne
2. **Validation** : Upload des documents requis
3. **Paiement** : Transaction sécurisée
4. **Traitement** : Révision par l'agent consulaire
5. **Approbation** : Validation finale
6. **Génération** : Document officiel avec QR code

### API REST

```python
# Découverte d'unités par géolocalisation
GET /api/units-by-location?country=France&city=Paris

# Services disponibles par unité
GET /api/unit-services/1

# Soumission de demande
POST /api/applications
{
    "service_id": 1,
    "unite_consulaire_id": 2,
    "personal_data": {...},
    "documents": [...]
}
```

## 🔒 Sécurité

### Mesures de protection
- **Chiffrement de bout en bout** : Toutes les données sensibles
- **Sessions sécurisées** : Expiration automatique
- **Validation côté serveur** : Protection CSRF/XSS
- **Audit complet** : Traçabilité de toutes les actions
- **Backup automatique** : Sauvegarde et restauration

### Conformité
- **RGPD** : Protection des données personnelles
- **Standards diplomatiques** : Sécurité consulaire internationale
- **PCI DSS** : Sécurité des paiements (si applicable)

## 🤝 Contribution

### Processus de développement

```bash
# Créer une branche feature
git checkout -b feature/nouvelle-fonctionnalite

# Développer et tester
python -m pytest tests/

# Soumettre une pull request
git push origin feature/nouvelle-fonctionnalite
```

### Standards de code
- **PEP 8** : Style de code Python
- **Type hints** : Annotations de type
- **Docstrings** : Documentation des fonctions
- **Tests unitaires** : Couverture > 80%

## 📊 Statut du projet

### ✅ Fonctionnalités complétées
- Architecture hiérarchique complète
- CRUD pour toutes les entités
- Système d'authentification robuste
- Interface utilisateur moderne
- Base de données PostgreSQL optimisée

### 🚧 En développement
- Module de paiement intégré
- Application mobile complémentaire
- API REST publique
- Dashboard analytique avancé

### 🎯 Prochaines versions
- **v2.0** : Module de paiement Stripe
- **v2.1** : API REST complète
- **v2.2** : Application mobile iOS/Android
- **v3.0** : Intelligence artificielle pour validation automatique

## 📝 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

### Contact technique
- **Email** : support@diplomatie.gouv.cd
- **Documentation** : [Wiki du projet](https://github.com/votre-org/e-consulaire-rdc/wiki)
- **Issues** : [GitHub Issues](https://github.com/votre-org/e-consulaire-rdc/issues)

### Équipe de développement
- **Lead Developer** : [Nom du développeur principal]
- **DevOps** : [Nom DevOps]
- **UI/UX** : [Nom Designer]

---

**Développé avec ❤️ pour la République Démocratique du Congo**

[![🇺🇸 English Version](https://img.shields.io/badge/🇺🇸-Read%20in%20English-blue?style=for-the-badge)](README_EN.md)