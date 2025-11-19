"""
Base module class for all display modules.
Inspired by Inkycal's modular architecture.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw


class BaseModule(ABC):
    """
    Abstract base class for all display modules.
    Each module is responsible for rendering a specific piece of information
    (e.g., clock, weather, departures) on a designated area of the display.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the module with configuration.

        Args:
            config: Dictionary containing module configuration
        """
        self.config = config
        self.position = config.get('position', (0, 0))  # (x, y) tuple
        self.size = config.get('size', (100, 100))  # (width, height) tuple
        self.enabled = config.get('enabled', True)
        self.name = self.__class__.__name__

    @abstractmethod
    def update(self) -> bool:
        """
        Fetch fresh data for the module.

        Returns:
            bool: True if update was successful, False otherwise
        """
        pass

    @abstractmethod
    def render(self, image: Image.Image, draw: ImageDraw.Draw) -> None:
        """
        Render the module content onto the provided image.

        Args:
            image: PIL Image object to draw on
            draw: PIL ImageDraw object for drawing operations
        """
        pass

    def get_bounds(self) -> tuple:
        """
        Get the bounding box for this module.

        Returns:
            tuple: (x, y, x + width, y + height)
        """
        x, y = self.position
        width, height = self.size
        return (x, y, x + width, y + height)

    def is_enabled(self) -> bool:
        """Check if the module is enabled."""
        return self.enabled

    def __repr__(self) -> str:
        return f"{self.name}(position={self.position}, size={self.size})"
