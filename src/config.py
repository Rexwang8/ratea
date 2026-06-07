# src/config.py
import os
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Paths to configuration file and derived directories
# ---------------------------------------------------------------------------
_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

# Base directories computed once from the script location — not in YAML
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "src"))
_DATA_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "data"))
_BACKUP_DIR = os.path.abspath(os.path.join(_BASE_DIR, "..", "backup"))
_FONTS_DIR = os.path.join(_SRC_DIR, "fonts")

# ---------------------------------------------------------------------------
# Load raw data from YAML
# ---------------------------------------------------------------------------
def _load_yaml() -> dict[str, Any]:
    """Read config.yaml and return the parsed dictionary."""
    with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_raw = _load_yaml()

def load_env_as_dict(filepath=".env"):
    config = {}
    # Check .env exists before trying to read it
    if not os.path.isfile(filepath):
        print(f"Warning: {filepath} not found. Environment variables will not be loaded. Create a .env to continue!")
        return config
    with open(filepath, "r") as file:
        for line in file:
            # Clean up spacing and ignore comments/empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Split at the first '=' sign only
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    return config
_env_config = load_env_as_dict(os.path.join(_SRC_DIR, "./.env"))

# ---------------------------------------------------------------------------
# Config class — provides typed attribute access matching the old API
# ---------------------------------------------------------------------------
class Config:
    """Application configuration, sourced from config.yaml.

    Every attribute maps to a value defined in the YAML file.  Any value that
    is purely a Python runtime construct (e.g. computed paths) lives at module
    level above with a leading underscore but is also mirrored here for
    backwards compatibility.
    """


    SEARCH_DEFAULTS_HIDE_REVIEWED: bool = _raw["search_defaults"]["hide_reviewed"]
    SEARCH_DEFAULTS_HIDE_FINISHED: bool = _raw["search_defaults"]["hide_finished"]
    SEARCH_DEFAULTS_HIDE_UNREVIEWED: bool = _raw["search_defaults"]["hide_unreviewed"]
    SEARCH_DEFAULTS_HIDE_FINISHED_REVIEWS: bool = _raw["search_defaults"]["hide_finished_reviews"]

    # -- Computed Paths (not from YAML) --------------------------------------
    BASE_DIR: str = _BASE_DIR
    SRC_DIR: str = _SRC_DIR
    DATA_DIR: str = _DATA_DIR
    BACKUP_DIR: str = _BACKUP_DIR
    FONTS_DIR: str = _FONTS_DIR

    # -- Review Defaults -----------------------------------------------------
    DEFAULT_RATING: str = _raw["review_defaults"]["rating"]
    DEFAULT_AMOUNT_DRUNK: float = _raw["review_defaults"]["amount_drunk_grams"]
    DEFAULT_STEEPS: int = _raw["review_defaults"]["steep_count"]
    DEFAULT_VESSEL_SIZE: float = _raw["review_defaults"]["vessel_size_ml"]
    DEFAULT_TAILING_STATEMENT: str = _raw["review_defaults"]["tailing_statement"]
    DEFAULT_FOOTER_STATEMENT: str = _raw["review_defaults"]["footer_statement"]

    # -- UI Settings ---------------------------------------------------------
    THEME: str = _raw["ui"]["theme"]
    LANGUAGE: str = _raw["ui"]["language"]
    UI_SCALE: float = _raw["ui"]["scale"]
    DEFAULT_WIDTH: int = _raw["ui"]["window_width"]
    DEFAULT_HEIGHT: int = _raw["ui"]["window_height"]

    # -- App Metadata --------------------------------------------------------
    APP_NAME: str = _raw["app"]["name"]
    VERSION: str = _raw["app"]["version"]

    # -- TeaDB Integration (Experimental) ------------------------------------
    TEADB_API_BASE_URL: str = _raw["teadb"]["api_base_url"]
    TEADB_TOKEN: str = _env_config.get("TEADB_API_KEY", "")
    TEADB_INTEGRATION_ENABLED: bool = _raw["teadb"]["enabled"]
    TEADB_MAPPING_FILE_PATH: str = os.path.join(
        _SRC_DIR, "connectors", "teadb", _raw["teadb"]["mapping_file"]
    )
    TEADB_RAW_DATA_FILE_PATH: str = os.path.join(
        _SRC_DIR, "connectors", "teadb", _raw["teadb"]["raw_data_file"]
    )

    # -- Colors (RGBA) -------------------------------------------------------
    # Keep the nested Colors class so callers can still do Config.Colors.TEXT_WHITE
    class Colors:
        TEXT_WHITE: tuple[int, ...] = tuple(_raw["colors"]["text_white"])
        TEXT_RED: tuple[int, ...] = tuple(_raw["colors"]["text_red"])
        TEXT_GREEN: tuple[int, ...] = tuple(_raw["colors"]["text_green"])
        CELL_AUTOCALC: tuple[int, ...] = tuple(_raw["colors"]["cell_autocalc"])
        CELL_INVALID: tuple[int, ...] = tuple(_raw["colors"]["cell_invalid"])
        CELL_LIGHT_BLUE: tuple[int, ...] = tuple(_raw["colors"]["cell_light_blue"])
        CELL_LIGHT_YELLOW: tuple[int, ...] = tuple(_raw["colors"]["cell_light_yellow"])
        CELL_LIGHT_GREEN: tuple[int, ...] = tuple(_raw["colors"]["cell_light_green"])
        CELL_DARK_GREEN: tuple[int, ...] = tuple(_raw["colors"]["cell_dark_green"])

    # -- Logging -------------------------------------------------------------
    DEBUG_LEVEL: str = _raw["logging"]["level"]

    # -- Font Settings -------------------------------------------------------
    DEFAULT_FONT: str = _raw["fonts"]["default"]
    VALID_FONTS: list[str] = _raw["fonts"]["valid"]

    # -- Adjustment Types ----------------------------------------------------
    TYPES_OF_ADJUSTMENTS_TO_TEA: list[str] = _raw["adjustment_types"]