import json
from pathlib import Path
from collections import defaultdict
from app.services.dps_mapping import map_dps_json_to_models

# reference log path (TpD1 equivalent)
CANDIDATES = [
    Path('data/dps_report/TpD1-20251224_103232_20251104-223944_wvw.json'),
    Path('data/dps_report/MzPB-20251225_130746_20251104-223944_wvw.json'),
    Path('data/dps_report/VAUY-20251223_004332_20251104-223944_wvw.json'),
]
json_path = next((p for p in CANDIDATES if p.exists()), None)
if not json_path:
    raise SystemExit('No reference JSON found among candidates.')

json_data = json.loads(json_path.read_text())
mapped = map_dps_json_to_models(json_data)

fight = mapped.fight
fight_duration_ms = fight.duration_ms or 0

boon_keys = {
    'quickness':'quickness_uptime',
    'alacrity':'alacrity_uptime',
    'superspeed':'superspeed_uptime',
}

def active_duration_ms(player):
    presence = getattr(player, 'presence', None) or getattr(player, 'presence_pct', None)
    try:
        presence_val = float(presence) if presence is not None else None
    except (TypeError, ValueError):
        presence_val = None
    if presence_val is not None and presence_val > 0 and fight_duration_ms:
        return fight_duration_ms * (presence_val / 100.0)
    return float(fight_duration_ms or 0)

def weighted_avg(pls, attr):
    num=0.0; den=0.0
    for p in pls:
        w=active_duration_ms(p)
        den+=w
        num+=(getattr(p, attr,0.0) or 0.0)*w
    return (num/den) if den>0 else 0.0

players = [p for p in mapped.player_stats if getattr(p, 'is_ally', True) and 2 <= (p.subgroup or 0) <= 5]

# group 2
grp2 = [p for p in players if p.subgroup==2]
print(f'Using JSON: {json_path}')
print('Group 2 (targets: Quickness~17.36):')
for label,attr in boon_keys.items():
    val = weighted_avg(grp2, attr)
    print(f'  {label.capitalize()}: {val:.2f}%')

print('\nSquad Average (subgroups 2-5):')
for label,attr in boon_keys.items():
    val = weighted_avg(players, attr)
    print(f'  {label.capitalize()}: {val:.2f}%')
