from dataclasses import dataclass, field
from typing import List, Optional

from domain.common.alert import Alert
from domain.common.line import Line
from domain.transport_type import TransportType
from providers.helpers.html_helper import HtmlHelper

@dataclass(kw_only=True)
class Station:
    id: int
    code: int
    name: str
    latitude: float
    longitude: float
    order: int
    transport_type: TransportType
    name_with_emoji: Optional[str] = None
    description: Optional[str] = None
    line_id: Optional[int] = None
    line_code: Optional[int] = None
    line_color: Optional[str] = None
    line_name: Optional[str] = None
    line_name_with_emoji: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[List[Alert]] = field(default_factory=list)
    connections: Optional[List[Line]] = field(default_factory=list)

    @staticmethod
    def get_alert_by_language(station, language: str):
        raw_alerts = []
        if station.has_alerts:
            raw_alerts.extend(
                getattr(alert, f'text{language.capitalize()}')
                for alert in station.alerts
            )
        return "\n".join(f"<pre>{alert}</pre>" for alert in set(raw_alerts))
    
    @staticmethod
    def update_station_with_connections(station, connections: List[Line]):
        station.connections = connections
        return station