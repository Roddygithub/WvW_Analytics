# WvW Analytics - Audit Complet et Plan d'Alignement Elite Insights

**Date:** 18 Janvier 2026  
**Objectif:** Analyse complète du parser actuel et alignement 100% avec Elite Insights Parser

---

## 1. ÉTAT ACTUEL DU PROJET

### 1.1 Architecture Générale

**Points Forts:**
- ✅ Architecture propre avec séparation des responsabilités (services/parser/routers)
- ✅ Utilisation de dps.report comme source de vérité pour les métriques détaillées
- ✅ Parser EVTC fonctionnel pour la détection WvW et extraction basique
- ✅ Tests de calibration validant l'alignement avec EI sur les métriques clés
- ✅ Base de données SQLAlchemy bien structurée
- ✅ Frontend moderne avec Tailwind CSS et HTMX

**Architecture Actuelle:**
```
app/
├── parser/
│   └── evtc_parser.py          # Parser EVTC legacy (1128 lignes)
├── services/
│   ├── dps_mapping.py          # Mapping JSON EI → modèles DB (641 lignes)
│   ├── ei_mapping.py           # Mapping EI simplifié (177 lignes)
│   ├── logs_service.py         # Service de traitement des logs
│   ├── meta_service.py         # Agrégation META
│   └── roles_service.py        # Détection de rôles
├── integrations/
│   └── dps_report.py           # Client dps.report
└── db/
    └── models.py               # Modèles SQLAlchemy
```

### 1.2 Stratégie de Parsing Actuelle

**Approche Hybride:**
1. **Primaire:** dps.report (Elite Insights CLI en backend)
   - Upload du fichier .evtc/.zevtc vers dps.report
   - Récupération du JSON EI complet
   - Mapping via `dps_mapping.py`

2. **Fallback:** Parser EVTC local (déprécié)
   - Utilisé uniquement si dps.report échoue
   - Extraction basique de métriques
   - **Note:** Marqué comme déprécié dans le code

**Verdict:** ✅ **Excellente approche** - Utiliser EI comme source de vérité est la bonne stratégie.

---

## 2. ANALYSE DU MAPPING ELITE INSIGHTS

### 2.1 Métriques Actuellement Mappées

**Offensive Stats (dpsStats):**
- ✅ `total_damage` - dpsStats[0]
- ✅ `power_damage` - dpsStats[1]
- ✅ `condi_damage` - dpsStats[2]
- ✅ `cc_total` (breakbar damage) - dpsStats[3]
- ✅ `kills` - via dpsAll/stats

**Defensive Stats (defStats):**
- ✅ `damage_taken` - defStats[0]
- ✅ `barrier_absorbed` - defStats[1]
- ✅ `missed_count` - defStats[2]
- ✅ `interrupted_count` - defStats[3]
- ✅ `evaded_count` - defStats[6]
- ✅ `blocked_count` - defStats[7]
- ✅ `dodged_count` - defStats[8]
- ✅ `downs_count` - defStats[13]
- ✅ `downed_damage_taken` - defStats[14]
- ✅ `dead_count` - defStats[15]
- ✅ `dead_duration_ms` - defStats[16]
- ✅ `dc_duration_ms` - defStats[18]

**Support Stats (supportStats):**
- ✅ `cleanses_other` - supportStats[0]
- ✅ `cleanses_time_other` - supportStats[1]
- ✅ `cleanses_self` - supportStats[2]
- ✅ `cleanses_time_self` - supportStats[3]
- ✅ `strips_out` - supportStats[4]
- ✅ `strips_time` - supportStats[5]
- ✅ `resurrects` - supportStats[6]
- ✅ `resurrect_time` - supportStats[7]
- ✅ `stun_breaks` - supportStats[8]
- ✅ `stun_break_time` - supportStats[9]

**Gameplay Stats (gameplayStats):**
- ✅ `time_wasted` - gameplayStats[0]
- ✅ `time_saved` - gameplayStats[2]
- ✅ `weapon_swaps` - gameplayStats[4]
- ✅ `stack_dist` - gameplayStats[5]
- ✅ `dist_to_com` - gameplayStats[6]
- ✅ `anim_percent` - gameplayStats[7]
- ✅ `anim_no_auto_percent` - gameplayStats[8]

**Boon Uptimes:**
- ✅ Tous les boons majeurs (stability, quickness, aegis, etc.)
- ✅ Weighted average par active duration (presence)
- ✅ Fallback sur boonGraph states si buffUptimes manquant

**Boon Generation (Outgoing):**
- ✅ Extraction depuis buffGenerations/buffGenerationsActive
- ✅ Fallback sur buffUptimes generated fields

### 2.2 Validation par Tests

**Test de Calibration (`test_dps_calibration.py`):**
```python
# Référence: TpD1 Group 2
✅ DPS: 371,876
✅ CC: 0
✅ Cleanses (others): 49
✅ Cleanses (self): 35
✅ Strips: 64
✅ Resurrects: 0
✅ Stun Breaks: 2
✅ Damage Taken: 265,583
✅ Barrier Absorbed: 67,014
✅ All defensive metrics validated
✅ All gameplay metrics validated
✅ Boon weighted averages: Quickness G2 ~17.36%, Squad ~25.84%
```

**Verdict:** ✅ **Excellente couverture** - Les métriques principales sont correctement extraites et validées.

---

## 3. GAPS ET PROBLÈMES IDENTIFIÉS

### 3.1 Métriques Manquantes dans la DB

**Modèle PlayerStats - Champs Non Persistés:**

Actuellement, certaines métriques sont extraites mais **non sauvegardées en base de données**:

```python
# Ces champs sont attachés dynamiquement mais pas dans le modèle DB:
ps.barrier_absorbed        # ❌ Non persisté
ps.missed_count           # ❌ Non persisté
ps.interrupted_count      # ❌ Non persisté
ps.evaded_count          # ❌ Non persisté
ps.blocked_count         # ❌ Non persisté
ps.dodged_count          # ❌ Non persisté
ps.downs_count           # ❌ Non persisté
ps.downed_damage_taken   # ❌ Non persisté
ps.dead_count            # ❌ Non persisté
ps.cleanses_other        # ❌ Non persisté
ps.cleanses_self         # ❌ Non persisté
ps.resurrects            # ❌ Non persisté
ps.resurrect_time        # ❌ Non persisté
ps.stun_breaks           # ❌ Non persisté
ps.stun_break_time       # ❌ Non persisté
ps.strips_time           # ❌ Non persisté
ps.cleanses_time_other   # ❌ Non persisté
ps.cleanses_time_self    # ❌ Non persisté
ps.time_wasted           # ❌ Non persisté
ps.time_saved            # ❌ Non persisté
ps.weapon_swaps          # ❌ Non persisté
ps.stack_dist            # ❌ Non persisté
ps.dist_to_com           # ❌ Non persisté
ps.anim_percent          # ❌ Non persisté
ps.anim_no_auto_percent  # ❌ Non persisté
ps.dead_duration_ms      # ❌ Non persisté
ps.dc_duration_ms        # ❌ Non persisté
ps.active_ms             # ❌ Non persisté
ps.presence_pct          # ❌ Non persisté
```

**Impact:** Ces métriques sont extraites et validées par les tests, mais **perdues après le parsing** car non sauvegardées en DB.

### 3.2 Métriques EI Non Extraites

**Offensive Stats Targets (offensiveStatsTargets):**
- ❌ Hits par cible
- ❌ Critical hits par cible
- ❌ Flanking hits
- ❌ Glancing hits
- ❌ Kills par cible spécifique

**Rotation/Skills:**
- ❌ Skill usage details
- ❌ Skill timing
- ❌ Rotation analysis
- ❌ Cast interruptions

**Buffs Détaillés:**
- ❌ Buff stacks over time (timeline)
- ❌ Buff sources (qui donne quoi à qui)
- ❌ Buff waste/overstack details
- ❌ Extension tracking

**Combat Replay:**
- ❌ Position tracking
- ❌ Movement data
- ❌ Mechanics tracking

**Damage Modifiers:**
- ❌ Trait modifiers
- ❌ Sigil/rune effects
- ❌ Food/utility buffs

### 3.3 Problèmes de Mapping Identifiés

**1. Boon Uptime Calculation:**
```python
# Actuel: Logique complexe avec multiples fallbacks
# ✅ CORRECT: Utilise presence/active duration pour weighted average
# ⚠️  ATTENTION: Multiples chemins de calcul peuvent créer des incohérences
```

**2. Outgoing Boon Generation:**
```python
# Actuel: Extraction depuis buffGenerations
# ⚠️  PROBLÈME: Certains boons utilisent des champs support legacy
ps.superspeed_out_ms = min(_to_int(support.get("superspeedOut"), 0), duration_ms)
ps.resistance_out_ms = min(_to_int(support.get("resistanceOut"), 0), duration_ms)
# ❌ Incohérent avec les autres boons qui utilisent buffGenerations
```

**3. Might Handling:**
```python
# Actuel: Might uptime en pourcentage (0-100)
might_uptime=uptimes["might"]
# ⚠️  ATTENTION: EI peut retourner might en stacks ou en %
# Besoin de normalisation claire
```

**4. Enemy Players:**
```python
# Actuel: Subgroup forcé à 0 pour enemies
subgroup_value = subgroup if is_ally else 0
# ✅ CORRECT pour éviter agrégation avec alliés
```

### 3.4 Parser EVTC Legacy

**État:** Déprécié mais toujours présent (1128 lignes)

**Problèmes:**
- ❌ Logique de boon tracking complexe et potentiellement buggée
- ❌ Calculs manuels de strips/cleanses (peut diverger d'EI)
- ❌ Pas de validation contre EI
- ❌ Utilisé uniquement en fallback

**Recommandation:** Garder uniquement pour WvW detection, supprimer la logique de calcul de métriques.

---

## 4. COMPARAISON AVEC ELITE INSIGHTS PARSER

### 4.1 Architecture EI (C#/.NET)

**Structure EI:**
```
GW2EI/
├── Parsers/
│   ├── ParsedEvtcLog.cs       # Log principal
│   ├── ParsedData/            # Données parsées
│   │   ├── CombatEvents/
│   │   ├── Buffs/
│   │   └── Mechanics/
│   └── EvtcParser.cs          # Parser binaire
├── Builders/
│   ├── JsonModels/            # Modèles JSON output
│   └── HtmlModels/            # Modèles HTML
└── Statistics/
    ├── DamageModifiers/
    ├── BuffStats/
    └── Mechanics/
```

**Différences Clés:**
1. **EI:** Parse complet → Calculs → Export JSON/HTML
2. **Notre approche:** Consomme JSON EI → Map vers DB

**Verdict:** ✅ Notre approche est **plus simple et plus fiable** - pas besoin de réimplémenter toute la logique EI.

### 4.2 JSON Schema EI

**Structure JSON EI (simplifié):**
```json
{
  "players": [{
    "name": "...",
    "profession": "...",
    "group": 1,
    "dpsAll": [{ "damage": 0, "dps": 0, ... }],
    "defenses": [{ "damageTaken": 0, ... }],
    "support": [{ "condiCleanse": 0, ... }],
    "statsAll": [{ ... }],
    "buffUptimes": [{ "id": 740, "buffData": [...] }],
    "buffUptimesActive": [...],
    "buffGenerations": [...],
    "details": {
      "boonGraph": [...],
      "rotation": [...],
      "damageModifiers": [...]
    }
  }],
  "phases": [{
    "dpsStats": [[...], [...]],
    "defStats": [[...], [...]],
    "supportStats": [[...], [...]],
    "gameplayStats": [[...], [...]]
  }]
}
```

**Notre Mapping:** ✅ Couvre les champs principaux, ❌ Manque details/rotation/damageModifiers

---

## 5. RECOMMANDATIONS POUR ALIGNEMENT 100%

### 5.1 Priorité 1: Compléter le Modèle DB

**Action:** Ajouter tous les champs manquants à `PlayerStats`

```python
# À ajouter dans app/db/models.py
class PlayerStats(Base):
    # ... champs existants ...
    
    # Defensive granular
    barrier_absorbed = Column(Integer, default=0)
    missed_count = Column(Integer, default=0)
    interrupted_count = Column(Integer, default=0)
    evaded_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    dodged_count = Column(Integer, default=0)
    downs_count = Column(Integer, default=0)
    downed_damage_taken = Column(Integer, default=0)
    dead_count = Column(Integer, default=0)
    
    # Support granular
    cleanses_other = Column(Integer, default=0)
    cleanses_self = Column(Integer, default=0)
    cleanses_time_other = Column(Float, default=0.0)
    cleanses_time_self = Column(Float, default=0.0)
    resurrects = Column(Integer, default=0)
    resurrect_time = Column(Float, default=0.0)
    stun_breaks = Column(Integer, default=0)
    stun_break_time = Column(Float, default=0.0)
    strips_time = Column(Float, default=0.0)
    
    # Gameplay
    time_wasted = Column(Float, default=0.0)
    time_saved = Column(Float, default=0.0)
    weapon_swaps = Column(Integer, default=0)
    stack_dist = Column(Float, default=0.0)
    dist_to_com = Column(Float, default=0.0)
    anim_percent = Column(Float, default=0.0)
    anim_no_auto_percent = Column(Float, default=0.0)
    
    # Active time tracking
    dead_duration_ms = Column(Float, default=0.0)
    dc_duration_ms = Column(Float, default=0.0)
    active_ms = Column(Float, default=0.0)
    presence_pct = Column(Float, default=0.0)
```

**Migration:** Créer migration Alembic pour ajouter ces colonnes.

### 5.2 Priorité 2: Uniformiser Boon Generation

**Problème:** Incohérence entre boons utilisant buffGenerations vs support legacy fields

**Solution:**
```python
# Dans dps_mapping.py, uniformiser tous les boons:
outgoing_ms = {
    name: _out_ms_from_generations(player, buff_id, duration_ms)
    for name, buff_id in BOON_IDS.items()
}
# Supprimer les lignes legacy:
# ps.superspeed_out_ms = min(_to_int(support.get("superspeedOut"), 0), duration_ms)
# ps.resistance_out_ms = min(_to_int(support.get("resistanceOut"), 0), duration_ms)
# etc.
```

### 5.3 Priorité 3: Nettoyer Parser EVTC Legacy

**Action:** Simplifier `evtc_parser.py`

**Garder:**
- Header parsing (WvW detection)
- Agent table parsing
- Basic metadata extraction

**Supprimer:**
- Logique de calcul de boons (lignes 666-1000+)
- Calculs manuels de strips/cleanses
- Toute logique dupliquant EI

**Nouveau rôle:** Validation WvW uniquement, pas de calcul de métriques.

### 5.4 Priorité 4: Améliorer Tests

**Ajouter:**
```python
# tests/test_ei_alignment.py
def test_all_metrics_persisted():
    """Vérifie que toutes les métriques extraites sont sauvegardées en DB"""
    # Parse log
    # Vérifie que tous les champs non-null sont en DB
    
def test_boon_generation_consistency():
    """Vérifie que tous les boons utilisent la même logique d'extraction"""
    
def test_enemy_players_handling():
    """Vérifie le traitement correct des enemy players"""
```

### 5.5 Priorité 5: Documentation

**Créer:**
- `docs/EI_MAPPING.md` - Documentation complète du mapping JSON EI → DB
- `docs/METRICS_REFERENCE.md` - Référence de toutes les métriques avec formules
- Mettre à jour `CALCULATION_RULES.md` avec les nouvelles métriques

---

## 6. FONCTIONNALITÉS AVANCÉES (OPTIONNEL)

### 6.1 Métriques Avancées EI

**Si besoin d'aller plus loin:**

**Damage Modifiers:**
- Extraction depuis `details.damageModifiers`
- Stockage par trait/sigil/food
- Calcul de contribution DPS

**Rotation Analysis:**
- Extraction depuis `details.rotation`
- Skill usage frequency
- Rotation optimization hints

**Combat Replay:**
- Position tracking depuis `details.combatReplayData`
- Movement analysis
- Mechanics tracking

**Buff Sources:**
- Qui donne quoi à qui (buffGenerations per source)
- Boon uptime contribution par joueur
- Optimization de boon share

### 6.2 Agrégations META Avancées

**Actuellement:** Simple top specs par usage

**Améliorations possibles:**
- Winrate par spec (nécessite fight result detection)
- Performance percentiles par spec
- Role distribution par context
- Boon coverage analysis (qui manque de quickness/alacrity)

---

## 7. PLAN D'ACTION RECOMMANDÉ

### Phase 1: Complétion DB (1-2h)
1. ✅ Ajouter colonnes manquantes à PlayerStats
2. ✅ Créer migration Alembic
3. ✅ Mettre à jour dps_mapping.py pour persister tous les champs
4. ✅ Vérifier que tests passent toujours

### Phase 2: Uniformisation (1h)
1. ✅ Uniformiser extraction boon generation
2. ✅ Nettoyer code legacy dans dps_mapping.py
3. ✅ Valider avec tests existants

### Phase 3: Nettoyage Parser (1h)
1. ✅ Simplifier evtc_parser.py
2. ✅ Garder uniquement WvW detection
3. ✅ Ajouter commentaires de dépréciation clairs

### Phase 4: Tests & Documentation (1h)
1. ✅ Ajouter tests de persistance
2. ✅ Créer documentation mapping EI
3. ✅ Mettre à jour CALCULATION_RULES.md

### Phase 5: Validation (30min)
1. ✅ Tester avec plusieurs logs réels
2. ✅ Comparer output avec EI HTML
3. ✅ Valider agrégations META

**Total estimé:** 5-6 heures de développement

---

## 8. CONCLUSION

### Points Forts du Projet Actuel

✅ **Architecture solide** - Séparation claire des responsabilités  
✅ **Stratégie correcte** - Utiliser EI comme source de vérité  
✅ **Mapping robuste** - Extraction correcte des métriques principales  
✅ **Tests validés** - Calibration contre référence EI  
✅ **Code propre** - Type hints, documentation, structure professionnelle  

### Gaps Principaux

❌ **Métriques non persistées** - 25+ champs extraits mais perdus  
⚠️ **Incohérences mineures** - Boon generation legacy fields  
⚠️ **Parser legacy** - Code mort à nettoyer  
❌ **Documentation incomplète** - Manque référence complète EI mapping  

### Verdict Final

**Le projet est à ~85% d'alignement avec Elite Insights.**

Les métriques sont **correctement extraites** mais **partiellement persistées**.  
Avec les 4 phases du plan d'action, on atteindra **100% d'alignement** sur:
- ✅ Toutes les métriques de combat (offensive/defensive/support/gameplay)
- ✅ Tous les boons (uptimes + generation)
- ✅ Toutes les statistiques granulaires
- ✅ Persistance complète en base de données

**Métriques avancées non couvertes** (optionnel):
- Damage modifiers
- Rotation analysis
- Combat replay
- Buff sources détaillés

Ces métriques avancées ne sont **pas nécessaires** pour un parser WvW fonctionnel, mais peuvent être ajoutées plus tard si besoin.

---

**Prochaine étape recommandée:** Exécuter Phase 1 (Complétion DB) pour persister toutes les métriques actuellement extraites.
