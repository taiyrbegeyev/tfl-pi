"""
Configuration manager for loading and validating application settings.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration loading and validation."""

    DEFAULT_CONFIG_PATH = "config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to configuration file (default: config.json)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = {}

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create config.json from config.example.json"
            )

        logger.info(f"Loading configuration from {self.config_path}")

        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self._validate()
        logger.info("Configuration loaded successfully")

        return self.config

    def _validate(self) -> None:
        """
        Validate the configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ['tfl_api_key', 'departures']

        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration field: {field}")

        # Validate departures configuration
        departures = self.config.get('departures', {})
        required_departure_fields = ['westbound_tube', 'westbound_bus', 'eastbound_tube', 'eastbound_bus']

        for field in required_departure_fields:
            if field not in departures:
                raise ValueError(f"Missing required departures field: {field}")

        logger.debug("Configuration validation passed")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'departures.westbound_tube')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_tfl_api_key(self) -> str:
        """Get TfL API key from configuration."""
        return self.config.get('tfl_api_key', '')

    def get_refresh_interval(self) -> int:
        """Get refresh interval in seconds (default: 60)."""
        return self.config.get('refresh_interval', 60)

    def get_departures_config(self) -> Dict[str, Any]:
        """Get departures configuration."""
        return self.config.get('departures', {})

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration."""
        return self.config.get('display', {})

    def is_mock_mode(self) -> bool:
        """Check if mock mode is enabled (for development without hardware)."""
        return self.config.get('mock_mode', False)

    def __repr__(self) -> str:
        return f"ConfigManager(config_path='{self.config_path}')"
