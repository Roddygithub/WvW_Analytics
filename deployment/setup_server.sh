#!/bin/bash
# Script de configuration du serveur pour WvW Analytics
# À exécuter sur le serveur distant après cleanup_server.sh

set -e

echo "=== Configuration du serveur pour WvW Analytics ==="

# Mise à jour du système
echo "Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

# Installation des dépendances système
echo "Installation des dépendances..."
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

# Vérifier les versions installées
echo ""
echo "=== Versions installées ==="
python3 --version
pip3 --version
git --version
nginx -v
psql --version

# Créer le répertoire pour l'application
echo ""
echo "Création du répertoire de l'application..."
mkdir -p ~/wvw-analytics
cd ~/wvw-analytics

# Configurer PostgreSQL
echo ""
echo "=== Configuration de PostgreSQL ==="
sudo -u postgres psql -c "CREATE DATABASE wvw_analytics;" || echo "Base de données existe déjà"
sudo -u postgres psql -c "CREATE USER wvw_user WITH PASSWORD 'wvw_secure_password_2024';" || echo "Utilisateur existe déjà"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE wvw_analytics TO wvw_user;"
sudo -u postgres psql -c "ALTER DATABASE wvw_analytics OWNER TO wvw_user;"

# Démarrer et activer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Démarrer et activer Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

echo ""
echo "=== Configuration terminée ==="
echo "PostgreSQL: ✓"
echo "Nginx: ✓"
echo "Python: ✓"
echo ""
echo "Prochaines étapes:"
echo "1. Cloner le dépôt GitHub"
echo "2. Configurer l'environnement virtuel Python"
echo "3. Configurer le service systemd"
echo "4. Configurer Nginx comme reverse proxy"
