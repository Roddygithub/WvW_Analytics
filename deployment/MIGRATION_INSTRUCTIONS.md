# Instructions de Migration - Base de Données

## Problème
L'upload de logs échoue avec l'erreur:
```
psycopg2.errors.UndefinedColumn: ERREUR: la colonne « barrier_absorbed » de la relation « player_stats » n'existe pas
```

## Solution
La base de données PostgreSQL sur le serveur distant doit être mise à jour avec 35 nouvelles colonnes.

---

## Méthode 1: Script Automatique (Recommandé)

Connectez-vous au serveur et exécutez:

```bash
ssh syff@82.64.171.203 -p 2222
cd ~/wvw-analytics
git pull origin main
bash deployment/apply_migration.sh
```

Le script vous demandera votre mot de passe sudo.

---

## Méthode 2: Commandes Manuelles

Si le script ne fonctionne pas, exécutez ces commandes une par une:

```bash
# 1. Connexion au serveur
ssh syff@82.64.171.203 -p 2222

# 2. Aller dans le répertoire
cd ~/wvw-analytics

# 3. Récupérer les dernières modifications
git pull origin main

# 4. Appliquer la migration SQL
sudo -u postgres psql -d wvw_analytics -f deployment/migrate_db_schema.sql

# 5. Redémarrer le service
sudo systemctl restart wvw-analytics

# 6. Vérifier le statut
sudo systemctl status wvw-analytics
```

---

## Méthode 3: Via psql Interactif

```bash
# Connexion au serveur
ssh syff@82.64.171.203 -p 2222

# Se connecter à PostgreSQL
sudo -u postgres psql wvw_analytics

# Copier-coller le contenu du fichier migrate_db_schema.sql
# Ou exécuter:
\i /home/syff/wvw-analytics/deployment/migrate_db_schema.sql

# Quitter psql
\q

# Redémarrer le service
sudo systemctl restart wvw-analytics
```

---

## Vérification

Après la migration, vérifiez que les colonnes existent:

```bash
sudo -u postgres psql -d wvw_analytics -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'player_stats' 
  AND column_name IN ('barrier_absorbed', 'stab_out_ms', 'detected_role')
ORDER BY column_name;
"
```

Vous devriez voir:
```
    column_name    
-------------------
 barrier_absorbed
 detected_role
 stab_out_ms
(3 rows)
```

---

## Colonnes Ajoutées (35 au total)

### Outgoing Boon Production (11)
- stab_out_ms, aegis_out_ms, protection_out_ms
- quickness_out_ms, alacrity_out_ms, superspeed_out_ms
- resistance_out_ms, might_out_stacks, fury_out_ms
- regeneration_out_ms, vigor_out_ms

### Defensive Stats (9)
- barrier_absorbed, missed_count, interrupted_count
- evaded_count, blocked_count, dodged_count
- downs_count, downed_damage_taken, dead_count

### Support Stats (9)
- cleanses_other, cleanses_self
- cleanses_time_other, cleanses_time_self
- resurrects, resurrect_time
- stun_breaks, stun_break_time, strips_time

### Gameplay Stats (7)
- time_wasted, time_saved, weapon_swaps
- stack_dist, dist_to_com
- anim_percent, anim_no_auto_percent

### Active Time Tracking (4)
- dead_duration_ms, dc_duration_ms
- active_ms, presence_pct

### Role Detection (1)
- detected_role

---

## Test

Après la migration, essayez d'uploader un log sur:
- http://82.64.171.203:8001 (ou :80 après fix Nginx)

L'upload devrait maintenant fonctionner sans erreur.

---

## En Cas de Problème

### Erreur: "permission denied"
```bash
# Vérifier les permissions du fichier SQL
ls -la ~/wvw-analytics/deployment/migrate_db_schema.sql
chmod 644 ~/wvw-analytics/deployment/migrate_db_schema.sql
```

### Erreur: "database does not exist"
```bash
# Vérifier que la base existe
sudo -u postgres psql -l | grep wvw_analytics
```

### Service ne redémarre pas
```bash
# Voir les logs d'erreur
sudo journalctl -u wvw-analytics -n 50 --no-pager
```

---

## Rollback (Si Nécessaire)

Si la migration cause des problèmes, vous pouvez supprimer les colonnes:

```sql
-- NE PAS EXÉCUTER sauf en cas de problème majeur
ALTER TABLE player_stats DROP COLUMN IF EXISTS barrier_absorbed;
-- ... (répéter pour toutes les colonnes)
```

Mais il est préférable de corriger le problème plutôt que de faire un rollback.
