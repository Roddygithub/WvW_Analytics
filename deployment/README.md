# Guide de Déploiement - WvW Analytics

Ce guide détaille le processus complet de déploiement de WvW Analytics sur le serveur Debian distant.

## Informations du Serveur

- **IP**: 82.64.171.203
- **Port SSH**: 2222
- **Utilisateur**: syff
- **OS**: Debian 13 (Trixie)
- **Ressources**: 4 Go RAM, 2 CPU, 96 Go disque

## Prérequis

- Accès SSH au serveur
- Mot de passe sudo configuré
- GitHub CLI authentifié (pour les mises à jour)

## Processus de Déploiement

### Étape 1: Transfert des Scripts

Depuis votre machine locale, transférez les scripts de déploiement vers le serveur :

```bash
cd /home/roddy/WvW_Analytics
scp -P 2222 deployment/*.sh syff@82.64.171.203:~/
scp -P 2222 deployment/*.service syff@82.64.171.203:~/
scp -P 2222 deployment/*.conf syff@82.64.171.203:~/
```

### Étape 2: Connexion au Serveur

```bash
ssh syff@82.64.171.203 -p 2222
```

### Étape 3: Nettoyage de l'Ancien Projet

Exécutez le script de nettoyage pour supprimer GW2 CounterPicker :

```bash
chmod +x cleanup_server.sh
./cleanup_server.sh
```

Ce script va :
- Arrêter et désactiver le service `gw2-counterpicker`
- Supprimer les dossiers du projet
- Arrêter Apache (on utilisera Nginx)
- Libérer de l'espace disque

### Étape 4: Configuration du Serveur

Installez les dépendances système et configurez PostgreSQL :

```bash
chmod +x setup_server.sh
./setup_server.sh
```

Ce script va installer :
- Python 3 + pip + venv
- Git
- Nginx
- PostgreSQL
- Build tools

Et créer :
- Base de données PostgreSQL `wvw_analytics`
- Utilisateur PostgreSQL `wvw_user`

### Étape 5: Déploiement de l'Application

Clonez le dépôt GitHub et installez l'application :

```bash
chmod +x deploy_app.sh
./deploy_app.sh
```

Ce script va :
- Cloner le dépôt depuis GitHub
- Créer un environnement virtuel Python
- Installer les dépendances
- Créer le fichier `.env` avec la configuration
- Initialiser la base de données

### Étape 6: Installation du Service Systemd et Nginx

Configurez le service systemd et Nginx :

```bash
chmod +x install_service.sh
./install_service.sh
```

Ce script va :
- Installer le service systemd `wvw-analytics`
- Configurer Nginx comme reverse proxy
- Démarrer automatiquement l'application

### Étape 7: Vérification

Vérifiez que tout fonctionne :

```bash
# Statut du service
sudo systemctl status wvw-analytics

# Logs de l'application
sudo journalctl -u wvw-analytics -f

# Logs Nginx
sudo tail -f /var/log/nginx/wvw_analytics_error.log

# Test de connexion
curl http://localhost:8000
```

Accédez à l'application : **http://82.64.171.203**

## Mises à Jour de l'Application

Pour mettre à jour l'application après un push sur GitHub :

```bash
cd ~/wvw-analytics
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart wvw-analytics
```

Ou utilisez le script de mise à jour :

```bash
cd ~/wvw-analytics
./deployment/update_app.sh
```

## Commandes Utiles

### Gestion du Service

```bash
# Démarrer
sudo systemctl start wvw-analytics

# Arrêter
sudo systemctl stop wvw-analytics

# Redémarrer
sudo systemctl restart wvw-analytics

# Statut
sudo systemctl status wvw-analytics

# Logs en temps réel
sudo journalctl -u wvw-analytics -f
```

### Gestion de Nginx

```bash
# Tester la configuration
sudo nginx -t

# Recharger la configuration
sudo systemctl reload nginx

# Redémarrer
sudo systemctl restart nginx

# Logs
sudo tail -f /var/log/nginx/wvw_analytics_access.log
sudo tail -f /var/log/nginx/wvw_analytics_error.log
```

### Base de Données

```bash
# Connexion à PostgreSQL
sudo -u postgres psql wvw_analytics

# Backup de la base de données
sudo -u postgres pg_dump wvw_analytics > backup_$(date +%Y%m%d).sql

# Restauration
sudo -u postgres psql wvw_analytics < backup_20241222.sql
```

## Structure des Fichiers sur le Serveur

```
/home/syff/
├── wvw-analytics/              # Application principale
│   ├── app/                    # Code Python
│   ├── templates/              # Templates Jinja2
│   ├── static/                 # CSS, JS, images
│   ├── uploads/                # Fichiers EVTC uploadés
│   ├── venv/                   # Environnement virtuel Python
│   ├── .env                    # Configuration (DATABASE_URL, etc.)
│   └── wvw_analytics.db        # Base SQLite (dev uniquement)
│
/etc/systemd/system/
└── wvw-analytics.service       # Service systemd

/etc/nginx/sites-available/
└── wvw-analytics               # Configuration Nginx

/var/log/nginx/
├── wvw_analytics_access.log   # Logs d'accès
└── wvw_analytics_error.log    # Logs d'erreur
```

## Configuration de la Base de Données

Par défaut, l'application utilise PostgreSQL en production :

**Connexion PostgreSQL:**
- Host: localhost
- Port: 5432
- Database: wvw_analytics
- User: wvw_user
- Password: wvw_secure_password_2024

Pour changer le mot de passe :

```bash
sudo -u postgres psql
ALTER USER wvw_user WITH PASSWORD 'nouveau_mot_de_passe';
\q
```

Puis mettez à jour le fichier `.env` :

```bash
nano ~/wvw-analytics/.env
# Modifier DATABASE_URL
sudo systemctl restart wvw-analytics
```

## Sécurité

### Firewall (UFW)

Si UFW est installé, configurez-le :

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 2222/tcp    # SSH custom port
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS (futur)
sudo ufw enable
```

### SSL/HTTPS (Optionnel)

Pour ajouter HTTPS avec Let's Encrypt :

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

## Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u wvw-analytics -n 50

# Vérifier que PostgreSQL tourne
sudo systemctl status postgresql

# Vérifier la connexion à la base
sudo -u postgres psql -c "\l" | grep wvw_analytics
```

### Nginx retourne 502 Bad Gateway

```bash
# Vérifier que l'application tourne
sudo systemctl status wvw-analytics

# Vérifier que le port 8000 écoute
sudo netstat -tlnp | grep 8000

# Vérifier les permissions
ls -la /home/syff/wvw-analytics/
```

### Erreurs de base de données

```bash
# Réinitialiser la base de données
cd ~/wvw-analytics
source venv/bin/activate
python3 -c "from app.db.base import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

## Support

Pour toute question ou problème :
- Vérifiez les logs : `sudo journalctl -u wvw-analytics -f`
- Consultez la documentation du projet
- Vérifiez le dépôt GitHub : https://github.com/Roddygithub/WvW_Analytics
