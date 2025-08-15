import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class MetroHandler:
    def __init__(self, keyboard_factory, metro_service, update_manager):
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.update_manager = update_manager

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú con todas las líneas de metro."""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(f"⏳ Cargando líneas de metro...")
        metro_lines = await self.metro_service.get_all_lines()
        reply_markup = self.keyboard_factory.metro_lines_menu(metro_lines)
        await query.edit_message_text("Elige una línea de metro:", reply_markup=reply_markup)

    async def show_line_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las estaciones de una línea."""
        query = update.callback_query
        await query.answer()
        data = query.data

        _, line_id = data.split(":")

        stations = await self.metro_service.get_stations_by_line(line_id)
        reply_markup = self.keyboard_factory.metro_stations_menu(stations, line_id)
        await query.edit_message_text(
            text=f"Estaciones de la línea {line_id}:",
            reply_markup=reply_markup
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la información de una estación de una línea."""
        query = update.callback_query
        await query.answer()
        data = query.data        
        user_id = query.from_user.id

        _, line_id, metro_station_id = data.split(":")

        station = await self.metro_service.get_station_by_id(metro_station_id, line_id)
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)

        desc_text = (
            f"🚏 <b>ESTACIÓN '{station.NOM_ESTACIO.upper()}'</b> 🚏\n\n"
            "Selecciona una entrada de metro para más detalles:"
        )
        await query.edit_message_text(text=desc_text, parse_mode='HTML')

        location_message = await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=station.coordinates[1],
            longitude=station.coordinates[0],
            reply_markup=self.keyboard_factory.metro_station_access_menu(station_accesses)
        )

        message = await context.bot.send_message(chat_id=query.message.chat_id, text="⏳ Cargando información de la estación...")

        routes = await self.metro_service.get_station_routes(metro_station_id)
        station_connections = await self.metro_service.get_metro_station_connections(metro_station_id)
        station_alerts = await self.metro_service.get_metro_station_alerts(line_id, metro_station_id)

        text = (
            f"🚉 <u>Próximos Metros:</u>\n{routes} \n\n"
            f"🔛 <u>Conexiones:</u> \n{station_connections}\n\n"
            f"🚨 <u>Alertas:</u> \n{station_alerts}"
        )

        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=message.message_id,
            text=text,
            parse_mode='HTML',
            #reply_markup=keyboard
        )

        async def update_loop():
            while True:
                try:
                    routes = await self.metro_service.get_station_routes(metro_station_id)

                    text = (
                        f"🚉 <u>Próximos Metros:</u>\n{routes} \n\n"
                        f"🔛 <u>Conexiones:</u> \n{station_connections}\n\n"
                        f"🚨 <u>Alertas:</u> \n{station_alerts}"
                    )

                    await context.bot.edit_message_text(
                        chat_id=query.message.chat_id,
                        message_id=message.message_id,
                        text=text,
                        parse_mode='HTML',
                        reply_markup=self.keyboard_factory.close_updates_menu(user_id)
                    )

                    await asyncio.sleep(1)

                except asyncio.CancelledError:
                    logger.info(f"Loop de actualización cancelado para usuario {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Error actualizando estación: {e}")
                    break


        self.update_manager.start_task(user_id, update_loop)


    async def close_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detiene la actualización automática de la estación."""
        query = update.callback_query
        await query.answer()
        _, user_id_str = query.data.split(":")
        user_id = int(user_id_str)

        self.update_manager.cancel_task(user_id)

        await query.edit_message_text("✅ Actualización detenida.")

        '''
        if data.startswith("metro_station:"):
        _, station_id = data.split(":")

        station = metro_stations_cache.get(int(station_id))
        print(f"station_id: {station_id}")
        print(f"station: \n{station}" )
        print(f"cache: \n{metro_stations_cache}")

        desc_text = (
            f"🚏 <b>ESTACIÓN '{station["station_name"].upper()}'</b> 🚏\n\n"
            "Selecciona una entrada de metro para más detalles:"
        )
        await query.edit_message_text(text=desc_text, parse_mode='HTML')
        bot_messages_to_delete.append(query.message)

        location_message = await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=station["coordinates"][1],
            longitude=station["coordinates"][0],
            reply_markup=get_metro_station_access_keyboard(station["station_group_code"])
        )
        bot_messages_to_delete.append(location_message)

        # Primer mensaje
        message = await context.bot.send_message(chat_id=query.message.chat_id, text="⏳ Cargando información de la estación...")
        bot_messages_to_delete.append(message)

        station_connections = get_metro_station_connections(station_id)
        formatted_connections = (
            "\n".join(str(c) for c in station_connections)
            or "      - Esta estación no tiene ninguna conexión de Metro."
        )

        station_alerts = get_metro_station_alerts(station["metro_line_name"], station_id)
        formatted_station_alerts = (
            "\n\n".join(f"- {str(a)}" for a in station_alerts)
            or "      - Esta estación no tiene ninguna alerta."
        )

        async def update_loop():
            while True:
                next_metros = get_next_metro_at_station(station_id)
               # if not any(metro_route.propers_trens for metro_route in next_metros):
            #     next_metros = get_next_scheduled_metro_at_station(station_id)
                formatted_routes = "\n\n".join(str(route) for route in next_metros)

                text = (
                    f"🚉 <u>Próximos Metros:</u>\n{formatted_routes} \n\n"
                    f"🔛 <u>Conexiones:</u> \n{formatted_connections}\n\n"
                    f"🚨 <u>Alertas:</u> \n{formatted_station_alerts}"
                )

                is_fav = favorites_manager.has_favorite(user_id, "metro", station_id)
                keyboard = create_favorite_keyboard(is_fav, "metro", station_id)

                try:
                    await context.bot.edit_message_text(
                        chat_id=query.message.chat_id,
                        message_id=message.message_id,
                        text=text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Error actualizando estación: {e}")
                    break

        # Cancelar tarea anterior si existe
        if user_id in station_update_tasks:
            station_update_tasks[user_id].cancel()

        station_update_tasks[user_id] = asyncio.create_task(update_loop())
        '''
