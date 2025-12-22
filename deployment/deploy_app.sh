#!/bin/bash
# Script de déploiement de l'application WvW Analytics
# À exécuter sur le serveur distant après setup_server.sh

set -e

APP_DIR="$HOME/wvw-analytics"
REPO_URL="https://github.com/Roddygithub/WvW_Analytics.git"

echo "=== Déploiement de WvW Analytics ==="

# Aller dans le répertoire de l'application
cd "$APP_DIR"

# Cloner ou mettre à jour le dépôt
if [ -d ".git" ]; then
    echo "Mise à jour du dépôt existant..."
    git pull origin main
else
    echo "Clonage du dépôt GitHub..."
    git clone "$REPO_URL" .
fi

# Créer l'environnement virtuel
echo "Création de l'environnement virtuel Python..."
python3 -m venv venv

# Activer l'environnement virtuel et installer les dépendances
echo "Installation des dépendances Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env pour la configuration
echo "Création du fichier de configuration..."
cat > .env << EOF
DATABASE_URL=postgresql://wvw_user:wvw_secure_password_2024@localhost/wvw_analytics
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF

# Créer le répertoire uploads
mkdir -p uploads

# Initialiser la base de données
echo "Initialisation de la base de données..."
python3 -c "from app.db.base import init_db; init_db()"

echo ""
echo "=== Déploiement terminé ==="
echo "Application installée dans: $APP_DIR"
echo "Environnement virtuel: $APP_DIR/venv"
echo ""
echo "Pour tester l'application:"
echo "cd $APP_DIR"
echo "source venv/bin/activate"
echo "uvicorn app.main:app --host 0.0.0.0 --port 8000"
