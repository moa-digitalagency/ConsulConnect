# Guide de Déploiement - e-Consulaire RDC

## Table des Matières
1. [Prérequis](#prérequis)
2. [Déploiement sur Replit](#déploiement-sur-replit)
3. [Déploiement en Production](#déploiement-en-production)
4. [Configuration](#configuration)
5. [Post-Déploiement](#post-déploiement)
6. [Maintenance](#maintenance)

## Prérequis

### Logiciels Requis
- Python 3.11 ou supérieur
- PostgreSQL 12 ou supérieur
- Serveur SMTP ou compte SendGrid

### Compétences Requises
- Connaissance de base de Linux/Unix
- Compréhension des applications web
- Gestion de base de données

## Déploiement sur Replit

### Configuration Initiale

1. **Créer un nouveau Repl**
   - Sélectionner Python comme langage
   - Importer le dépôt Git ou copier les fichiers

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer la base de données**
   - Replit fournit automatiquement une base PostgreSQL
   - La variable `DATABASE_URL` est automatiquement configurée

4. **Configurer les variables d'environnement**
   Dans les Secrets de Replit, ajouter:
   ```
   SESSION_SECRET=<générer-une-clé-secrète>
   MAIL_USERNAME=<votre-email>
   MAIL_PASSWORD=<votre-mot-de-passe>
   SENDGRID_API_KEY=<votre-clé-sendgrid>
   ```

5. **Initialiser la base de données**
   ```bash
   python backend/scripts/init_db.py
   ```

6. **Créer des données de démonstration (optionnel)**
   ```bash
   python backend/scripts/demo_data.py
   ```

7. **Lancer l'application**
   - Cliquer sur "Run" ou exécuter `python main.py`
   - L'application sera accessible à l'URL Replit fournie

### Publication sur Replit

1. **Configurer le déploiement**
   - Utiliser le fichier `.replit` déjà configuré
   - Le déploiement utilise Gunicorn en production

2. **Publier l'application**
   - Cliquer sur "Deploy" dans l'interface Replit
   - Choisir "Autoscale Deployment"
   - Configurer le domaine personnalisé si souhaité

## Déploiement en Production

### Option 1: Serveur VPS (Ubuntu/Debian)

#### 1. Préparation du Serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Python et dépendances
sudo apt install python3.11 python3.11-venv python3-pip postgresql nginx -y

# Installation de certbot pour HTTPS
sudo apt install certbot python3-certbot-nginx -y
```

#### 2. Configuration PostgreSQL

```bash
# Connexion à PostgreSQL
sudo -u postgres psql

# Création de la base de données et de l'utilisateur
CREATE DATABASE econsular_db;
CREATE USER econsular_user WITH PASSWORD 'votre-mot-de-passe-sécurisé';
GRANT ALL PRIVILEGES ON DATABASE econsular_db TO econsular_user;
\q
```

#### 3. Déploiement de l'Application

```bash
# Créer un utilisateur système
sudo useradd -m -s /bin/bash econsular
sudo su - econsular

# Cloner le dépôt
git clone https://github.com/votre-repo/econsular.git
cd econsular

# Créer un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pip install gunicorn

# Créer le fichier de configuration
cat > .env << EOF
DATABASE_URL=postgresql://econsular_user:votre-mot-de-passe@localhost/econsular_db
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
ENVIRONMENT=production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=votre-email@diplomatie.gouv.cd
MAIL_PASSWORD=votre-mot-de-passe-app
SENDGRID_API_KEY=votre-clé-sendgrid
EOF

# Initialiser la base de données
python backend/scripts/init_db.py
```

#### 4. Configuration Systemd

```bash
# Retour en utilisateur root
exit

# Créer le service systemd
sudo nano /etc/systemd/system/econsular.service
```

Contenu du fichier:
```ini
[Unit]
Description=e-Consulaire RDC Application
After=network.target postgresql.service

[Service]
Type=notify
User=econsular
Group=econsular
WorkingDirectory=/home/econsular/econsular
Environment="PATH=/home/econsular/econsular/venv/bin"
EnvironmentFile=/home/econsular/econsular/.env
ExecStart=/home/econsular/econsular/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable econsular
sudo systemctl start econsular
sudo systemctl status econsular
```

#### 5. Configuration Nginx

```bash
# Créer la configuration Nginx
sudo nano /etc/nginx/sites-available/econsular
```

Contenu du fichier:
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Logs
    access_log /var/log/nginx/econsular_access.log;
    error_log /var/log/nginx/econsular_error.log;

    # Limite de taille des uploads
    client_max_body_size 20M;

    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Fichiers statiques
    location /static {
        alias /home/econsular/econsular/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers uploads
    location /uploads {
        alias /home/econsular/econsular/uploads;
        internal;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/econsular /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Configurer HTTPS avec Let's Encrypt
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

### Option 2: Docker

#### 1. Créer le Dockerfile

```dockerfile
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p uploads

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "main:app"]
```

#### 2. Créer docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: econsular_db
      POSTGRES_USER: econsular_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://econsular_user:${DB_PASSWORD}@db:5432/econsular_db
      SESSION_SECRET: ${SESSION_SECRET}
      FLASK_ENV: production
      ENVIRONMENT: production
      MAIL_SERVER: ${MAIL_SERVER}
      MAIL_PORT: ${MAIL_PORT}
      MAIL_USERNAME: ${MAIL_USERNAME}
      MAIL_PASSWORD: ${MAIL_PASSWORD}
      SENDGRID_API_KEY: ${SENDGRID_API_KEY}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 3. Déployer avec Docker

```bash
# Créer le fichier .env
cat > .env << EOF
DB_PASSWORD=votre-mot-de-passe-db
SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=votre-email@diplomatie.gouv.cd
MAIL_PASSWORD=votre-mot-de-passe
SENDGRID_API_KEY=votre-clé-sendgrid
EOF

# Construire et lancer
docker-compose up -d

# Initialiser la base de données
docker-compose exec web python backend/scripts/init_db.py
```

## Configuration

### Génération de Clés Secrètes

```python
# Générer SESSION_SECRET
import secrets
print(secrets.token_hex(32))

# Générer ENCRYPTION_KEY
import os
import base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
```

### Configuration SendGrid

1. Créer un compte sur https://sendgrid.com
2. Créer une clé API avec permissions d'envoi d'emails
3. Vérifier votre domaine d'envoi
4. Ajouter la clé à `SENDGRID_API_KEY`

### Configuration Email SMTP

Si vous utilisez Gmail:
1. Activer l'authentification à 2 facteurs
2. Générer un mot de passe d'application
3. Utiliser ce mot de passe dans `MAIL_PASSWORD`

## Post-Déploiement

### 1. Vérifications

```bash
# Vérifier que l'application répond
curl http://localhost:5000

# Vérifier les logs
tail -f /var/log/econsular/app.log  # VPS
docker-compose logs -f web           # Docker
```

### 2. Créer le Compte Administrateur

Se connecter avec:
- **Email**: admin@diplomatie.gouv.cd
- **Mot de passe**: admin123

**Important**: Changer le mot de passe immédiatement après la première connexion!

### 3. Configuration Initiale

1. Créer les unités consulaires
2. Configurer les services disponibles
3. Créer les comptes agents
4. Tester le workflow complet

### 4. Tests de Sécurité

```bash
# Scanner de vulnérabilités
pip install safety
safety check

# Audit de sécurité
pip install bandit
bandit -r backend/
```

## Maintenance

### Sauvegardes Base de Données

```bash
# Sauvegarde manuelle
pg_dump -U econsular_user econsular_db > backup_$(date +%Y%m%d).sql

# Restauration
psql -U econsular_user econsular_db < backup_20240101.sql
```

### Automatisation des Sauvegardes

```bash
# Créer un script de sauvegarde
sudo nano /usr/local/bin/backup-econsular.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/econsular"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Sauvegarde de la base de données
pg_dump -U econsular_user econsular_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Sauvegarde des fichiers uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /home/econsular/econsular/uploads

# Garder seulement les 30 derniers jours
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Sauvegarde terminée: $DATE"
```

```bash
# Rendre exécutable
sudo chmod +x /usr/local/bin/backup-econsular.sh

# Ajouter au cron (tous les jours à 2h du matin)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-econsular.sh >> /var/log/backup-econsular.log 2>&1
```

### Mise à Jour de l'Application

```bash
# VPS
sudo su - econsular
cd econsular
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart econsular

# Docker
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### Surveillance

#### Logs à Surveiller

```bash
# Logs application (VPS)
tail -f /var/log/econsular/app.log
journalctl -u econsular -f

# Logs Nginx
tail -f /var/log/nginx/econsular_error.log

# Logs Docker
docker-compose logs -f
```

#### Métriques à Surveiller

- Utilisation CPU et mémoire
- Espace disque (uploads, base de données, logs)
- Temps de réponse HTTP
- Erreurs 500
- Tentatives de connexion échouées

### Dépannage

#### L'application ne démarre pas

```bash
# Vérifier les logs
journalctl -u econsular -n 100

# Vérifier la configuration
sudo systemctl status econsular

# Tester manuellement
sudo su - econsular
cd econsular
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 main:app
```

#### Erreurs de base de données

```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Vérifier les connexions
sudo -u postgres psql
\l  # Lister les bases de données
\du # Lister les utilisateurs
```

#### Problèmes de performance

```bash
# Augmenter le nombre de workers Gunicorn
# Dans /etc/systemd/system/econsular.service
ExecStart=... --workers 8 ...

# Redémarrer
sudo systemctl daemon-reload
sudo systemctl restart econsular
```

## Sécurité en Production

### Checklist de Sécurité

- [ ] HTTPS activé avec certificat valide
- [ ] Mot de passe admin changé
- [ ] SESSION_SECRET unique et sécurisé
- [ ] Firewall configuré (seulement ports 80, 443, 22)
- [ ] PostgreSQL accessible uniquement en local
- [ ] Sauvegardes automatiques configurées
- [ ] Logs de sécurité surveillés
- [ ] Mises à jour système régulières
- [ ] Rate limiting activé
- [ ] Headers de sécurité configurés

### Configuration du Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Support

Pour toute question ou problème:
- Consulter la documentation technique: `docs/TECHNICAL.md`
- Vérifier les logs d'application
- Contacter l'équipe de support technique

## Changelog

Consulter le fichier `CHANGELOG.md` pour l'historique des versions et modifications.
