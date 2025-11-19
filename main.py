#!/usr/bin/env python3
"""
TfL Pi - Transport for London E-Paper Display
Main application entry point.
"""
import logging
import sys
import time
import signal
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_manager import ConfigManager
from lib.display.epd_driver import EPDDriver
from lib.display.renderer import Renderer
from lib.api.tfl_client import TfLClient
from lib.modules.clock import ClockModule
from lib.modules.tfl_departures import TfLDeparturesModule

# Configure logging - only log warnings and errors to prevent filling storage
# When running as systemd service, logs go to journalctl which has automatic rotation
logging.basicConfig(
    level=logging.WARNING,  # Only log WARNING, ERROR, and CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class TfLPiApp:
    """Main application class for TfL Pi."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the application.

        Args:
            config_path: Path to configuration file
        """
        self.running = False
        self.config_manager = None
        self.epd = None
        self.renderer = None
        self.tfl_client = None
        self.modules = []
        self.config_path = config_path

    def setup(self) -> None:
        """Setup the application components."""
        logger.info("Starting TfL Pi application...")

        # Load configuration
        try:
            self.config_manager = ConfigManager(self.config_path)
            self.config_manager.load()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

        # Initialize display
        mock_mode = self.config_manager.is_mock_mode()
        self.epd = EPDDriver(mock_mode=mock_mode)
        try:
            self.epd.init()
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            sys.exit(1)

        # Initialize renderer
        width, height = EPDDriver.get_dimensions()
        self.renderer = Renderer(width, height)

        # Initialize API clients
        tfl_api_key = self.config_manager.get_tfl_api_key()
        self.tfl_client = TfLClient(api_key=tfl_api_key)

        # Initialize modules
        self._setup_modules()

        logger.info("Application setup complete")

    def _setup_modules(self) -> None:
        """Setup all display modules based on configuration."""
        modules_config = self.config_manager.get('modules', {})

        # Clock module
        clock_config = modules_config.get('clock', {})
        if clock_config.get('enabled', True):
            clock = ClockModule(clock_config)
            self.modules.append(clock)
            logger.info("Clock module enabled")

        # TfL Departures module
        departures_config = modules_config.get('departures', {})
        if departures_config.get('enabled', True):
            # Merge departures configuration
            full_config = {**self.config_manager.get_departures_config(), **departures_config}
            departures = TfLDeparturesModule(full_config, self.tfl_client)
            self.modules.append(departures)
            logger.info("TfL Departures module enabled")

        logger.info(f"Initialized {len(self.modules)} modules")

    def update_modules(self) -> None:
        """Update all modules with fresh data."""
        for module in self.modules:
            try:
                module.update()
            except Exception as e:
                logger.error(f"Failed to update module {module.name}: {e}")

    def render_display(self) -> None:
        """Render all modules and update the display."""
        try:
            image = self.renderer.render_modules(self.modules)
            self.epd.display(image)
        except Exception as e:
            logger.error(f"Failed to render display: {e}")

    def run(self) -> None:
        """Main application loop."""
        self.running = True
        refresh_interval = self.config_manager.get_refresh_interval()

        logger.info(f"Starting main loop (refresh interval: {refresh_interval}s)")

        try:
            while self.running:
                # Update data and render display
                self.update_modules()
                self.render_display()

                # Sleep until next update
                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            pass  # Normal shutdown, no need to log
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Cleanup resources before exit."""
        logger.info("Cleaning up...")
        self.running = False

        if self.epd:
            try:
                self.epd.sleep()
                self.epd.close()
            except Exception as e:
                logger.error(f"Error during display cleanup: {e}")

        logger.info("Application stopped")

    def handle_signal(self, signum, frame) -> None:
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point."""
    # Create application instance
    app = TfLPiApp()

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)

    # Setup and run
    try:
        app.setup()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
