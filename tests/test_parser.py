import pytest
from pathlib import Path
from io import BytesIO
import struct

from app.parser.evtc_parser import EVTCParser, EVTCParseError, EVTCHeader


def create_minimal_evtc_header(species_id: int = 1) -> bytes:
    """Create a minimal valid EVTC header for testing."""
    header = bytearray(16)
    
    header[0:4] = b"EVTC"
    header[4:12] = b"20231201"
    header[12] = 1
    struct.pack_into("<H", header, 13, species_id)
    header[15] = 0
    
    return bytes(header)


def create_minimal_evtc_file(species_id: int = 1) -> bytes:
    """Create a minimal valid EVTC file for testing."""
    data = bytearray()
    
    data.extend(create_minimal_evtc_header(species_id))
    
    data.extend(struct.pack("<I", 0))
    
    data.extend(struct.pack("<I", 0))
    
    return bytes(data)


def test_evtc_header_parsing(tmp_path: Path):
    """Test EVTC header parsing."""
    test_file = tmp_path / "test.evtc"
    test_file.write_bytes(create_minimal_evtc_file(species_id=1))
    
    parser = EVTCParser(test_file)
    parser._parse_header(open(test_file, "rb"))
    
    assert parser.header is not None
    assert parser.header.magic == "EVTC"
    assert parser.header.arcdps_version == "20231201"
    assert parser.header.revision == 1
    assert parser.header.species_id == 1


def test_wvw_detection_positive(tmp_path: Path):
    """Test WvW log detection (npcid == 1)."""
    test_file = tmp_path / "wvw.evtc"
    test_file.write_bytes(create_minimal_evtc_file(species_id=1))
    
    parser = EVTCParser(test_file)
    parser.parse()
    
    assert parser.is_wvw_log() is True


def test_wvw_detection_negative(tmp_path: Path):
    """Test non-WvW log detection (npcid != 1)."""
    test_file = tmp_path / "pve.evtc"
    test_file.write_bytes(create_minimal_evtc_file(species_id=100))
    
    parser = EVTCParser(test_file)
    parser.parse()
    
    assert parser.is_wvw_log() is False


def test_invalid_magic_bytes(tmp_path: Path):
    """Test parser rejects invalid magic bytes."""
    test_file = tmp_path / "invalid.evtc"
    
    invalid_data = bytearray(16)
    invalid_data[0:4] = b"XXXX"
    test_file.write_bytes(bytes(invalid_data))
    
    parser = EVTCParser(test_file)
    
    with pytest.raises(EVTCParseError, match="Invalid magic bytes"):
        parser.parse()


def test_file_too_short(tmp_path: Path):
    """Test parser rejects files that are too short."""
    test_file = tmp_path / "short.evtc"
    test_file.write_bytes(b"EVTC")
    
    parser = EVTCParser(test_file)
    
    with pytest.raises(EVTCParseError, match="File too short"):
        parser.parse()
