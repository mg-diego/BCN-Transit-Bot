import urllib.parse

class GoogleMapsHelper:
    """
    Helper to generate Google Maps URLs for directions with customizable options.
    """

    @staticmethod
    def build_directions_url(latitude: float, longitude: float, travel_mode: str = "walking") -> str:
        """
        Builds a Google Maps URL for directions from the user's current location
        to the given coordinates.

        Args:
            latitude (float): Destination latitude.
            longitude (float): Destination longitude.
            travel_mode (str): Travel mode. Options: 'driving', 'walking', 'bicycling', 'transit'.
                               Default is 'walking'.

        Returns:
            str: A complete Google Maps URL.
        """
        # Ensure travel_mode is valid, fallback to "transit"
        valid_modes = {"driving", "walking", "bicycling", "transit"}
        if travel_mode not in valid_modes:
            travel_mode = "walking"

        # Encode origin
        origin = urllib.parse.quote("Current Location")

        # Build URL
        maps_url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}"
            f"&destination={latitude},{longitude}"
            f"&travelmode={travel_mode}"
            f"&basemap=roadmap"
        )

        return maps_url
