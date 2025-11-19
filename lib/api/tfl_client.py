"""
TfL (Transport for London) API client for fetching real-time arrival data.
Documentation: https://api.tfl.gov.uk/
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TfLClient:
    """Client for interacting with the TfL Unified API."""

    BASE_URL = "https://api.tfl.gov.uk"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TfL API client.

        Args:
            api_key: TfL API key (optional but recommended to avoid rate limits)
        """
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            # Add API key to all requests
            self.session.params = {'app_key': api_key}
            logger.info("TfL API client initialized with API key")
        else:
            logger.warning(
                "TfL API client initialized without API key. "
                "Rate limits may apply. Register at https://api.tfl.gov.uk/"
            )

    def get_arrivals(
        self,
        stop_point_id: str,
        line_ids: Optional[List[str]] = None,
        direction: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get arrival predictions for a specific stop point.

        Args:
            stop_point_id: The stop point ID
            line_ids: Optional list of line IDs to filter by
            direction: Optional direction filter ('inbound', 'outbound')
            max_results: Maximum number of results to return

        Returns:
            List of arrival dictionaries sorted by arrival time
        """
        try:
            url = f"{self.BASE_URL}/StopPoint/{stop_point_id}/Arrivals"
            logger.debug(f"Fetching arrivals for stop: {stop_point_id}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            arrivals = response.json()
            logger.debug(f"Received {len(arrivals)} arrivals")

            # Filter by line IDs if specified
            if line_ids:
                arrivals = [
                    a for a in arrivals
                    if a.get('lineId') in line_ids
                ]

            # Filter by direction if specified
            if direction:
                direction_lower = direction.lower()
                arrivals = [
                    a for a in arrivals
                    if a.get('direction', '').lower() == direction_lower
                ]

            # Sort by time to station (seconds)
            arrivals.sort(key=lambda x: x.get('timeToStation', 999999))

            # Limit results
            arrivals = arrivals[:max_results]

            # Parse and clean the data
            return [self._parse_arrival(a) for a in arrivals]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch arrivals for {stop_point_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching arrivals: {e}")
            return []

    def _parse_arrival(self, arrival: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and clean arrival data.

        Args:
            arrival: Raw arrival data from API

        Returns:
            Cleaned arrival dictionary
        """
        return {
            'line_id': arrival.get('lineId', 'Unknown'),
            'line_name': arrival.get('lineName', 'Unknown'),
            'destination': arrival.get('destinationName', 'Unknown'),
            'platform': arrival.get('platformName', ''),
            'direction': arrival.get('direction', ''),
            'time_to_station': arrival.get('timeToStation', 0),  # seconds
            'minutes_until': arrival.get('timeToStation', 0) // 60,  # minutes
            'expected_arrival': arrival.get('expectedArrival', ''),
            'current_location': arrival.get('currentLocation', ''),
            'towards': arrival.get('towards', ''),
            'mode': arrival.get('modeName', 'tube'),  # tube, bus, etc.
        }

    def get_stop_point_info(self, stop_point_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stop point.

        Args:
            stop_point_id: The stop point ID

        Returns:
            Dictionary with stop point information or None if not found
        """
        try:
            url = f"{self.BASE_URL}/StopPoint/{stop_point_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            return {
                'id': data.get('id'),
                'name': data.get('commonName', 'Unknown'),
                'modes': data.get('modes', []),
                'lines': [line.get('name') for line in data.get('lines', [])],
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch stop point info: {e}")
            return None

    def get_line_status(self, line_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get status information for specific lines.

        Args:
            line_ids: List of line IDs (e.g., ['district', 'dlr'])

        Returns:
            List of line status dictionaries
        """
        try:
            line_ids_str = ','.join(line_ids)
            url = f"{self.BASE_URL}/Line/{line_ids_str}/Status"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            statuses = response.json()

            return [
                {
                    'line_id': status.get('id'),
                    'line_name': status.get('name'),
                    'status': status.get('lineStatuses', [{}])[0].get('statusSeverityDescription', 'Unknown'),
                }
                for status in statuses
            ]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch line status: {e}")
            return []

    def search_stop_points(
        self,
        query: str,
        modes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for stop points by name.

        Args:
            query: Search query (e.g., 'Limehouse')
            modes: Optional list of modes to filter by (e.g., ['tube', 'bus'])

        Returns:
            List of matching stop points
        """
        try:
            url = f"{self.BASE_URL}/StopPoint/Search"
            params = {'query': query}

            if modes:
                params['modes'] = ','.join(modes)

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            matches = data.get('matches', [])

            return [
                {
                    'id': match.get('id'),
                    'name': match.get('name'),
                    'modes': match.get('modes', []),
                }
                for match in matches
            ]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search stop points: {e}")
            return []
