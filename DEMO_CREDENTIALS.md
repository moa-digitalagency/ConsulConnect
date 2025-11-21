# 🔐 Comptes de Démonstration - e-Consulaire RDC

## 📌 Information Importante

L'application a **DEUX portails de connexion séparés** :

1. **`/login`** - Pour les CITOYENS (usagers)
2. **`/admin`** - Pour le PERSONNEL CONSULAIRE (superviseur, admin, agents)

---

## 👨‍💼 COMPTE SUPERVISEUR SYSTÈME

**Rôle** : Superviseur - Accès complet au système

- **URL de connexion** : `/admin`
- **Email** : `admin@diplomatie.gouv.cd`
- **Mot de passe** : `admin123`
- **Accès** : Dashboard superviseur, gestion globale

**Fonctionnalités disponibles :**
- ✅ Vue d'ensemble système complète
- ✅ Gestion des utilisateurs (créer, modifier, désactiver)
- ✅ Gestion des unités consulaires
- ✅ Configuration des services
- ✅ Tableau de bord sécurité
- ✅ Audit logs complets
- ✅ Statistiques globales

---

## 🏛️ COMPTES AGENTS CONSULAIRES

### Agent - Ambassade RDC Maroc (Rabat)

- **URL de connexion** : `/admin`
- **Email** : `agent.rabat@diplomatie.gouv.cd`
- **Mot de passe** : `agent123`
- **Unité** : Ambassade de la RD Congo au Maroc (Rabat)
- **Rôle** : Agent consulaire

**Fonctionnalités disponibles :**
- ✅ Tableau de bord de l'unité
- ✅ Liste des demandes de son unité
- ✅ Traitement des demandes (valider, rejeter, demander documents)
- ✅ Gestion des rendez-vous
- ✅ Statistiques de l'unité

### Agent - Consulat RDC France (Paris)

- **URL de connexion** : `/admin`
- **Email** : `agent.paris@diplomatie.gouv.cd`
- **Mot de passe** : `agent123`
- **Unité** : Consulat Général de la RD Congo en France (Paris)
- **Rôle** : Agent consulaire

**Fonctionnalités disponibles :**
- ✅ Tableau de bord de l'unité
- ✅ Liste des demandes de son unité
- ✅ Traitement des demandes
- ✅ Gestion des rendez-vous
- ✅ Statistiques de l'unité

---

## 👨‍👩‍👧‍👦 COMPTES CITOYENS (USAGERS)

### Citoyen 1 - Jean Kalala

- **URL de connexion** : `/login` (PAS /admin !)
- **Email** : `demo.user1@example.com`
- **Mot de passe** : `user123`
- **Profil** : Citoyen congolais résidant à Rabat, Maroc
- **Unité** : Ambassade RDC Maroc

**Fonctionnalités disponibles :**
- ✅ Tableau de bord personnel
- ✅ Soumettre de nouvelles demandes
- ✅ Suivre l'état des demandes
- ✅ Télécharger documents
- ✅ Voir les notifications
- ✅ Mettre à jour le profil

**Demandes actives :**
- Carte Consulaire (soumise)
- Attestation de Prise en Charge (en_traitement)
- Légalisations (validee)

### Citoyen 2 - Marie Tshisekedi

- **URL de connexion** : `/login` (PAS /admin !)
- **Email** : `demo.user2@example.com`
- **Mot de passe** : `user123`
- **Profil** : Citoyenne congolaise résidant à Paris, France
- **Unité** : Consulat RDC France

**Fonctionnalités disponibles :**
- ✅ Tableau de bord personnel
- ✅ Soumettre de nouvelles demandes
- ✅ Suivre l'état des demandes
- ✅ Télécharger documents
- ✅ Voir les notifications
- ✅ Mettre à jour le profil

**Demandes actives :**
- Carte Consulaire (soumise)
- Attestation de Prise en Charge (en_traitement)
- Légalisations (validee)

---

## 📋 SERVICES CONSULAIRES DISPONIBLES

1. **Carte Consulaire** - $50 USD (5 jours)
2. **Attestation de Prise en Charge** - $25 USD (3 jours)
3. **Légalisations** - $30 USD (7 jours)
4. **Passeport** - $100 USD (14 jours)
5. **État Civil** - $35 USD (10 jours)
6. **Procuration** - $40 USD (5 jours)
7. **Autres Documents** - $20 USD (5 jours)

---

## 🏢 UNITÉS CONSULAIRES CONFIGURÉES

### 1. Ambassade de la RD Congo au Maroc
- **Ville** : Rabat
- **Pays** : Maroc
- **Email** : ambassade.rabat@diplomatie.gouv.cd
- **Téléphone** : +212-537-751234
- **Agent** : agent.rabat@diplomatie.gouv.cd

### 2. Consulat Général de la RD Congo en France
- **Ville** : Paris
- **Pays** : France
- **Email** : consulat.paris@diplomatie.gouv.cd
- **Téléphone** : +33-1-42-123456
- **Agent** : agent.paris@diplomatie.gouv.cd

### 3. Ambassade de la RD Congo en Belgique
- **Ville** : Bruxelles
- **Pays** : Belgique
- **Email** : ambassade.bruxelles@diplomatie.gouv.cd
- **Téléphone** : +32-2-345-6789
- **Agent** : (à créer)

---

## 🔄 WORKFLOW DE TEST COMPLET

### Test 1 : Parcours Citoyen

1. **Connexion** : Aller sur `/login`
   - Email : `demo.user1@example.com`
   - Mot de passe : `user123`

2. **Dashboard** : Voir vos demandes en cours

3. **Nouvelle demande** : Soumettre une demande de passeport
   - Remplir le formulaire
   - Télécharger documents requis
   - Soumettre

4. **Suivi** : Suivre l'état de la demande

5. **Notifications** : Vérifier les notifications

### Test 2 : Parcours Agent Consulaire

1. **Connexion** : Aller sur `/admin`
   - Email : `agent.rabat@diplomatie.gouv.cd`
   - Mot de passe : `agent123`

2. **Dashboard Unité** : Voir les demandes à traiter

3. **Traiter une demande** :
   - Ouvrir une demande "soumise"
   - Vérifier les documents
   - Valider ou demander des documents supplémentaires

4. **Statistiques** : Voir les statistiques de l'unité

### Test 3 : Parcours Superviseur

1. **Connexion** : Aller sur `/admin`
   - Email : `admin@diplomatie.gouv.cd`
   - Mot de passe : `admin123`

2. **Gestion Utilisateurs** : Créer un nouvel agent
   - Nom, email, mot de passe
   - Assigner à une unité

3. **Gestion Unités** : Créer une nouvelle unité consulaire

4. **Configuration Services** : Modifier tarifs

5. **Sécurité** : Consulter les logs d'audit

---

## ⚠️ NOTES IMPORTANTES

### Sécurité
- **CHANGEZ TOUS LES MOTS DE PASSE** en production
- Les mots de passe par défaut sont : `admin123` et `user123`
- Session secret et encryption key doivent être configurés

### Portails de Connexion
- **Citoyens** → `/login`
- **Personnel** → `/admin`
- Ne confondez pas les deux !

### Premier Démarrage
```bash
# 1. Initialiser la base de données
python backend/scripts/init_db.py

# 2. Créer les données de démonstration
python backend/scripts/demo_data.py

# 3. Lancer l'application
python main.py
```

### Réinitialisation
Pour réinitialiser complètement la base :
```bash
# Option 1 : Via SQL (si PostgreSQL)
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Option 2 : Supprimer les tables manuellement
# Puis relancer init_db.py et demo_data.py
```

---

## 📞 Support

Pour toute question :
- Documentation technique : `docs/TECHNICAL.md`
- Guide de déploiement : `docs/DEPLOYMENT.md`
- README : `README.md` (FR) ou `README_EN.md` (EN)

---

**Développé pour la République Démocratique du Congo 🇨🇩**

*Date de génération : 21 Novembre 2025*
