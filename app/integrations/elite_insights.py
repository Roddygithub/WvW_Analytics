import json
import subprocess
from pathlib import Path
from typing import Dict

from app.config import settings


class EliteInsightsError(RuntimeError):
    """Raised when Elite Insights CLI fails."""


class EliteInsightsClient:
    """
    Thin wrapper around the Elite Insights CLI.

    Assumptions (documented):
    - EI_CLI_PATH points to the executable (e.g. /opt/elite-insights/GW2EIParser.exe or dotnet /opt/elite-insights/GW2EIParser.dll).
    - We call: <cli> -c <input> -o <output_dir> --json
    - EI writes JSON to <output_dir>/<input_stem>.json
    """

    def __init__(self, cli_path: str, output_dir: Path) -> None:
        self.cli_path = cli_path
        self.output_dir = output_dir

    def run(self, input_path: Path) -> tuple[Dict, Path]:
        """
        Run EI CLI synchronously and return parsed JSON.
        """
        if not self.cli_path:
            raise EliteInsightsError("EI_CLI_PATH is not configured.")
        if not input_path.exists():
            raise EliteInsightsError(f"Input log not found: {input_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            *self.cli_path.split(" "),
            "-c",
            str(input_path),
            "-o",
            str(self.output_dir),
            "--json",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise EliteInsightsError(
                f"Elite Insights failed (code {result.returncode}): {result.stderr or result.stdout}"
            )

        # EI typically outputs <stem>.json in the output directory
        json_path = self.output_dir / f"{input_path.stem}.json"
        if not json_path.exists():
            # If not found, try to locate the most recent JSON file in output_dir
            candidates = sorted(self.output_dir.glob(f"{input_path.stem}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not candidates:
                raise EliteInsightsError(f"Elite Insights JSON not found for {input_path.stem}")
            json_path = candidates[0]

        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f), json_path


def get_ei_client() -> EliteInsightsClient:
    return EliteInsightsClient(settings.EI_CLI_PATH, settings.EI_OUTPUT_DIR)
