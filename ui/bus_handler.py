import asyncio
import logging
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from providers.mapper import Mapper

logger = logging.getLogger(__name__)

class BusHandler:
    def __init__(self, keyboard_factory, bus_service, update_manager):
        self.keyboard_factory = keyboard_factory
        self.bus_service = bus_service
        self.update_manager = update_manager

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú con todas las líneas de bus."""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(f"⏳ Cargando líneas de bus...")
        bus_lines = await self.bus_service.get_all_lines()
        reply_markup = self.keyboard_factory.bus_lines_menu(bus_lines)
        await query.edit_message_text("Elige una línea de bus:", reply_markup=reply_markup)

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las paradas de una línea."""
        query = update.callback_query
        await query.answer()
        data = query.data

        _, line_id, line_name = data.split(":")

        stops = await self.bus_service.get_stops_by_line(line_id)
        mapper = Mapper()
        encoded = mapper.map_bus_stops(stops)

        message = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"🚌 Has seleccionado la <b>Línea {line_name}</b>.\n\n"
                "Puedes explorar el mapa interactivo para elegir una parada específica. "
                "Pulsa el botón de abajo para abrir el mapa y seleccionar tu parada preferida."
            ),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded),
            parse_mode="HTML"
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Verifica si el mensaje tiene web_app_data
        if update.message and update.message.web_app_data:
            data_str = update.message.web_app_data.data  # string JSON enviado desde la webapp
            data = json.loads(data_str)
            bus_stop_id = data.get("name").split("-")[0]
            bus_stop_id = bus_stop_id.strip()           

            user_id = update.message.from_user.id

            bus_stop = self.bus_service.get_stop_by_id(bus_stop_id)

            desc_text = (
                f"🚏 <b>PARADA '{bus_stop.NOM_PARADA.upper()}'</b> 🚏"
            )
            message = await update.message.reply_text(text=desc_text, parse_mode='HTML')

            location_message = await context.bot.send_location(
                chat_id=update.message.chat_id,
                latitude=bus_stop.coordinates[1],
                longitude=bus_stop.coordinates[0]
            )

            # Primer mensaje
            message = await context.bot.send_message(text="⏳ Cargando información de la parada...", chat_id=update.message.chat_id)
            
            '''
            async def update_loop():
                while True:
                    next_buses = get_next_bus_at_stop(bus_stop_id)
                    formatted_routes = "\n\n".join(str(route) for route in next_buses)

                    text = (
                        f"🚉 <u>Próximos Buses:</u>\n{formatted_routes} \n\n"
                        f"🚨 <u>Alertas:</u> \n - TBD"
                    )

                    #is_fav = favorites_manager.has_favorite(user_id, "bus", bus_stop_id)
                    #keyboard = create_favorite_keyboard(is_fav, "bus", bus_stop_id)

                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.message.chat_id,
                            message_id=message.message_id,
                            text=text,
                            parse_mode='HTML',
                            #reply_markup=keyboard
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