"""
E-Paper Display driver wrapper for Waveshare 7.5inch e-Paper HAT.
Provides a clean interface and mock mode for development without hardware.
"""
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class EPDDriver:
    """
    Wrapper for Waveshare 7.5inch e-Paper display driver.
    Supports both real hardware and mock mode for development.
    """

    # Display specifications for Waveshare 7.5" e-Paper HAT
    WIDTH = 800
    HEIGHT = 480

    def __init__(self, mock_mode: bool = False):
        """
        Initialize the e-paper display driver.

        Args:
            mock_mode: If True, run in mock mode without hardware
        """
        self.mock_mode = mock_mode
        self.epd = None

        if not mock_mode:
            try:
                # Try to import the Waveshare driver
                # The actual driver files need to be downloaded from Waveshare
                from waveshare_epd import epd7in5_V2
                self.epd = epd7in5_V2.EPD()
                logger.info("Waveshare EPD driver loaded successfully")
            except ImportError:
                logger.warning(
                    "Waveshare EPD driver not found. Running in mock mode. "
                    "To use real hardware, install the Waveshare driver from: "
                    "https://github.com/waveshare/e-Paper"
                )
                self.mock_mode = True
        else:
            logger.info("Running in mock mode (no hardware)")

    def init(self) -> None:
        """Initialize the display."""
        if not self.mock_mode and self.epd:
            try:
                logger.info("Initializing e-paper display...")
                self.epd.init()
                self.epd.Clear()
                logger.info("Display initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize display: {e}")
                raise
        else:
            logger.info("Mock mode: Display initialization skipped")

    def display(self, image: Image.Image) -> None:
        """
        Display an image on the e-paper screen.

        Args:
            image: PIL Image object to display (should be 800x480)
        """
        if image.size != (self.WIDTH, self.HEIGHT):
            logger.warning(
                f"Image size {image.size} doesn't match display size "
                f"({self.WIDTH}x{self.HEIGHT}). Resizing..."
            )
            image = image.resize((self.WIDTH, self.HEIGHT))

        if not self.mock_mode and self.epd:
            try:
                # Convert image to 1-bit mode if needed
                if image.mode != '1':
                    image = image.convert('1')
                self.epd.display(self.epd.getbuffer(image))
            except Exception as e:
                logger.error(f"Failed to update display: {e}")
                raise
        else:
            # Mock mode: save image to file for debugging
            output_path = "/tmp/epd_mock_output.png"
            image.save(output_path)
            logger.debug(f"Mock mode: Display image saved to {output_path}")

    def sleep(self) -> None:
        """Put the display into sleep mode to save power."""
        if not self.mock_mode and self.epd:
            try:
                logger.info("Putting display to sleep...")
                self.epd.sleep()
            except Exception as e:
                logger.error(f"Failed to put display to sleep: {e}")
        else:
            logger.info("Mock mode: Sleep command skipped")

    def clear(self) -> None:
        """Clear the display."""
        if not self.mock_mode and self.epd:
            try:
                logger.info("Clearing display...")
                self.epd.Clear()
            except Exception as e:
                logger.error(f"Failed to clear display: {e}")
        else:
            logger.info("Mock mode: Clear command skipped")

    def close(self) -> None:
        """Close the display and cleanup resources."""
        if not self.mock_mode and self.epd:
            try:
                logger.info("Closing display...")
                self.epd.Dev_exit()
            except Exception as e:
                logger.error(f"Failed to close display: {e}")
        else:
            logger.info("Mock mode: Close command skipped")

    @classmethod
    def get_dimensions(cls) -> tuple:
        """
        Get display dimensions.

        Returns:
            tuple: (width, height)
        """
        return (cls.WIDTH, cls.HEIGHT)
