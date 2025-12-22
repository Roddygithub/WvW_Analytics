# Guide de Déploiement Manuel - WvW Analytics

Ce guide vous permet de déployer manuellement l'application sur le serveur.

## Connexion au Serveur

```bash
ssh syff@82.64.171.203 -p 2222
```

---

## Étape 1: Nettoyage de l'Ancien Projet

Exécutez ces commandes une par une :

```bash
# Arrêter et désactiver le service gw2-counterpicker
sudo systemctl stop gw2-counterpicker.service
sudo systemctl disable gw2-counterpicker.service

# Supprimer le fichier de service
sudo rm -f /etc/systemd/system/gw2-counterpicker.service
sudo systemctl daemon-reload

# Supprimer les dossiers du projet
rm -rf ~/gw2-counterpicker
sudo rm -rf /root/gw2optimizer
rm -f ~/gw2opt-deploy.tar.gz
rm -f ~/deploy_*.sh
rm -f ~/fix_apache_and_start.sh

# Arrêter Apache (on utilisera Nginx)
sudo systemctl stop apache2 || true
sudo systemctl disable apache2 || true

# Vérifier l'espace disque
df -h /
```

---

## Étape 2: Configuration du Serveur

```bash
# Mise à jour du système
sudo apt update
sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    postgresql \
    postgresql-contrib \
    build-essential \
    libpq-dev

# Vérifier les versions
python3 --version
pip3 --version
git --version
nginx -v
psql --version
```

---

## Étape 3: Configuration de PostgreSQL

```bash
# Créer la base de données et l'utilisateur
sudo -u postgres psql << EOF
CREATE DATABASE wvw_analytics;
CREATE USER wvw_user WITH PASSWORD 'wvw_secure_password_2024';
GRANT ALL PRIVILEGES ON DATABASE wvw_analytics TO wvw_user;
ALTER DATABASE wvw_analytics OWNER TO wvw_user;
\q
EOF

# Démarrer et activer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Démarrer et activer Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## Étape 4: Déploiement de l'Application

```bash
# Créer le répertoire et cloner le dépôt
mkdir -p ~/wvw-analytics
cd ~/wvw-analytics

# Si vous avez déjà cloné dans ~/WvW_Analytics, déplacez les fichiers
if [ -d ~/WvW_Analytics ]; then
    cp -r ~/WvW_Analytics/* ~/wvw-analytics/
    cp -r ~/WvW_Analytics/.git ~/wvw-analytics/
fi

# Ou cloner directement
git clone https://github.com/Roddygithub/WvW_Analytics.git .

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env
cat > .env << 'EOF'
DATABASE_URL=postgresql://wvw_user:wvw_secure_password_2024@localhost/wvw_analytics
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF

# Créer le répertoire uploads
mkdir -p uploads

# Initialiser la base de données
python3 << 'PYEOF'
from app.db.base import init_db
init_db()
print("Base de données initialisée avec succès!")
PYEOF

# Désactiver l'environnement virtuel
deactivate
```

---

## Étape 5: Configuration du Service Systemd

```bash
# Copier le fichier de service
sudo cp ~/wvw-analytics/deployment/wvw-analytics.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer et démarrer le service
sudo systemctl enable wvw-analytics.service
sudo systemctl start wvw-analytics.service

# Vérifier le statut
sudo systemctl status wvw-analytics.service
```

---

## Étape 6: Configuration de Nginx

```bash
# Copier la configuration Nginx
sudo cp ~/wvw-analytics/deployment/nginx_wvw_analytics.conf /etc/nginx/sites-available/wvw-analytics

# Créer le lien symbolique
sudo ln -sf /etc/nginx/sites-available/wvw-analytics /etc/nginx/sites-enabled/

# Supprimer la configuration par défaut
sudo rm -f /etc/nginx/sites-enabled/default

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

---

## Étape 7: Vérification

```bash
# Vérifier que le service tourne
sudo systemctl status wvw-analytics

# Vérifier les logs
sudo journalctl -u wvw-analytics -n 50

# Tester localement
curl http://localhost:8000

# Tester via Nginx
curl http://localhost
```

---

## Accès à l'Application

L'application est maintenant accessible sur : **http://82.64.171.203**

---

## Commandes de Maintenance

### Voir les logs en temps réel
```bash
sudo journalctl -u wvw-analytics -f
```

### Redémarrer le service
```bash
sudo systemctl restart wvw-analytics
```

### Mettre à jour l'application
```bash
cd ~/wvw-analytics
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart wvw-analytics
```

### Backup de la base de données
```bash
sudo -u postgres pg_dump wvw_analytics > ~/backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Dépannage

### Le service ne démarre pas
```bash
# Vérifier les logs détaillés
sudo journalctl -u wvw-analytics -n 100 --no-pager

# Vérifier que PostgreSQL tourne
sudo systemctl status postgresql

# Tester manuellement
cd ~/wvw-analytics
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Nginx retourne 502
```bash
# Vérifier que l'app tourne sur le port 8000
sudo netstat -tlnp | grep 8000

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/wvw_analytics_error.log
```

### Erreur de connexion PostgreSQL
```bash
# Vérifier que la base existe
sudo -u postgres psql -l | grep wvw_analytics

# Tester la connexion
sudo -u postgres psql wvw_analytics -c "SELECT 1;"

# Vérifier les permissions
sudo -u postgres psql -c "\du" | grep wvw_user
```

---

## Sécurité (Optionnel)

### Configurer le firewall
```bash
sudo apt install ufw
sudo ufw allow 22/tcp
sudo ufw allow 2222/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### Changer le mot de passe PostgreSQL
```bash
sudo -u postgres psql
ALTER USER wvw_user WITH PASSWORD 'nouveau_mot_de_passe_securise';
\q

# Mettre à jour le fichier .env
nano ~/wvw-analytics/.env
# Modifier DATABASE_URL avec le nouveau mot de passe

# Redémarrer le service
sudo systemctl restart wvw-analytics
```

---

## Support

Si vous rencontrez des problèmes, vérifiez :
1. Les logs du service : `sudo journalctl -u wvw-analytics -f`
2. Les logs Nginx : `sudo tail -f /var/log/nginx/wvw_analytics_error.log`
3. Que PostgreSQL tourne : `sudo systemctl status postgresql`
4. Que le port 8000 écoute : `sudo netstat -tlnp | grep 8000`
