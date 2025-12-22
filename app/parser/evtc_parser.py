import struct
import zlib
import zipfile
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


class StateChange(IntEnum):
    """Combat state change types from EVTC spec."""
    NONE = 0
    ENTERCOMBAT = 1
    EXITCOMBAT = 2
    CHANGEUP = 3
    CHANGEDEAD = 4
    CHANGEDOWN = 5
    SPAWN = 6
    DESPAWN = 7
    HEALTHPCTUPDATE = 8
    SQCOMBATSTART = 9
    SQCOMBATEND = 10
    WEAPSWAP = 11
    MAXHEALTHUPDATE = 12
    POINTOFVIEW = 13
    LANGUAGE = 14
    GWBUILD = 15
    SHARDID = 16
    REWARD = 17
    BUFFINITIAL = 18
    POSITION = 19
    VELOCITY = 20
    FACING = 21
    TEAMCHANGE = 22
    ATTACKTARGET = 23
    TARGETABLE = 24
    MAPID = 25
    REPLINFO = 26
    STACKACTIVE = 27
    STACKRESET = 28
    GUILD = 29
    BUFFINFO = 30
    BUFFFORMULA = 31
    SKILLINFO = 32
    SKILLTIMING = 33
    BREAKBARSTATE = 34
    BREAKBARPERCENT = 35
    INTEGRITY = 36
    MARKER = 37
    BARRIERPCTUPDATE = 38
    STATRESET = 39
    EXTENSION = 40
    APIDELAYED = 41
    INSTANCESTART = 42
    RATEHEALTH = 43
    RULESET = 44
    SQUADMARKER = 45
    ARCBUILD = 46
    GLIDER = 47
    STUNBREAK = 48


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
    subgroup: int = 0
    is_ally: bool = False  # True if player is in our squad (has account_name)
    
    total_damage: int = 0
    damage_taken: int = 0
    downs: int = 0
    kills: int = 0
    deaths: int = 0


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
        player_stats: dict[int, PlayerStatsData] = {}
        
        # Initialize stats for all player agents
        for agent in self.agents:
            if agent.is_player:
                char_name, acc_name, subgroup = agent.parse_player_name()
                # Allied players have account_name starting with ':'
                is_ally = acc_name.startswith(':') if acc_name else False
                
                player_stats[agent.addr] = PlayerStatsData(
                    addr=agent.addr,
                    character_name=char_name,
                    account_name=acc_name,
                    profession=agent.prof,
                    elite_spec=agent.is_elite,
                    subgroup=subgroup,
                    is_ally=is_ally
                )
        
        # Process all combat events
        for event in self.events:
            # Handle state changes first
            if event.is_statechange != StateChange.NONE:
                if event.is_statechange == StateChange.CHANGEDEAD:
                    # Player death (allied player died)
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.deaths += 1
                elif event.is_statechange == StateChange.CHANGEDOWN:
                    # Player downed - check if it's an enemy downed by an ally
                    # src_agent is the one who got downed
                    # We need to find who caused it from previous damage events
                    # For now, we'll rely on CBTR_DOWNED result code in damage events
                    pass
                continue
            
            # Skip activation and buff remove events for damage calculation
            if event.is_activation != 0 or event.is_buffremove != 0:
                continue
            
            # Direct damage events (buff == 0)
            if event.buff == 0 and event.value > 0:
                # Damage dealt by player
                if event.src_agent in player_stats:
                    player_stats[event.src_agent].total_damage += event.value
                
                # Damage taken by player
                if event.dst_agent in player_stats:
                    player_stats[event.dst_agent].damage_taken += event.value
                
                # Check for downs and kills (only count if target is enemy = IFF_FOE)
                if event.result == CombatResult.DOWNED and event.iff == IFF.FOE:
                    # Allied player downed an enemy
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.downs += 1
                elif event.result == CombatResult.KILLINGBLOW and event.iff == IFF.FOE:
                    # Allied player killed an enemy
                    if event.src_agent in player_stats:
                        stats = player_stats[event.src_agent]
                        if stats.is_ally:
                            stats.kills += 1
            
            # Condition damage events (buff != 0, buff_dmg > 0)
            elif event.buff != 0 and event.buff_dmg > 0:
                # Condition damage dealt by player
                if event.src_agent in player_stats:
                    player_stats[event.src_agent].total_damage += event.buff_dmg
        
        return player_stats
