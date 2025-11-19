"""
TfL Departures module for displaying tube and bus arrivals in 4 quadrants.
Layout:
- Upper Left: Westbound Tubes
- Lower Left: Westbound Buses
- Upper Right: Eastbound Tubes
- Lower Right: Eastbound Buses
"""
import logging
from typing import Dict, Any, List
from PIL import Image, ImageDraw
from lib.modules.base_module import BaseModule
from lib.api.tfl_client import TfLClient
from lib.display.renderer import Renderer

logger = logging.getLogger(__name__)


class TfLDeparturesModule(BaseModule):
    """Module for displaying TfL departures in a 4-quadrant layout."""

    def __init__(self, config: Dict[str, Any], tfl_client: TfLClient):
        """
        Initialize the TfL departures module.

        Args:
            config: Module configuration with stop IDs for each quadrant
            tfl_client: TfLClient instance
        """
        super().__init__(config)
        self.tfl_client = tfl_client

        # Departure configurations for each quadrant
        self.westbound_tube = config.get('westbound_tube', {})
        self.westbound_bus = config.get('westbound_bus', {})
        self.eastbound_tube = config.get('eastbound_tube', {})
        self.eastbound_bus = config.get('eastbound_bus', {})

        # Number of departures to show per quadrant
        self.max_departures = config.get('max_departures', 5)

        # Font sizes
        self.title_font_size = config.get('title_font_size', 18)
        self.departure_font_size = config.get('departure_font_size', 14)

        # Cached departure data
        self.departures = {
            'westbound_tube': [],
            'westbound_bus': [],
            'eastbound_tube': [],
            'eastbound_bus': [],
        }

    def update(self) -> bool:
        """
        Fetch departure data for all quadrants.

        Returns:
            bool: True if at least one update was successful
        """
        success_count = 0

        # Update westbound tube
        if self.westbound_tube.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.westbound_tube['stop_id'],
                direction='outbound',  # TfL API uses 'outbound' for westbound
                max_results=self.max_departures
            )
            if departures:
                self.departures['westbound_tube'] = departures
                success_count += 1
                logger.debug(f"Westbound tube: {len(departures)} arrivals")

        # Update westbound bus
        if self.westbound_bus.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.westbound_bus['stop_id'],
                direction='outbound',
                max_results=self.max_departures
            )
            if departures:
                self.departures['westbound_bus'] = departures
                success_count += 1
                logger.debug(f"Westbound bus: {len(departures)} arrivals")

        # Update eastbound tube
        if self.eastbound_tube.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.eastbound_tube['stop_id'],
                direction='inbound',  # TfL API uses 'inbound' for eastbound
                max_results=self.max_departures
            )
            if departures:
                self.departures['eastbound_tube'] = departures
                success_count += 1
                logger.debug(f"Eastbound tube: {len(departures)} arrivals")

        # Update eastbound bus
        if self.eastbound_bus.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.eastbound_bus['stop_id'],
                direction='inbound',
                max_results=self.max_departures
            )
            if departures:
                self.departures['eastbound_bus'] = departures
                success_count += 1
                logger.debug(f"Eastbound bus: {len(departures)} arrivals")

        return success_count > 0

    def render(self, image: Image.Image, draw: ImageDraw.Draw) -> None:
        """
        Render all 4 quadrants of departures.

        Args:
            image: PIL Image to draw on
            draw: PIL ImageDraw object
        """
        try:
            x, y = self.position
            width, height = self.size

            # Calculate quadrant dimensions
            quad_width = width // 2
            quad_height = height // 2

            # Calculate positions for each quadrant
            quadrants = {
                'westbound_tube': (x, y),  # Upper left
                'eastbound_tube': (x + quad_width, y),  # Upper right
                'westbound_bus': (x, y + quad_height),  # Lower left
                'eastbound_bus': (x + quad_width, y + quad_height),  # Lower right
            }

            # Render each quadrant
            for quad_name, quad_pos in quadrants.items():
                self._render_quadrant(
                    draw=draw,
                    quadrant_name=quad_name,
                    position=quad_pos,
                    size=(quad_width, quad_height)
                )

            # Draw dividing lines
            self._draw_dividers(draw, x, y, width, height)

            logger.debug("TfL departures rendered")

        except Exception as e:
            logger.error(f"Failed to render TfL departures: {e}")

    def _render_quadrant(
        self,
        draw: ImageDraw.Draw,
        quadrant_name: str,
        position: tuple,
        size: tuple
    ) -> None:
        """
        Render a single quadrant with departures.

        Args:
            draw: PIL ImageDraw object
            quadrant_name: Name of the quadrant (e.g., 'westbound_tube')
            position: (x, y) position of the quadrant
            size: (width, height) size of the quadrant
        """
        x, y = position
        width, height = size

        # Get fonts
        title_font = Renderer.get_bold_font(self.title_font_size)
        departure_font = Renderer.get_default_font(self.departure_font_size)
        time_font = Renderer.get_bold_font(self.departure_font_size + 2)

        # Determine title
        titles = {
            'westbound_tube': 'Westbound Tubes',
            'eastbound_tube': 'Eastbound Tubes',
            'westbound_bus': 'Westbound Buses',
            'eastbound_bus': 'Eastbound Buses',
        }
        title = titles.get(quadrant_name, quadrant_name)

        # Draw title with padding
        padding = 10
        title_x = x + padding
        title_y = y + padding
        draw.text((title_x, title_y), title, font=title_font, fill=0)

        # Get departures for this quadrant
        departures = self.departures.get(quadrant_name, [])

        if not departures:
            # No departures available
            no_data_y = title_y + self.title_font_size + 15
            draw.text(
                (title_x, no_data_y),
                "No departures",
                font=departure_font,
                fill=0
            )
            return

        # Render each departure
        current_y = title_y + self.title_font_size + 15
        line_height = self.departure_font_size + 8

        for i, departure in enumerate(departures):
            if current_y + line_height > y + height - padding:
                break  # Don't overflow quadrant

            # Format departure info
            line_name = departure.get('line_name', 'Unknown')
            destination = departure.get('destination', 'Unknown')
            minutes = departure.get('minutes_until', 0)

            # Truncate destination if too long
            if len(destination) > 20:
                destination = destination[:17] + '...'

            # Format time
            if minutes == 0:
                time_str = "Due"
            elif minutes == 1:
                time_str = "1 min"
            else:
                time_str = f"{minutes} min"

            # Draw line name/bus number (bold)
            draw.text((title_x, current_y), line_name, font=departure_font, fill=0)

            # Draw destination (regular)
            dest_x = title_x + 60  # Offset for destination
            draw.text((dest_x, current_y), destination, font=departure_font, fill=0)

            # Draw time (bold, right-aligned within quadrant)
            time_x = x + width - padding - 60  # Right align with padding
            draw.text((time_x, current_y), time_str, font=time_font, fill=0)

            current_y += line_height

    def _draw_dividers(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """
        Draw dividing lines between quadrants.

        Args:
            draw: PIL ImageDraw object
            x: Starting x position
            y: Starting y position
            width: Total width
            height: Total height
        """
        # Vertical divider
        mid_x = x + width // 2
        draw.line([(mid_x, y), (mid_x, y + height)], fill=0, width=2)

        # Horizontal divider
        mid_y = y + height // 2
        draw.line([(x, mid_y), (x + width, mid_y)], fill=0, width=2)
