import json
import os

import requests
from google.protobuf.json_format import MessageToDict
from google.transit import gtfs_realtime_pb2


class GTFSRealtimeReader:
    """
    A class to read GTFS-Realtime (.pb) files and convert them to Python dict or JSON.

    Features:
    - Load from local .pb files or URLs.
    - Parse GTFS-Realtime feeds using Google's protobuf definition.
    - Export parsed data as dict or JSON.
    """

    def __init__(self, source: str, is_url: bool = False):
        """
        Initialize the GTFSRealtimeReader.

        :param source: Path to the local .pb file or URL.
        :param is_url: Set to True if 'source' is a URL.
        """
        self.source = source
        self.is_url = is_url
        self.feed = gtfs_realtime_pb2.FeedMessage()
        self._raw_data = None

    def load(self):
        """
        Loads the GTFS-Realtime data from the source (local file or URL).
        """
        if self.is_url:
            print(f"Downloading GTFS-Realtime data from {self.source}...")
            response = requests.get(self.source)
            response.raise_for_status()
            self._raw_data = response.content
        else:
            if not os.path.exists(self.source):
                raise FileNotFoundError(f"File not found: {self.source}")
            print(f"Reading GTFS-Realtime data from local file: {self.source}")
            with open(self.source, "rb") as f:
                self._raw_data = f.read()

        # Parse the data
        self.feed.ParseFromString(self._raw_data)

    def to_dict(self) -> dict:
        """
        Converts the GTFS-Realtime data to a Python dictionary.
        """
        return MessageToDict(self.feed)

    def to_json(self, output_file: str = None, indent: int = 2) -> str:
        """
        Converts the GTFS-Realtime data to JSON format.

        :param output_file: If provided, save the JSON data to this file.
        :param indent: JSON indentation.
        :return: JSON string representation of the data.
        """
        json_data = json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_data)
            print(f"JSON data saved to {output_file}")
        return json_data

    def show_summary(self):
        """
        Prints a summary of entities in the GTFS-Realtime feed.
        """
        print("GTFS-Realtime Feed Summary")
        print(f"Total entities: {len(self.feed.entity)}")
        for entity in self.feed.entity[:5]:  # show only first 5
            if entity.HasField("trip_update"):
                print(f"- Trip update: {entity.trip_update.trip.trip_id}")
            if entity.HasField("vehicle"):
                print(
                    f"- Vehicle: {entity.vehicle.vehicle.id}, Position: {entity.vehicle.position}"
                )
            if entity.HasField("alert"):
                print(f"- Alert: {entity.alert.header_text.translation[0].text}")


reader = GTFSRealtimeReader("tripupdates.pb")
reader.load()
print(reader.to_dict())
