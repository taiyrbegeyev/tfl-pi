"""
Clock module for displaying current time and date.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from PIL import Image, ImageDraw
from lib.modules.base_module import BaseModule
from lib.display.renderer import Renderer

logger = logging.getLogger(__name__)


class ClockModule(BaseModule):
    """Module for displaying current time and date."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the clock module.

        Args:
            config: Module configuration
        """
        super().__init__(config)
        self.time_format = config.get('time_format', '%H:%M')
        self.date_format = config.get('date_format', '%A, %d %B %Y')
        self.show_seconds = config.get('show_seconds', False)
        self.font_size = config.get('font_size', 24)

        self.current_time = None
        self.current_date = None

    def update(self) -> bool:
        """
        Update the current time and date.

        Returns:
            bool: Always True (time always updates)
        """
        try:
            now = datetime.now()

            if self.show_seconds:
                self.current_time = now.strftime('%H:%M:%S')
            else:
                self.current_time = now.strftime(self.time_format)

            self.current_date = now.strftime(self.date_format)

            logger.debug(f"Clock updated: {self.current_time}")
            return True

        except Exception as e:
            logger.error(f"Failed to update clock: {e}")
            return False

    def render(self, image: Image.Image, draw: ImageDraw.Draw) -> None:
        """
        Render the clock onto the image.

        Args:
            image: PIL Image to draw on
            draw: PIL ImageDraw object
        """
        if not self.current_time:
            self.update()

        try:
            x, y = self.position
            width, height = self.size

            # Get fonts
            time_font = Renderer.get_bold_font(self.font_size)
            date_font = Renderer.get_default_font(self.font_size // 2)

            # Draw time
            draw.text((x, y), self.current_time, font=time_font, fill=0)

            # Draw date below time
            date_y = y + self.font_size + 5
            draw.text((x, date_y), self.current_date, font=date_font, fill=0)

            logger.debug(f"Clock rendered at {self.position}")

        except Exception as e:
            logger.error(f"Failed to render clock: {e}")
