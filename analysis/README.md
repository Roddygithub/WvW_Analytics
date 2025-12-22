# Role Threshold Tuning - Data-Driven Analysis

This directory contains scripts for analyzing your WvW log dataset to calibrate role detection thresholds based on real data distributions.

## 📋 Workflow

### Step 1: Bulk Import Logs

Import all your existing logs into the database:

```bash
python -m app.scripts.bulk_import "/home/roddy/Téléchargements/WvW/WvW (1)"
```

This will:
- Recursively scan the directory for `.evtc` and `.zevtc` files
- Process each log through the same pipeline as web uploads
- Skip files already imported (based on filename)
- Show progress and error summary

**Expected time:** ~1-2 hours for 1600 logs (depends on file sizes and CPU)

**Note:** The script handles spaces and special characters in folder names correctly.

### Step 2: Export Player Stats to CSV

Export all allied player statistics to CSV for analysis:

```bash
python -m app.scripts.export_player_stats analysis/player_stats_all.csv
```

This creates a CSV with columns:
- **Basic info:** `fight_id`, `character_name`, `account_name`, `profession`, `elite_spec`
- **Combat stats:** `dps`, `total_damage`, `downs`, `kills`, `deaths`, `damage_taken`
- **Boon uptimes:** `quickness_uptime`, `alacrity_uptime`, `resistance_uptime`, `might_uptime`, etc.
- **Support stats:** `strips_out`, `cleanses`, `cc_total`, `healing_out`, `barrier_out`
- **Current classification:** `detected_role`

### Step 3: Analyze Distributions

Compute percentiles and get threshold recommendations:

```bash
python analysis/analyze_percentiles.py analysis/player_stats_all.csv
```

This will output:
- **Distribution analysis** for each key metric (DPS, cleanses, strips, quickness, resistance, etc.)
- **Percentiles** (P50, P70, P80, P90, P95) for each metric
- **Current role distribution** (how many DPS, Boon Support, Healer, etc.)
- **Proposed threshold values** based on your real data

Example output:
```
📈 Distribution Analysis
================================================================================

🔍 DPS (dps)
--------------------------------------------------------------------------------
   Count:  15234
   Mean:   1456.23
   Median: 1203.45
   Std:    892.11

   Percentiles:
      P50:  1203.45
      P70:  1789.23
      P80:  2134.56
      P90:  2678.90
      P95:  3012.34

🔍 Cleanses (cleanses)
--------------------------------------------------------------------------------
   ...
```

### Step 4: Update Thresholds

Based on the analysis output, update `app/services/roles_service.py`:

```python
# Example: if P80 of cleanses is 280, update:
HEALER_MIN_CLEANSES = 280  # was 200

# If P70 of DPS is 1800, update:
DPS_MIN_DPS = 1800  # was 1500

# etc.
```

### Step 5: Test & Iterate

1. Restart your Flask server (if running)
2. Check a few sample fights to see if role classification improved
3. If needed, adjust thresholds again and repeat

---

## 🎯 Key Metrics for WvW Role Detection

### Healer/Support
- **High cleanses** (P80-P90 of cleanses distribution)
- **Low DPS** (< 800)
- Typical builds: Tempest, Druid, support Scrapper

### Boon Support
- **High boon uptime** (P70-P80 of quickness/alacrity/resistance)
- **Moderate cleanses** (P50+)
- **Moderate DPS** (< P80 of DPS)
- Typical builds: Firebrand, Chronomancer, Scrapper
- **Note:** In WvW, Resistance is as important as Quickness for support detection

### Stripper
- **High strips** (P80+ of strips)
- **Low cleanses** (< P50)
- **Strip-to-cleanse ratio** > 1.5
- Typical builds: Spellbreaker, Scourge, strip Scrapper

### DPS
- **High DPS** (P70+ of DPS)
- **Low support stats** (cleanses < P50, strips < P50)
- **Note:** Boon uptimes are NOT checked (players receive boons, don't give them)
- Typical builds: Weaver, Deadeye, Reaper, power builds

### Hybrid
- Catch-all for mixed builds that don't fit clear categories
- Examples: boon DPS, off-support, weird builds

---

## 📊 Understanding Percentiles

- **P50 (median):** Half of players are below this value
- **P70:** 70% of players are below this value (good for "above average")
- **P80:** 80% of players are below this value (good for "high performers")
- **P90:** 90% of players are below this value (top 10%)
- **P95:** 95% of players are below this value (top 5%)

**Recommendation:** Use P70-P80 for role-defining thresholds to capture dedicated builds without being too strict.

---

## 🔧 Troubleshooting

### "Directory not found"
Make sure the path is correct and properly quoted:
```bash
python -m app.scripts.bulk_import "/home/roddy/Téléchargements/WvW/WvW (1)"
```

### "File already imported"
The script skips files with the same filename. To re-import:
1. Delete the corresponding Fight records from the database, or
2. Rename the files

### Import errors
Check the error summary at the end. Common issues:
- Corrupted .zevtc files
- Non-WvW logs (will be rejected)
- Very short fights (< 10 seconds)

### Analysis script fails
Make sure you ran the export script first:
```bash
python -m app.scripts.export_player_stats analysis/player_stats_all.csv
```

---

## 📝 Notes

- The bulk import script is **idempotent**: running it multiple times won't create duplicates
- CSV export only includes **allied players** (account_name is not null)
- Analysis filters out **inactive players** (DPS = 0 and no support stats)
- Thresholds are **tuneable constants** - adjust based on your meta and playstyle
- You can re-run the analysis after each tuning iteration to see the impact

---

## 🚀 Next Steps After Tuning

Once you're happy with the role classification:

1. **Multi-log aggregation:** Analyze trends across all fights
2. **META analysis:** Which specs dominate each role?
3. **Performance benchmarks:** What's "good DPS" for each spec?
4. **Comp analysis:** Which group comps win more?
5. **Player progression:** Track individual improvement over time

All of this becomes possible once you have 1600+ logs with accurate role detection! 🎯
