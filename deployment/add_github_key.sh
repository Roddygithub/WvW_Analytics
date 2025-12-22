#!/bin/bash
# Ajout de la clé SSH GitHub Actions au serveur

echo "=== Ajout de la clé SSH pour GitHub Actions ==="
echo ""

# Lire la clé publique locale
PUB_KEY=$(cat ~/.ssh/github_actions_wvw.pub)

echo "Clé publique à ajouter :"
echo "$PUB_KEY"
echo ""

# Ajouter la clé au serveur
ssh syff@82.64.171.203 -p 2222 "echo '$PUB_KEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

echo ""
echo "✓ Clé ajoutée au serveur"
echo ""
echo "Test de connexion sans mot de passe..."
ssh -i ~/.ssh/github_actions_wvw -p 2222 syff@82.64.171.203 "echo '✓ Connexion SSH réussie sans mot de passe !'"
