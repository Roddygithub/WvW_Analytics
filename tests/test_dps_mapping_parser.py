import datetime

from app.services.dps_mapping import map_dps_json_to_models


def _base_json():
    return {
        "fightName": "Test",
        "durationMS": 60000,
        "players": [
            {
                "name": "Player One",
                "account": "one.1234",
                "group": 1,
                "profession": "Guardian",
                "eliteSpec": "Firebrand",
                "dpsAll": [{"damage": 1000}],
                "support": [{}],
                "defenses": [
                    {
                        "downCount": "2",
                        "deadCount": "1",
                        "damageTaken": 0,
                    }
                ],
                "details": {"boonGraph": []},
            }
        ],
        "phases": [
            {
                "dpsStats": [[1000, 0, 0, 0]],
                "defStats": [
                    # cols: damageTaken, barrier, missed, interrupted, invuln, damageInvuln,
                    # evaded, blocked, dodges, ... , downCount (13), downedDmg (14), deadCount (15)
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "3", 0, "2"]
                ],
                "supportStats": [[0, 0, 0, 0, 0, 0, 0, 0, 0]],
                "gameplayStats": [[]],
            }
        ],
    }


def test_downs_deaths_parsed_as_ints():
    data = _base_json()
    mapped = map_dps_json_to_models(data)
    ps = mapped.player_stats[0]
    assert ps.downs == 3
    assert ps.deaths == 2


def test_outgoing_boons_clamped_to_duration():
    data = _base_json()
    # Set explicit generations higher than duration to ensure clamp
    data["players"][0]["buffGenerations"] = [
        {"id": 1187, "buffData": [{"generation": 120000}]}  # Stability
    ]
    mapped = map_dps_json_to_models(data)
    ps = mapped.player_stats[0]
    # durationMS is 60000 -> clamp expected
    assert ps.stab_out_ms == 60000
