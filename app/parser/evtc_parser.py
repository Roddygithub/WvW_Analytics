import struct
import zlib
import zipfile
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, BinaryIO
from dataclasses import dataclass, field
from enum import IntEnum


class CombatResult(IntEnum):
    """Combat result types from EVTC spec."""
    NORMAL = 0
    CRIT = 1
    GLANCE = 2
    BLOCK = 3
    EVADE = 4
    INTERRUPT = 5
    ABSORB = 6
    BLIND = 7
    KILLINGBLOW = 8
    DOWNED = 9
    BREAKBAR = 10
    ACTIVATION = 11
    CROWDCONTROL = 12


class IFF(IntEnum):
    """Friend/Foe affinity from EVTC spec."""
    FRIEND = 0
    FOE = 1
    UNKNOWN = 2


class BoonID(IntEnum):
    """Boon buff IDs from GW2."""
    MIGHT = 740
    FURY = 725
    QUICKNESS = 1187
    ALACRITY = 30328
    PROTECTION = 717
    AEGIS = 743
    STABILITY = 1122
    RESISTANCE = 26980
    RESOLUTION = 873
    REGENERATION = 718
    VIGOR = 726
    SWIFTNESS = 719
    SUPERSPEED = 5974  # Sprint boon


# Skill ID sets for boons and conditions (subset based on EVTC spec)
# These are used for strip/cleanse classification.
BOON_SKILL_IDS: set[int] = {
    int(BoonID.MIGHT),
    int(BoonID.FURY),
    int(BoonID.QUICKNESS),
    int(BoonID.ALACRITY),
    int(BoonID.PROTECTION),
    int(BoonID.AEGIS),
    int(BoonID.STABILITY),
    int(BoonID.RESISTANCE),
    int(BoonID.RESOLUTION),
    int(BoonID.REGENERATION),
    int(BoonID.VIGOR),
    int(BoonID.SWIFTNESS),
    int(BoonID.SUPERSPEED),
}

# Common damaging/negative conditions from EVTC spec
CONDITION_SKILL_IDS: set[int] = {
    723,    # Poison
    736,    # Bleeding
    737,    # Burning (implied by ordering in spec)
    738,    # Vulnerability
    742,    # Weakness
    861,    # Confusion
    19426,  # Torment
}


class StateChange(IntEnum):
    """Combat state change types from EVTC spec (cbtstatechange)."""
    NONE = 0  # CBTS_NONE
    ENTERCOMBAT = 1  # CBTS_ENTERCOMBAT
    EXITCOMBAT = 2  # CBTS_EXITCOMBAT
    CHANGEUP = 3  # CBTS_CHANGEUP
    CHANGEDEAD = 4  # CBTS_CHANGEDEAD
    CHANGEDOWN = 5  # CBTS_CHANGEDOWN
    SPAWN = 6  # CBTS_SPAWN
    DESPAWN = 7  # CBTS_DESPAWN
    HEALTHPCTUPDATE = 8  # CBTS_HEALTHPCTUPDATE
    SQCOMBATSTART = 9  # CBTS_SQCOMBATSTART
    SQCOMBATEND = 10  # CBTS_SQCOMBATEND
    WEAPSWAP = 11  # CBTS_WEAPSWAP
    MAXHEALTHUPDATE = 12  # CBTS_MAXHEALTHUPDATE
    POINTOFVIEW = 13  # CBTS_POINTOFVIEW
    LANGUAGE = 14  # CBTS_LANGUAGE
    GWBUILD = 15  # CBTS_GWBUILD
    SHARDID = 16  # CBTS_SHARDID
    REWARD = 17  # CBTS_REWARD
    BUFFINITIAL = 18  # CBTS_BUFFINITIAL
    POSITION = 19  # CBTS_POSITION
    VELOCITY = 20  # CBTS_VELOCITY
    FACING = 21  # CBTS_FACING
    TEAMCHANGE = 22  # CBTS_TEAMCHANGE
    ATTACKTARGET = 23  # CBTS_ATTACKTARGET
    TARGETABLE = 24  # CBTS_TARGETABLE
    MAPID = 25  # CBTS_MAPID
    REPLINFO = 26  # CBTS_REPLINFO
    STACKACTIVE = 27  # CBTS_STACKACTIVE
    STACKRESET = 28  # CBTS_STACKRESET
    GUILD = 29  # CBTS_GUILD
    BUFFINFO = 30  # CBTS_BUFFINFO
    BUFFFORMULA = 31  # CBTS_BUFFFORMULA
    SKILLINFO = 32  # CBTS_SKILLINFO
    SKILLTIMING = 33  # CBTS_SKILLTIMING
    BREAKBARSTATE = 34  # CBTS_BREAKBARSTATE
    BREAKBARPERCENT = 35  # CBTS_BREAKBARPERCENT
    INTEGRITY = 36  # CBTS_INTEGRITY
    MARKER = 37  # CBTS_MARKER
    BARRIERPCTUPDATE = 38  # CBTS_BARRIERPCTUPDATE
    STATRESET = 39  # CBTS_STATRESET
    EXTENSION = 40  # CBTS_EXTENSION
    APIDELAYED = 41  # CBTS_APIDELAYED
    INSTANCESTART = 42  # CBTS_INSTANCESTART
    RATEHEALTH = 43  # CBTS_RATEHEALTH
    RULESET = 44  # CBTS_RULESET
    SQUADMARKER = 45  # CBTS_SQUADMARKER
    ARCBUILD = 46  # CBTS_ARCBUILD
    GLIDER = 47  # CBTS_GLIDER
    STUNBREAK = 48  # CBTS_STUNBREAK


class BuffRemove(IntEnum):
    """Buff remove types from EVTC spec (cbtbuffremove)."""
    NONE = 0  # CBTB_NONE
    ALL = 1  # CBTB_ALL (all stacks removed)
    SINGLE = 2  # CBTB_SINGLE (single stack removed)
    MANUAL = 3  # CBTB_MANUAL (manual remove, ignore for strip/cleanse)
    UNKNOWN = 4  # CBTB_UNKNOWN


# Profession ID to name mapping (from GW2 API)
PROFESSION_NAMES = {
    1: "Guardian",
    2: "Warrior",
    3: "Engineer",
    4: "Ranger",
    5: "Thief",
    6: "Elementalist",
    7: "Mesmer",
    8: "Necromancer",
    9: "Revenant",
}

# Elite spec ID to name mapping (from GW2 API)
ELITE_SPEC_NAMES = {
    5: "Druid",
    7: "Daredevil",
    18: "Berserker",
    27: "Dragonhunter",
    34: "Reaper",
    40: "Chronomancer",
    43: "Scrapper",
    48: "Tempest",
    52: "Herald",
    55: "Soulbeast",
    56: "Weaver",
    57: "Holosmith",
    58: "Deadeye",
    59: "Mirage",
    60: "Scourge",
    61: "Spellbreaker",
    62: "Firebrand",
    63: "Renegade",
    64: "Harbinger",
    65: "Willbender",
    66: "Virtuoso",
    67: "Catalyst",
    68: "Bladesworn",
    69: "Vindicator",
    70: "Mechanist",
    71: "Specter",
    72: "Untamed",
}


def get_spec_name(profession_id: int, elite_spec_id: int) -> str:
    """Get human-readable spec name from profession and elite spec IDs."""
    prof_name = PROFESSION_NAMES.get(profession_id, "Unknown")
    
    # If no elite spec or elite spec is 0, return just profession
    if elite_spec_id == 0 or elite_spec_id not in ELITE_SPEC_NAMES:
        return prof_name
    
    # Return "Profession (Elite Spec)"
    elite_name = ELITE_SPEC_NAMES.get(elite_spec_id, "Unknown")
    return f"{prof_name} ({elite_name})"


@dataclass
class EVTCHeader:
    """EVTC file header."""
    magic: str
    arcdps_version: str
    revision: int
    species_id: int


@dataclass
class EVTCAgent:
    """Agent from EVTC agent table."""
    addr: int
    prof: int
    is_elite: int
    toughness: int
    concentration: int
    healing: int
    hitbox_width: int
    condition: int
    hitbox_height: int
    name: str
    
    @property
    def is_player(self) -> bool:
        """Check if agent is a player."""
        return self.is_elite != 0xFFFFFFFF
    
    @property
    def is_npc(self) -> bool:
        """Check if agent is an NPC."""
        return self.is_elite == 0xFFFFFFFF and (self.prof >> 16) != 0xFFFF
    
    @property
    def is_gadget(self) -> bool:
        """Check if agent is a gadget."""
        return self.is_elite == 0xFFFFFFFF and (self.prof >> 16) == 0xFFFF
    
    @property
    def species_id(self) -> int:
        """Get species ID for NPCs."""
        if self.is_npc:
            return self.prof & 0xFFFF
        return 0
    
    def parse_player_name(self) -> tuple[str, str, int]:
        """Parse player name combo string: character\x00account\x00subgroup\x00."""
        parts = self.name.split('\x00')
        character_name = parts[0] if len(parts) > 0 else ""
        account_name = parts[1] if len(parts) > 1 else ""
        subgroup = 0
        if len(parts) > 2 and parts[2].isdigit():
            subgroup = int(parts[2])
        return character_name, account_name, subgroup


@dataclass
class EVTCSkill:
    """Skill from EVTC skill table."""
    id: int
    name: str


@dataclass
class PlayerStatsData:
    """Aggregated statistics for a single player."""
    addr: int
    character_name: str = ""
    account_name: str = ""
    profession: int = 0
    elite_spec: int = 0
    profession_name: str = ""
    elite_spec_name: str = ""
    spec_name: str = ""  # e.g. "Guardian (Firebrand)"
    subgroup: int = 0
    is_ally: bool = False  # True if player is in our squad (has account_name)
    
    total_damage: int = 0
    damage_taken: int = 0
    downs: int = 0
    kills: int = 0
    deaths: int = 0
    
    # Boon uptimes (in milliseconds of buff active time)
    stability_uptime_ms: int = 0
    quickness_uptime_ms: int = 0
    aegis_uptime_ms: int = 0
    protection_uptime_ms: int = 0
    fury_uptime_ms: int = 0
    resistance_uptime_ms: int = 0
    alacrity_uptime_ms: int = 0
    might_total_stacks: int = 0  # Sum of all might stacks over time
    might_sample_count: int = 0  # Number of samples for averaging
    vigor_uptime_ms: int = 0
    superspeed_uptime_ms: int = 0
    
    # Support/Control stats
    strips: int = 0  # Boons removed from enemies
    cleanses: int = 0  # Conditions removed from allies
    cc_total: int = 0  # Breakbar damage dealt
    healing_out: int = 0  # Healing output
    barrier_out: int = 0  # Barrier output
    
    # Outgoing boon production (what this player gives to others, in milliseconds)
    stab_out_ms: int = 0  # Stability given to allies
    aegis_out_ms: int = 0  # Aegis given to allies
    protection_out_ms: int = 0  # Protection given to allies
    quickness_out_ms: int = 0  # Quickness given to allies
    alacrity_out_ms: int = 0  # Alacrity given to allies
    resistance_out_ms: int = 0  # Resistance given to allies
    might_out_stacks: int = 0  # Might stacks given to allies (sum of stacks * duration)
    fury_out_ms: int = 0  # Fury given to allies
    regeneration_out_ms: int = 0  # Regeneration given to allies
    vigor_out_ms: int = 0  # Vigor given to allies
    superspeed_out_ms: int = 0  # Superspeed given to allies


@dataclass
class CombatEvent:
    """Combat event from EVTC."""
    time: int
    src_agent: int
    dst_agent: int
    value: int
    buff_dmg: int
    overstack_value: int
    skillid: int
    src_instid: int
    dst_instid: int
    src_master_instid: int
    dst_master_instid: int
    iff: int
    buff: int
    result: int
    is_activation: int
    is_buffremove: int
    is_ninety: int
    is_fifty: int
    is_moving: int
    is_statechange: int
    is_flanking: int
    is_shields: int
    is_offcycle: int
    pad61: int
    pad62: int
    pad63: int
    pad64: int


class EVTCParseError(Exception):
    """EVTC parsing error."""
    pass


class EVTCParser:
    """
    EVTC/ZEVTC file parser.
    
    Based on specifications in docs/parser/README_evtc_spec.txt
    and docs/parser/writeencounter.cpp
    """
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.header: Optional[EVTCHeader] = None
        self.agents: list[EVTCAgent] = []
        self.skills: list[EVTCSkill] = []
        self.events: list[CombatEvent] = []
        
    def parse(self) -> None:
        """Parse EVTC file."""
        is_compressed = self.file_path.suffix == ".zevtc"
        
        if is_compressed:
            # .zevtc files are ZIP archives containing a single .evtc file
            try:
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    names = zf.namelist()
                    if not names:
                        raise EVTCParseError(".zevtc archive is empty")
                    inner_name = names[0]
                    with zf.open(inner_name, "r") as inner:
                        inner_data = inner.read()
            except zipfile.BadZipFile as e:
                raise EVTCParseError(f"Invalid .zevtc ZIP archive: {e}")
            except Exception as e:
                raise EVTCParseError(f"Failed to read .zevtc archive: {e}")

            file_obj = BytesIO(inner_data)
        else:
            file_obj = open(self.file_path, "rb")
        
        try:
            self._parse_header(file_obj)
            self._parse_agents(file_obj)
            self._parse_skills(file_obj)
            self._parse_events(file_obj)
        finally:
            if not is_compressed:
                file_obj.close()
    
    def _parse_header(self, f: BinaryIO) -> None:
        """Parse EVTC header (16 bytes)."""
        header_data = f.read(16)
        if len(header_data) < 16:
            raise EVTCParseError("File too short for header")
        
        magic = header_data[0:4].decode("ascii")
        if magic != "EVTC":
            raise EVTCParseError(f"Invalid magic bytes: {magic}")
        
        arcdps_version = header_data[4:12].decode("ascii").rstrip("\x00")
        
        revision = header_data[12]
        
        species_id = struct.unpack("<H", header_data[13:15])[0]
        
        self.header = EVTCHeader(
            magic=magic,
            arcdps_version=arcdps_version,
            revision=revision,
            species_id=species_id
        )
    
    def _parse_agents(self, f: BinaryIO) -> None:
        """Parse agent table."""
        agent_count_data = f.read(4)
        if len(agent_count_data) < 4:
            raise EVTCParseError("Failed to read agent count")
        
        agent_count = struct.unpack("<I", agent_count_data)[0]
        
        for _ in range(agent_count):
            agent_data = f.read(96)
            if len(agent_data) < 96:
                raise EVTCParseError("Failed to read agent data")
            
            addr = struct.unpack("<Q", agent_data[0:8])[0]
            prof = struct.unpack("<I", agent_data[8:12])[0]
            is_elite = struct.unpack("<I", agent_data[12:16])[0]
            toughness = struct.unpack("<h", agent_data[16:18])[0]
            concentration = struct.unpack("<h", agent_data[18:20])[0]
            healing = struct.unpack("<h", agent_data[20:22])[0]
            hitbox_width = struct.unpack("<H", agent_data[22:24])[0]
            condition = struct.unpack("<h", agent_data[24:26])[0]
            hitbox_height = struct.unpack("<H", agent_data[26:28])[0]
            
            name_bytes = agent_data[28:92]
            name = name_bytes.decode("utf-8", errors="ignore").rstrip("\x00")
            
            agent = EVTCAgent(
                addr=addr,
                prof=prof,
                is_elite=is_elite,
                toughness=toughness,
                concentration=concentration,
                healing=healing,
                hitbox_width=hitbox_width,
                condition=condition,
                hitbox_height=hitbox_height,
                name=name
            )
            
            self.agents.append(agent)
    
    def _parse_skills(self, f: BinaryIO) -> None:
        """Parse skill table."""
        skill_count_data = f.read(4)
        if len(skill_count_data) < 4:
            raise EVTCParseError("Failed to read skill count")
        
        skill_count = struct.unpack("<I", skill_count_data)[0]
        
        for _ in range(skill_count):
            skill_data = f.read(68)
            if len(skill_data) < 68:
                raise EVTCParseError("Failed to read skill data")
            
            skill_id = struct.unpack("<i", skill_data[0:4])[0]
            
            name_bytes = skill_data[4:68]
            name = name_bytes.decode("utf-8", errors="ignore").rstrip("\x00")
            
            skill = EVTCSkill(id=skill_id, name=name)
            self.skills.append(skill)
    
    def _parse_events(self, f: BinaryIO) -> None:
        """Parse combat events."""
        event_size = 64 if self.header.revision == 1 else 64
        
        while True:
            event_data = f.read(event_size)
            if len(event_data) < event_size:
                break
            
            if self.header.revision == 1:
                event = self._parse_event_rev1(event_data)
            else:
                event = self._parse_event_rev0(event_data)
            
            self.events.append(event)
    
    def _parse_event_rev1(self, data: bytes) -> CombatEvent:
        """Parse revision 1 combat event (64 bytes)."""
        time = struct.unpack("<Q", data[0:8])[0]
        src_agent = struct.unpack("<Q", data[8:16])[0]
        dst_agent = struct.unpack("<Q", data[16:24])[0]
        value = struct.unpack("<i", data[24:28])[0]
        buff_dmg = struct.unpack("<i", data[28:32])[0]
        overstack_value = struct.unpack("<I", data[32:36])[0]
        skillid = struct.unpack("<I", data[36:40])[0]
        src_instid = struct.unpack("<H", data[40:42])[0]
        dst_instid = struct.unpack("<H", data[42:44])[0]
        src_master_instid = struct.unpack("<H", data[44:46])[0]
        dst_master_instid = struct.unpack("<H", data[46:48])[0]
        iff = data[48]
        buff = data[49]
        result = data[50]
        is_activation = data[51]
        is_buffremove = data[52]
        is_ninety = data[53]
        is_fifty = data[54]
        is_moving = data[55]
        is_statechange = data[56]
        is_flanking = data[57]
        is_shields = data[58]
        is_offcycle = data[59]
        pad61 = data[60]
        pad62 = data[61]
        pad63 = data[62]
        pad64 = data[63]
        
        return CombatEvent(
            time=time,
            src_agent=src_agent,
            dst_agent=dst_agent,
            value=value,
            buff_dmg=buff_dmg,
            overstack_value=overstack_value,
            skillid=skillid,
            src_instid=src_instid,
            dst_instid=dst_instid,
            src_master_instid=src_master_instid,
            dst_master_instid=dst_master_instid,
            iff=iff,
            buff=buff,
            result=result,
            is_activation=is_activation,
            is_buffremove=is_buffremove,
            is_ninety=is_ninety,
            is_fifty=is_fifty,
            is_moving=is_moving,
            is_statechange=is_statechange,
            is_flanking=is_flanking,
            is_shields=is_shields,
            is_offcycle=is_offcycle,
            pad61=pad61,
            pad62=pad62,
            pad63=pad63,
            pad64=pad64
        )
    
    def _parse_event_rev0(self, data: bytes) -> CombatEvent:
        """Parse revision 0 combat event (64 bytes)."""
        return self._parse_event_rev1(data)
    
    def is_wvw_log(self) -> bool:
        """
        Check if log is WvW.
        
        From spec: "an npcid of 1 indicates log is wvw"
        species_id in header is the npcid.
        """
        if not self.header:
            return False
        
        return self.header.species_id == 1
    
    def get_map_id(self) -> Optional[int]:
        """Extract map ID from MAPID state change event."""
        for event in self.events:
            if event.is_statechange == StateChange.MAPID:
                return event.src_agent
        return None
    
    def get_combat_start_time(self) -> Optional[int]:
        """Get squad combat start time."""
        for event in self.events:
            if event.is_statechange == StateChange.SQCOMBATSTART:
                return event.time
        return None
    
    def get_combat_end_time(self) -> Optional[int]:
        """Get squad combat end time."""
        for event in self.events:
            if event.is_statechange == StateChange.SQCOMBATEND:
                return event.time
        return None
    
    def extract_player_stats(self) -> dict[int, PlayerStatsData]:
        """
        Extract per-player statistics from combat events.
        
        Returns:
            Dictionary mapping agent address to PlayerStatsData
        """
        logger = logging.getLogger(__name__)
        
        total_events = len(self.events)
        direct_damage_events = 0
        ally_to_enemy_damage_events = 0
        changedown_events = 0
        changedead_events = 0
        downed_results = 0
        killingblow_results = 0
        
        # Debug: count buff events
        buff_apply_events = 0
        quickness_events = 0
        alacrity_events = 0
        might_events = 0
        stability_events = 0
        unique_buff_ids = set()
        
        player_stats: dict[int, PlayerStatsData] = {}
        
        # Initialize stats for all player agents
        for agent in self.agents:
            if agent.is_player:
                char_name, acc_name, subgroup = agent.parse_player_name()
                # Allied players have account_name starting with ':'
                is_ally = acc_name.startswith(':') if acc_name else False
                
                # Get human-readable profession/spec names
                prof_name = PROFESSION_NAMES.get(agent.prof, "Unknown")
                elite_name = ELITE_SPEC_NAMES.get(agent.is_elite, "") if agent.is_elite != 0 else ""
                spec_name = get_spec_name(agent.prof, agent.is_elite)
                
                player_stats[agent.addr] = PlayerStatsData(
                    addr=agent.addr,
                    character_name=char_name,
                    account_name=acc_name,
                    profession=agent.prof,
                    elite_spec=agent.is_elite,
                    profession_name=prof_name,
                    elite_spec_name=elite_name,
                    spec_name=spec_name,
                    subgroup=subgroup,
                    is_ally=is_ally
                )
        
        # Track active boons per player (received): {player_addr: {buff_id: [(start_time, duration, stack_info), ...]}}
        active_boons: dict[int, dict[int, list[tuple[int, int]]]] = {}
        
                # Track outgoing boons per player (given):
        # {src_player: {buff_id: {dst_player: [(start_ms, end_ms, stack_count)]}}}
        outgoing_boons: dict[int, dict[int, dict[int, list[tuple[int, int, int]]]]] = {}
        
        # Debug helpers for suspect boon math
        DEBUG_BOON_PLAYERS = {"Fineeeh", "Fyrënstär", "Stikko Ze Rallybot"}
        DEBUG_BOON_IDS = {BoonID.AEGIS}
        debug_boon_totals: dict[str, dict[int, int]] = {}
        
        # Helpers to cap/validate durations
        squad_start = self.get_combat_start_time() or (self.events[0].time if self.events else 0)
        squad_end = self.get_combat_end_time() or (self.events[-1].time if self.events else squad_start)
        fight_duration_ms = max(1, squad_end - squad_start)

        logger.debug(
            "Fight timing: raw_start=%d raw_end=%d duration_ms=%d file=%s",
            squad_start,
            squad_end,
            fight_duration_ms,
            getattr(self.file_path, "name", "N/A"),
        )

        def normalize_time(timestamp: int) -> int:
            """Convert raw EVTC timestamp into fight-relative milliseconds."""
            if timestamp <= squad_start:
                return 0
            if timestamp >= squad_end:
                return fight_duration_ms
            return timestamp - squad_start
        
        # Process all combat events
        for event in self.events:
            # Handle buff remove events (strips/cleanses)
            if event.is_buffremove != BuffRemove.NONE and event.is_buffremove != BuffRemove.MANUAL:
                # For buff remove events, EVTC uses:
                #   src_agent: agent that had the buff removed (target)
                #   dst_agent: agent that removed it (source/remover)
                if event.src_agent in player_stats and event.dst_agent in player_stats:
                    target_stats = player_stats[event.src_agent]
                    remover_stats = player_stats[event.dst_agent]

                    if remover_stats.is_ally:
                        stacks_removed = event.result if event.result > 0 else 1

                        # Strips: allied player removes a boon from an enemy player
                        if (event.skillid in BOON_SKILL_IDS) and (not target_stats.is_ally):
                            remover_stats.strips += stacks_removed

                        # Cleanses: allied player removes a condition from an allied player
                        elif (event.skillid in CONDITION_SKILL_IDS) and target_stats.is_ally:
                            remover_stats.cleanses += stacks_removed

                # Skip further processing of this event for damage/boons
                continue
            
            # Handle state changes
            if event.is_statechange != StateChange.NONE:
                if event.is_statechange == StateChange.CHANGEDEAD:
                    changedead_events += 1
                    # Player death (allied player died)
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.deaths += 1
                elif event.is_statechange == StateChange.CHANGEDOWN:
                    changedown_events += 1
                elif event.is_statechange == StateChange.BARRIERPCTUPDATE:
                    # Barrier application - track source if available
                    # Note: This state change doesn't directly give us the source
                    pass
                continue
            
            # Skip activation and buff remove events for damage calculation
            if event.is_activation != 0 or event.is_buffremove != 0:
                continue
            
            # Direct damage events (buff == 0)
            if event.buff == 0 and event.value > 0:
                direct_damage_events += 1
                
                # Damage dealt by player
                if event.src_agent in player_stats:
                    player_stats[event.src_agent].total_damage += event.value
                
                # Damage taken by player
                if event.dst_agent in player_stats:
                    player_stats[event.dst_agent].damage_taken += event.value
                
                # Count allied -> enemy damage events (players only)
                src_stats = player_stats.get(event.src_agent)
                dst_stats = player_stats.get(event.dst_agent)
                if src_stats and src_stats.is_ally and dst_stats and not dst_stats.is_ally:
                    ally_to_enemy_damage_events += 1
                
                # Check for breakbar damage
                if event.result == CombatResult.BREAKBAR:
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.cc_total += event.value if event.value > 0 else 0
                
                # Check for downs and kills (only count if target is enemy = IFF_FOE)
                if event.result == CombatResult.DOWNED and event.iff == IFF.FOE:
                    downed_results += 1
                    # Allied player downed an enemy
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.downs += 1
                elif event.result == CombatResult.KILLINGBLOW and event.iff == IFF.FOE:
                    killingblow_results += 1
                    # Allied player killed an enemy
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.kills += 1
            
            # Buff apply events (buff != 0, buff_dmg == 0, value > 0)
            elif event.buff != 0 and event.buff_dmg == 0 and event.value >= 0:
                buff_apply_events += 1
                unique_buff_ids.add(event.skillid)
                
                # Count specific boons
                if event.skillid == BoonID.QUICKNESS:
                    quickness_events += 1
                elif event.skillid == BoonID.ALACRITY:
                    alacrity_events += 1
                elif event.skillid == BoonID.MIGHT:
                    might_events += 1
                    # Debug: log first 20 Might events for first allied player we find
                    if might_events <= 20 and event.dst_agent in player_stats:
                        stats = player_stats[event.dst_agent]
                        if stats.is_ally and stats.character_name:
                            logger.info(
                                "Might #%d for %s: time=%d, value=%d, buff_dmg=%d, overstack=%d, is_shields=%d, is_offcycle=%d, pad61=%d",
                                might_events, stats.character_name, event.time, event.value, event.buff_dmg,
                                event.overstack_value, event.is_shields, event.is_offcycle, event.pad61
                            )
                elif event.skillid == BoonID.STABILITY:
                    stability_events += 1
                
                # Buff applied to dst_agent - store (time, duration, stacks) for RECEIVED boons
                if event.dst_agent in player_stats:
                    if event.dst_agent not in active_boons:
                        active_boons[event.dst_agent] = {}
                    if event.skillid not in active_boons[event.dst_agent]:
                        active_boons[event.dst_agent][event.skillid] = []
                    # Store (start_time, duration, stack_count) - is_shields is the stack count!
                    active_boons[event.dst_agent][event.skillid].append((event.time, event.value, event.is_shields))
                
                # Track OUTGOING boons: src_agent gave boon to dst_agent
                # Only track if both are allied players and the boon is relevant
                if (
                    event.src_agent in player_stats
                    and event.dst_agent in player_stats
                    and player_stats[event.src_agent].is_ally
                    and player_stats[event.dst_agent].is_ally
                ):
                    src = event.src_agent
                    buff_id = event.skillid
                    dst = event.dst_agent
                    duration = int(max(0, event.value))
                    if duration == 0:
                        continue
                    
                    # Clamp duration to fight length to avoid sentinel values (~4e9)
                    duration = min(duration, fight_duration_ms)
                    
                    if src not in outgoing_boons:
                        outgoing_boons[src] = {}
                    if buff_id not in outgoing_boons[src]:
                        outgoing_boons[src][buff_id] = {}
                    if dst not in outgoing_boons[src][buff_id]:
                        outgoing_boons[src][buff_id][dst] = []
                    
                    raw_start_time = event.time
                    raw_end_time = event.time + duration

                    # Normalize to fight-relative timeline and clamp to [0, fight_duration]
                    start_time = normalize_time(raw_start_time)
                    end_time = normalize_time(raw_end_time)
                    if end_time <= start_time:
                        continue
                    
                    stack_count = (
                        event.is_shields if buff_id == BoonID.MIGHT and event.is_shields > 0 else 1
                    )
                    outgoing_boons[src][buff_id][dst].append((start_time, end_time, stack_count))
                    
                    src_stats = player_stats[src]
                    if (
                        src_stats.character_name in DEBUG_BOON_PLAYERS
                        and buff_id in DEBUG_BOON_IDS
                    ):
                        debug_totals = debug_boon_totals.setdefault(src_stats.character_name, {})
                        prev_total = debug_totals.get(buff_id, 0)
                        interval_duration = end_time - start_time
                        debug_totals[buff_id] = prev_total + interval_duration
                        logger.debug(
                            (
                                "Aegis debug: player=%s dst=%s raw_time=%d rel_start=%d "
                                "rel_end=%d interval_ms=%d cumulative_ms=%d"
                            ),
                            src_stats.character_name,
                            player_stats[dst].character_name,
                            event.time,
                            start_time,
                            end_time,
                            interval_duration,
                            debug_totals[buff_id],
                        )
            
            # Condition damage events (buff != 0, buff_dmg > 0)
            elif event.buff != 0 and event.buff_dmg > 0:
                # Condition damage dealt by player
                if event.src_agent in player_stats:
                    player_stats[event.src_agent].total_damage += event.buff_dmg
        
        # Calculate boon uptimes from active_boons tracking
        for player_addr, stats in player_stats.items():
            if player_addr not in active_boons:
                continue
            
            player_boons = active_boons[player_addr]
            
            # Stability
            if BoonID.STABILITY in player_boons:
                stats.stability_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.STABILITY])
            
            # Quickness
            if BoonID.QUICKNESS in player_boons:
                stats.quickness_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.QUICKNESS])
            
            # Aegis
            if BoonID.AEGIS in player_boons:
                stats.aegis_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.AEGIS])
            
            # Protection
            if BoonID.PROTECTION in player_boons:
                stats.protection_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.PROTECTION])
            
            # Fury
            if BoonID.FURY in player_boons:
                stats.fury_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.FURY])
            
            # Resistance
            if BoonID.RESISTANCE in player_boons:
                stats.resistance_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.RESISTANCE])
            
            # Alacrity
            if BoonID.ALACRITY in player_boons:
                stats.alacrity_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.ALACRITY])
            
            # Vigor
            if BoonID.VIGOR in player_boons:
                stats.vigor_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.VIGOR])
            
            # Superspeed
            if BoonID.SUPERSPEED in player_boons:
                stats.superspeed_uptime_ms = sum(duration for _, duration, _ in player_boons[BoonID.SUPERSPEED])
            
            # Might - calculate average stacks by tracking active buff instances
            if BoonID.MIGHT in player_boons:
                # For stacking buffs, each application is a separate instance
                # We need to track when instances start and end to count concurrent stacks
                might_instances = player_boons[BoonID.MIGHT]
                
                # Create timeline of stack changes: (time, stack_delta)
                timeline = []
                for event_time, duration, _ in might_instances:
                    timeline.append((event_time, +1))  # Stack added
                    timeline.append((event_time + duration, -1))  # Stack removed
                
                # Sort by time
                timeline.sort()
                
                # Calculate time-weighted average
                total_stack_time = 0.0
                current_stacks = 0
                last_time = timeline[0][0] if timeline else 0
                
                for event_time, stack_delta in timeline:
                    # Accumulate time with current stack count
                    if event_time > last_time:
                        total_stack_time += current_stacks * (event_time - last_time)
                    
                    # Update stack count
                    current_stacks += stack_delta
                    current_stacks = max(0, min(25, current_stacks))  # Cap at 0-25
                    last_time = event_time
                
                # Store for service layer calculation
                stats.might_total_stacks = int(total_stack_time)
                stats.might_sample_count = 1  # Use 1 to indicate we have data
        
        # Helper to compute merged duration from intervals
        def merged_duration(intervals: list[tuple[int, int, int]], *, weight_by_stack: bool = False) -> int:
            if not intervals:
                return 0
            # Sort by start time
            sorted_intervals = sorted(intervals, key=lambda x: x[0])
            if not weight_by_stack:
                simplified = [(start, end) for start, end, _ in sorted_intervals]
                total = 0
                cur_start, cur_end = simplified[0]
                for start, end in simplified[1:]:
                    if start <= cur_end:
                        cur_end = max(cur_end, end)
                    else:
                        total += cur_end - cur_start
                        cur_start, cur_end = start, end
                total += cur_end - cur_start
                return total
            else:
                # For Might (stack count matters), expand timeline with deltas weighted by stacks
                timeline: list[tuple[int, int]] = []
                for start, end, stack in sorted_intervals:
                    stack = max(1, stack)
                    timeline.append((start, stack))
                    timeline.append((end, -stack))
                timeline.sort()
                total_weighted = 0
                current_stack = 0
                last_time = timeline[0][0]
                for time_point, delta in timeline:
                    if time_point > last_time and current_stack > 0:
                        total_weighted += current_stack * (time_point - last_time)
                    current_stack = max(0, current_stack + delta)
                    last_time = time_point
                return total_weighted
        
        # Calculate OUTGOING boon production from outgoing_boons tracking
        for player_addr, stats in player_stats.items():
            if player_addr not in outgoing_boons:
                continue
            
            player_outgoing = outgoing_boons[player_addr]
            
            def accumulate_boon(buff_id: int, *, weight_by_stack: bool = False) -> int:
                if buff_id not in player_outgoing:
                    return 0
                total = 0
                for intervals in player_outgoing[buff_id].values():
                    total += merged_duration(intervals, weight_by_stack=weight_by_stack)
                return total
            
            stats.stab_out_ms = accumulate_boon(BoonID.STABILITY)
            stats.aegis_out_ms = accumulate_boon(BoonID.AEGIS)
            stats.protection_out_ms = accumulate_boon(BoonID.PROTECTION)
            stats.quickness_out_ms = accumulate_boon(BoonID.QUICKNESS)
            stats.alacrity_out_ms = accumulate_boon(BoonID.ALACRITY)
            stats.resistance_out_ms = accumulate_boon(BoonID.RESISTANCE)
            stats.fury_out_ms = accumulate_boon(BoonID.FURY)
            stats.regeneration_out_ms = accumulate_boon(BoonID.REGENERATION)
            stats.vigor_out_ms = accumulate_boon(BoonID.VIGOR)
            stats.superspeed_out_ms = accumulate_boon(BoonID.SUPERSPEED)
            stats.might_out_stacks = accumulate_boon(BoonID.MIGHT, weight_by_stack=True)
        
        if debug_boon_totals:
            for player_name, boon_totals in debug_boon_totals.items():
                for boon_id, total_ms in boon_totals.items():
                    logger.debug(
                        "Outgoing boon summary: player=%s boon=%s total_ms=%d (fight_duration_ms=%d)",
                        player_name,
                        BoonID(boon_id).name if boon_id in BoonID.__members__.values() else boon_id,
                        total_ms,
                        fight_duration_ms,
                    )
        
        logger.info(
            "EVTC debug for %s: events=%d, direct=%d, ally_to_enemy=%d, changedown=%d, changedead=%d, res_downed=%d, res_killingblow=%d",
            self.file_path.name,
            total_events,
            direct_damage_events,
            ally_to_enemy_damage_events,
            changedown_events,
            changedead_events,
            downed_results,
            killingblow_results,
        )
        logger.info(
            "Buff debug for %s: buff_apply=%d, quick=%d, alac=%d, might=%d, stab=%d, unique_buffs=%d",
            self.file_path.name,
            buff_apply_events,
            quickness_events,
            alacrity_events,
            might_events,
            stability_events,
            len(unique_buff_ids),
        )
        if len(unique_buff_ids) > 0:
            logger.info("Sample buff IDs seen: %s", sorted(list(unique_buff_ids))[:20])
        
        return player_stats
