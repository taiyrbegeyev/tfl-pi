"""
PIL-based rendering engine for composing the display layout.
Manages the canvas and coordinates module rendering.
"""
import logging
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class Renderer:
    """
    Rendering engine that manages the PIL canvas and coordinates
    all module rendering operations.
    """

    def __init__(self, width: int, height: int):
        """
        Initialize the renderer.

        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.image = None
        self.draw = None

    def create_canvas(self) -> Image.Image:
        """
        Create a fresh white canvas for rendering.

        Returns:
            PIL Image object
        """
        # Create white background (1-bit mode for e-paper: 0=black, 255=white)
        self.image = Image.new('1', (self.width, self.height), 255)
        self.draw = ImageDraw.Draw(self.image)
        logger.debug(f"Created canvas: {self.width}x{self.height}")
        return self.image

    def render_modules(self, modules: List) -> Image.Image:
        """
        Render all enabled modules onto the canvas.

        Args:
            modules: List of BaseModule instances to render

        Returns:
            PIL Image with all modules rendered
        """
        self.create_canvas()

        for module in modules:
            if module.is_enabled():
                try:
                    logger.debug(f"Rendering module: {module.name}")
                    module.render(self.image, self.draw)
                except Exception as e:
                    logger.error(f"Failed to render module {module.name}: {e}")

        return self.image

    def draw_text(
        self,
        text: str,
        position: tuple,
        font: Optional[ImageFont.FreeTypeFont] = None,
        fill: int = 0
    ) -> None:
        """
        Helper method to draw text on the canvas.

        Args:
            text: Text to draw
            position: (x, y) tuple for text position
            font: PIL Font object (None for default)
            fill: Fill color (0=black, 255=white for e-paper)
        """
        if self.draw is None:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")

        self.draw.text(position, text, font=font, fill=fill)

    def draw_line(
        self,
        start: tuple,
        end: tuple,
        fill: int = 0,
        width: int = 1
    ) -> None:
        """
        Helper method to draw a line on the canvas.

        Args:
            start: (x, y) tuple for line start
            end: (x, y) tuple for line end
            fill: Line color (0=black, 255=white)
            width: Line width in pixels
        """
        if self.draw is None:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")

        self.draw.line([start, end], fill=fill, width=width)

    def draw_rectangle(
        self,
        bbox: tuple,
        outline: int = 0,
        fill: Optional[int] = None,
        width: int = 1
    ) -> None:
        """
        Helper method to draw a rectangle on the canvas.

        Args:
            bbox: (x1, y1, x2, y2) bounding box
            outline: Outline color (0=black, 255=white)
            fill: Fill color (None for transparent)
            width: Line width in pixels
        """
        if self.draw is None:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")

        self.draw.rectangle(bbox, outline=outline, fill=fill, width=width)

    @staticmethod
    def get_default_font(size: int = 12) -> Optional[ImageFont.FreeTypeFont]:
        """
        Get a default font for rendering text.

        Args:
            size: Font size in points

        Returns:
            PIL Font object or None if font not available
        """
        try:
            # Try to load a common system font
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except OSError:
            try:
                # Fallback to another common font
                return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", size)
            except OSError:
                logger.warning("Could not load TrueType font, using default")
                return ImageFont.load_default()

    @staticmethod
    def get_bold_font(size: int = 12) -> Optional[ImageFont.FreeTypeFont]:
        """
        Get a bold font for rendering text.

        Args:
            size: Font size in points

        Returns:
            PIL Font object or None if font not available
        """
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except OSError:
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size)
            except OSError:
                logger.warning("Could not load bold font, using default")
                return Renderer.get_default_font(size)

    def get_canvas(self) -> Optional[Image.Image]:
        """
        Get the current canvas image.

        Returns:
            PIL Image object or None if not created
        """
        return self.image
