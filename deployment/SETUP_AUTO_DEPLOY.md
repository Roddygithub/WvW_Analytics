# Configuration du Déploiement Automatique via GitHub Actions

Ce guide vous permet de configurer le déploiement automatique. Après cette configuration, chaque `git push` déclenchera automatiquement le déploiement sur le serveur.

## Étape 1 : Générer une Clé SSH pour GitHub Actions

Sur votre machine locale, exécutez :

```bash
ssh-keygen -t ed25519 -C "github-actions-wvw-analytics" -f ~/.ssh/github_actions_wvw
```

Appuyez sur Entrée pour ne pas mettre de passphrase (important pour l'automatisation).

Cela créera deux fichiers :
- `~/.ssh/github_actions_wvw` (clé privée)
- `~/.ssh/github_actions_wvw.pub` (clé publique)

## Étape 2 : Ajouter la Clé Publique au Serveur

Copiez la clé publique sur le serveur :

```bash
ssh-copy-id -i ~/.ssh/github_actions_wvw.pub -p 2222 syff@82.64.171.203
```

Ou manuellement :

```bash
cat ~/.ssh/github_actions_wvw.pub
```

Puis sur le serveur :

```bash
ssh syff@82.64.171.203 -p 2222
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
# Collez la clé publique à la fin du fichier
chmod 600 ~/.ssh/authorized_keys
```

## Étape 3 : Ajouter la Clé Privée à GitHub Secrets

1. Copiez la clé privée :
   ```bash
   cat ~/.ssh/github_actions_wvw
   ```

2. Allez sur GitHub : https://github.com/Roddygithub/WvW_Analytics/settings/secrets/actions

3. Cliquez sur **"New repository secret"**

4. Nom du secret : `SSH_PRIVATE_KEY`

5. Valeur : Collez tout le contenu de la clé privée (incluant les lignes `-----BEGIN` et `-----END`)

6. Cliquez sur **"Add secret"**

## Étape 4 : Tester le Déploiement Automatique

Faites un petit changement et poussez :

```bash
cd ~/WvW_Analytics
echo "# Test auto-deploy" >> README.md
git add README.md
git commit -m "Test automatic deployment"
git push origin main
```

Allez sur GitHub Actions pour voir le déploiement :
https://github.com/Roddygithub/WvW_Analytics/actions

## Vérification

Si tout fonctionne, vous verrez :
- ✅ Le workflow GitHub Actions passe au vert
- ✅ Le serveur se met à jour automatiquement
- ✅ L'application redémarre automatiquement

## Workflow Simplifié

Après configuration, votre workflow devient :

```bash
# 1. Modifiez votre code
cd ~/WvW_Analytics
# ... vos modifications ...

# 2. Commitez et poussez
git add .
git commit -m "Votre message"
git push origin main

# 3. C'EST TOUT ! GitHub Actions s'occupe du reste automatiquement
```

## Dépannage

### Le workflow échoue avec "Permission denied"
- Vérifiez que la clé publique est bien dans `~/.ssh/authorized_keys` sur le serveur
- Vérifiez les permissions : `chmod 600 ~/.ssh/authorized_keys`

### Le workflow ne se déclenche pas
- Vérifiez que le fichier `.github/workflows/deploy.yml` existe bien
- Vérifiez que vous avez poussé sur la branche `main`

### Le déploiement ne met pas à jour l'application
- Connectez-vous au serveur et vérifiez les logs : `sudo journalctl -u wvw-analytics -n 50`
