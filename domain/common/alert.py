
from dataclasses import dataclass
from datetime import datetime
from typing import List
import html

from providers.helpers.html_helper import HtmlHelper

@dataclass
class Publication:
    headerCa: str
    headerEn: str
    headerEs: str
    textCa: str
    textEn: str
    textEs: str

@dataclass
class AffectedEntity:
    direction_code: str
    direction_name: str
    entrance_code: str
    entrance_name: str
    line_code: str
    line_name: str
    station_code: str
    station_name: str

@dataclass
class Alert:
    id: str
    begin_date: datetime
    end_date: datetime
    status: str
    cause: str
    publications: List[Publication]
    affected_entities: List[AffectedEntity]

    @staticmethod
    def map_from_metro_alert(metro_alert):
        publications = []
        for metro_alert_publication in metro_alert.get('publications'):
            publications.append(Publication(
                headerCa=metro_alert_publication.get('headerCa', None),
                headerEn=metro_alert_publication.get('headerEn', None),
                headerEs=metro_alert_publication.get('headerEs', None),
                textCa=HtmlHelper.clean_text(metro_alert_publication.get('textCa', '')),
                textEn=HtmlHelper.clean_text(metro_alert_publication.get('textEn', '')),
                textEs=HtmlHelper.clean_text(metro_alert_publication.get('textEs', '')),
            ))

        affected_entities = []
        for entity in metro_alert.get('entities'):
            affected_entities.append(AffectedEntity(
                direction_code=entity.get('direction_code'),
                direction_name=entity.get('direction_name'),
                entrance_code=entity.get('entrance_code'),
                entrance_name=entity.get('entrance_name'),
                line_code=entity.get('line_code'),
                line_name=entity.get('line_name'),
                station_code=entity.get('station_code'),
                station_name=entity.get('station_name')
            ))

        return Alert(
            id=metro_alert.get('id'),
            begin_date=datetime.fromtimestamp(metro_alert.get('disruption_dates')[0].get('begin_date', None) / 1000),
            end_date=datetime.fromtimestamp(metro_alert.get('disruption_dates')[0].get('end_date', None) / 1000),
            publications=publications,
            affected_entities=affected_entities,
            status=metro_alert.get('effect').get('status'),
            cause=metro_alert.get('cause').get('code')
        )
    
    @staticmethod
    def map_from_bus_alert(bus_alert):
        channel_info = bus_alert.get('channelInfoTO')

        publications = [Publication(
                headerCa=HtmlHelper.clean_text(bus_alert.get('typeName', '')),
                headerEn=HtmlHelper.clean_text(bus_alert.get('typeName', '')),
                headerEs=HtmlHelper.clean_text(bus_alert.get('typeName', '')),
                textCa=HtmlHelper.clean_text(channel_info.get('textCa', '')),
                textEn=HtmlHelper.clean_text(channel_info.get('textEn', '')),
                textEs=HtmlHelper.clean_text(channel_info.get('textEs', '')),
            )]
        
        affected_entities = []
        for entity in bus_alert.get('linesAffected'):
            ways = entity.get('ways')
            for way in ways:
                for stop in way.get('stops'):
                    affected_entities.append(AffectedEntity(
                        direction_code=way.get('wayId'),
                        direction_name=way.get('wayName'),
                        entrance_code=None,
                        entrance_name=None,
                        line_code=entity.get('lineId'),
                        line_name=entity.get('commercialLineId'),
                        station_code=stop.get('stopId'),
                        station_name=stop.get('stopName')
                    ))

        return Alert(
            id=bus_alert.get('id'),
            begin_date=datetime.fromtimestamp(bus_alert.get('begin') / 1000),
            end_date=datetime.fromtimestamp(bus_alert.get('end') / 1000),
            publications=publications,
            affected_entities=affected_entities,
            status=HtmlHelper.clean_text(bus_alert.get('causeName')),
            cause=bus_alert.get('categories').get('messageType')
        )