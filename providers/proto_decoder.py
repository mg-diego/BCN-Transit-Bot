from google.transit import gtfs_realtime_pb2

class ProtoDecoder:

    async def decode_gtfs_realtime(self, proto_data: bytes):
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(proto_data)

        with open("tram_gtfs_realtime.txt", "w", encoding="utf-8") as f:
            f.write(str(feed))
        return

        for entity in feed.entity:
            if entity.HasField("trip_update"):
                print(entity.trip_update.trip)
                break
                trip = entity.trip_update.trip
                print(f"Trip ID: {trip.trip_id}, Route ID: {trip.route_id}")

                for stop_time in entity.trip_update.stop_time_update:
                    print(f"  Stop ID: {stop_time.stop_id}")
                    if stop_time.HasField("arrival"):
                        print(f"    Arrival: {stop_time.arrival.time}")
                    if stop_time.HasField("departure"):
                        print(f"    Departure: {stop_time.departure.time}")

            elif entity.HasField("vehicle"):
                vehicle = entity.vehicle
                print(f"Vehicle ID: {vehicle.vehicle.id}, Status: {vehicle.current_status}")

            elif entity.HasField("alert"):
                alert = entity.alert
                print(f"Alert: {alert.header_text.translation[0].text}")

    def filter_feed_by_stop_id(self, proto_data: bytes, stop_id: str):
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(proto_data)

        filtered_entities = []

        for entity in feed.entity:
            if entity.HasField("trip_update"):
                matching_updates = [
                    stu for stu in entity.trip_update.stop_time_update
                    if stu.stop_id == stop_id
                ]
                if matching_updates:
                    # Clonar la entidad con solo las paradas que coinciden
                    new_entity = gtfs_realtime_pb2.FeedEntity()
                    new_entity.CopyFrom(entity)
                    new_entity.trip_update.ClearField("stop_time_update")
                    new_entity.trip_update.stop_time_update.extend(matching_updates)
                    filtered_entities.append(new_entity)

        return filtered_entities
