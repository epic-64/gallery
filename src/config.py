"""Configuration management for the image processing application."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "number_mode": "suffix",  # "prefix" or "suffix"
    "separator": " ",
}

CONFIG_FILENAME = "woop_config.json"


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to the configuration file in the user's home directory.
    """
    # Store config in user's home directory
    home = Path.home()
    config_dir = home / ".woop"
    config_dir.mkdir(exist_ok=True)
    return config_dir / CONFIG_FILENAME


def load_config() -> dict:
    """Load configuration from file.

    Returns:
        Dictionary with configuration values. Returns defaults if file doesn't exist.
    """
    config_path = get_config_path()

    if not config_path.exists():
        logger.info("No configuration file found, using defaults")
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")

        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        return merged_config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> bool:
    """Save configuration to file.

    Args:
        config: Dictionary with configuration values to save.

    Returns:
        True if successful, False otherwise.
    """
    config_path = get_config_path()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False
