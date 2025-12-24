import os
from pathlib import Path


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        # Legacy EI CLI support (disabled by default)
        self.EI_ENABLED: bool = os.getenv("EI_ENABLED", "0").lower() in {"1", "true", "yes"}
        self.EI_CLI_PATH: str = os.getenv("EI_CLI_PATH", "")
        self.EI_OUTPUT_DIR: Path = Path(os.getenv("EI_OUTPUT_DIR", "data/ei_output")).resolve()
        self.EI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.EI_VERSION_FILE: Path = Path(os.getenv("EI_VERSION_FILE", "ei_version.txt")).resolve()

        # dps.report integration (canonical EI JSON source)
        self.DPS_REPORT_ENABLED: bool = os.getenv("DPS_REPORT_ENABLED", "1").lower() in {"1", "true", "yes"}
        self.DPS_REPORT_BASE_URL: str = os.getenv("DPS_REPORT_BASE_URL", "https://dps.report").rstrip("/")
        self.DPS_REPORT_CACHE_DIR: Path = Path(os.getenv("DPS_REPORT_CACHE_DIR", "data/dps_report")).resolve()
        self.DPS_REPORT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
