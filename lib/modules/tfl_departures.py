"""
TfL Departures module for displaying tube and bus arrivals in 2-panel layout.
Layout:
- Header: Station Name + Current DateTime
- Left Panel: All Underground departures (sorted by time)
- Right Panel: All Bus departures (sorted by time)
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image, ImageDraw
from lib.modules.base_module import BaseModule
from lib.api.tfl_client import TfLClient
from lib.display.renderer import Renderer

logger = logging.getLogger(__name__)


class TfLDeparturesModule(BaseModule):
    """Module for displaying TfL departures in a 2-panel layout."""

    def __init__(self, config: Dict[str, Any], tfl_client: TfLClient):
        """
        Initialize the TfL departures module.

        Args:
            config: Module configuration with stop IDs
            tfl_client: TfLClient instance
        """
        super().__init__(config)
        self.tfl_client = tfl_client

        # Station name for header
        self.station_name = config.get('station_name', 'Station')

        # Departure configurations
        self.westbound_tube = config.get('westbound_tube', {})
        self.westbound_bus = config.get('westbound_bus', {})
        self.eastbound_tube = config.get('eastbound_tube', {})
        self.eastbound_bus = config.get('eastbound_bus', {})

        # Font sizes
        self.header_font_size = config.get('header_font_size', 24)
        self.section_header_font_size = config.get('section_header_font_size', 16)
        self.departure_font_size = config.get('departure_font_size', 13)
        self.line_badge_font_size = config.get('line_badge_font_size', 11)

        # Cached departure data - now combined by mode
        self.departures = {
            'tube': [],  # All tube departures combined and sorted
            'bus': [],   # All bus departures combined and sorted
        }

    def update(self) -> bool:
        """
        Fetch departure data for all stops and combine by mode.

        Returns:
            bool: True if at least one update was successful
        """
        all_tube_departures = []
        all_bus_departures = []

        # Fetch westbound tube
        if self.westbound_tube.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.westbound_tube['stop_id'],
                direction='outbound',
                max_results=20  # Fetch more, we'll sort and limit later
            )
            if departures:
                all_tube_departures.extend(departures)
                logger.debug(f"Westbound tube: {len(departures)} arrivals")

        # Fetch eastbound tube
        if self.eastbound_tube.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.eastbound_tube['stop_id'],
                direction='inbound',
                max_results=20
            )
            if departures:
                all_tube_departures.extend(departures)
                logger.debug(f"Eastbound tube: {len(departures)} arrivals")

        # Fetch westbound bus
        if self.westbound_bus.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.westbound_bus['stop_id'],
                direction='outbound',
                max_results=20
            )
            if departures:
                all_bus_departures.extend(departures)
                logger.debug(f"Westbound bus: {len(departures)} arrivals")

        # Fetch eastbound bus
        if self.eastbound_bus.get('stop_id'):
            departures = self.tfl_client.get_arrivals(
                stop_point_id=self.eastbound_bus['stop_id'],
                direction='inbound',
                max_results=20
            )
            if departures:
                all_bus_departures.extend(departures)
                logger.debug(f"Eastbound bus: {len(departures)} arrivals")

        # Filter out buses arriving in less than 2 minutes (not enough time to catch)
        # Underground/tube shows all departures (easier to catch from platform)
        all_bus_departures = [d for d in all_bus_departures if d.get('minutes_until', 0) >= 2]

        # Sort by arrival time (no limit - fit as many as possible)
        self.departures['tube'] = sorted(
            all_tube_departures,
            key=lambda d: d.get('minutes_until', 999)
        )

        self.departures['bus'] = sorted(
            all_bus_departures,
            key=lambda d: d.get('minutes_until', 999)
        )

        logger.debug(f"Combined: {len(self.departures['tube'])} tube, {len(self.departures['bus'])} bus")

        return len(self.departures['tube']) > 0 or len(self.departures['bus']) > 0

    def render(self, image: Image.Image, draw: ImageDraw.Draw) -> None:
        """
        Render 2-panel layout with header.

        Args:
            image: PIL Image to draw on
            draw: PIL ImageDraw object
        """
        try:
            x, y = self.position
            width, height = self.size

            # Layout constants
            header_height = 50
            panel_header_height = 30
            padding = 10

            # Render header with logo and station name
            self._render_header(image, draw, x, y, width, header_height)

            # Calculate panel dimensions (two equal columns)
            content_y = y + header_height
            content_height = height - header_height
            panel_width = width // 2

            # Render left panel (Underground)
            self._render_panel(
                draw=draw,
                mode='tube',
                title='UNDERGROUND',
                x=x,
                y=content_y,
                width=panel_width,
                height=content_height,
                panel_header_height=panel_header_height,
                padding=padding
            )

            # Render right panel (Buses)
            self._render_panel(
                draw=draw,
                mode='bus',
                title='BUSES',
                x=x + panel_width,
                y=content_y,
                width=panel_width,
                height=content_height,
                panel_header_height=panel_header_height,
                padding=padding
            )

            # Draw vertical divider between panels
            mid_x = x + panel_width
            draw.line(
                [(mid_x, content_y), (mid_x, content_y + content_height)],
                fill=0,
                width=3
            )

            logger.debug("TfL departures rendered in 2-panel layout")

        except Exception as e:
            logger.error(f"Failed to render TfL departures: {e}")

    def _render_header(
        self,
        image: Image.Image,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> None:
        """
        Render header with station name and current datetime.

        Args:
            image: PIL Image to paste logo onto
            draw: PIL ImageDraw object
            x: Starting x position
            y: Starting y position
            width: Header width
            height: Header height
        """
        padding = 10

        # Get current datetime
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_date = now.strftime('%a %d %b')

        # Get fonts
        header_font = Renderer.get_bold_font(self.header_font_size)

        # Draw station name (left-aligned)
        text_x = x + padding
        text_y = y + (height // 2) - (self.header_font_size // 2)
        draw.text((text_x, text_y), self.station_name, font=header_font, fill=0)

        # Draw datetime (right-aligned)
        datetime_text = f"{current_time} {current_date}"
        datetime_bbox = draw.textbbox((0, 0), datetime_text, font=header_font)
        datetime_width = datetime_bbox[2] - datetime_bbox[0]
        datetime_x = x + width - datetime_width - padding
        draw.text((datetime_x, text_y), datetime_text, font=header_font, fill=0)

        # Draw horizontal line below header
        draw.line([(x, y + height), (x + width, y + height)], fill=0, width=2)

    def _render_panel(
        self,
        draw: ImageDraw.Draw,
        mode: str,
        title: str,
        x: int,
        y: int,
        width: int,
        height: int,
        panel_header_height: int,
        padding: int
    ) -> None:
        """
        Render a single panel (Underground or Buses).

        Args:
            draw: PIL ImageDraw object
            mode: 'tube' or 'bus'
            title: Panel title ('UNDERGROUND' or 'BUSES')
            x: Panel x position
            y: Panel y position
            width: Panel width
            height: Panel height
            panel_header_height: Height of the black header bar
            padding: Padding in pixels
        """
        # Draw black header bar
        draw.rectangle(
            [(x, y), (x + width, y + panel_header_height)],
            fill=0,
            outline=0
        )

        # Draw white title text on black background (centered)
        section_font = Renderer.get_bold_font(self.section_header_font_size)

        # Calculate text width to center it
        title_bbox = draw.textbbox((0, 0), title, font=section_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = x + (width - title_width) // 2
        title_y = y + (panel_header_height // 2) - (self.section_header_font_size // 2)
        draw.text((title_x, title_y), title, font=section_font, fill=255)  # White text

        # Get departures for this mode
        departures = self.departures.get(mode, [])

        if not departures:
            # No departures available
            departure_font = Renderer.get_default_font(self.departure_font_size)
            no_data_y = y + panel_header_height + padding * 2
            draw.text(
                (x + padding, no_data_y),
                "No departures",
                font=departure_font,
                fill=0
            )
            return

        # Calculate optimal row height to fill available space perfectly
        available_height = height - panel_header_height
        min_line_height = self.departure_font_size + 20  # Minimum height needed

        # Calculate how many rows can fit with minimum height
        max_rows = int(available_height / min_line_height)

        # Limit to available departures
        num_rows = min(max_rows, len(departures))

        # Calculate line height to perfectly fill the space
        if num_rows > 0:
            line_height = available_height // num_rows
        else:
            line_height = min_line_height

        # Render departures
        current_y = y + panel_header_height

        for idx, departure in enumerate(departures[:num_rows]):
            self._render_departure_row(
                draw=draw,
                departure=departure,
                x=x,
                y=current_y,
                width=width,
                line_height=line_height,
                padding=padding,
                is_first_row=(idx == 0)
            )

            current_y += line_height

    def _render_departure_row(
        self,
        draw: ImageDraw.Draw,
        departure: Dict[str, Any],
        x: int,
        y: int,
        width: int,
        line_height: int,
        padding: int,
        is_first_row: bool = False
    ) -> None:
        """
        Render a single departure row with line badge and destination.

        Args:
            draw: PIL ImageDraw object
            departure: Departure information dictionary
            x: Row x position
            y: Row y position
            width: Row width
            line_height: Height allocated for this row
            padding: Padding for content inside the row
            is_first_row: Whether this is the first row (skip top border)
        """
        # Draw borders (left, right, bottom, and top if not first row)
        # Left border
        draw.line([(x, y), (x, y + line_height)], fill=0, width=2)
        # Right border
        draw.line([(x + width, y), (x + width, y + line_height)], fill=0, width=2)
        # Bottom border
        draw.line([(x, y + line_height), (x + width, y + line_height)], fill=0, width=2)
        # Top border (only if not first row - first row uses header as top border)
        if not is_first_row:
            draw.line([(x, y), (x + width, y)], fill=0, width=2)

        line_name = departure.get('line_name', 'Unknown')
        destination = departure.get('destination', 'Unknown')
        minutes = departure.get('minutes_until', 0)

        # Get fonts
        badge_font = Renderer.get_bold_font(self.line_badge_font_size)
        dest_font = Renderer.get_default_font(self.departure_font_size)
        time_font = Renderer.get_bold_font(self.departure_font_size + 2)

        # Add padding to x coordinate for content
        content_x = x + padding

        # Draw line badge (black box with white text) - bigger size
        badge_width = 70
        badge_height = 28
        badge_y = y + (line_height - badge_height) // 2

        draw.rectangle(
            [(content_x, badge_y), (content_x + badge_width, badge_y + badge_height)],
            fill=0,
            outline=0
        )

        # Draw line name in white on black badge
        # Center text in badge
        badge_text_bbox = draw.textbbox((0, 0), line_name, font=badge_font)
        badge_text_width = badge_text_bbox[2] - badge_text_bbox[0]
        badge_text_x = content_x + (badge_width - badge_text_width) // 2
        badge_text_y = badge_y + (badge_height // 2) - (self.line_badge_font_size // 2)
        draw.text((badge_text_x, badge_text_y), line_name, font=badge_font, fill=255)

        # Draw destination next to badge
        dest_x = content_x + badge_width + 15
        dest_y = y + (line_height // 2) - (self.departure_font_size // 2)

        # Truncate destination if too long
        max_dest_width = width - badge_width - 150 - (2 * padding)  # Leave space for time
        while len(destination) > 0:
            dest_bbox = draw.textbbox((0, 0), destination, font=dest_font)
            dest_width = dest_bbox[2] - dest_bbox[0]
            if dest_width <= max_dest_width:
                break
            destination = destination[:-1]

        if len(destination) < len(departure.get('destination', '')):
            destination = destination[:-3] + '...'

        draw.text((dest_x, dest_y), destination, font=dest_font, fill=0)

        # Format and draw time (right-aligned with padding)
        if minutes == 0:
            time_str = "Due"
        elif minutes == 1:
            time_str = f"{minutes} min"
        else:
            time_str = f"{minutes} mins"

        time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = x + width - time_width - padding
        time_y = y + (line_height // 2) - (self.departure_font_size // 2)
        draw.text((time_x, time_y), time_str, font=time_font, fill=0)
