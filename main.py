from api import (
    get_bus_lines,
    get_bus_line_stops,
    get_metro_lines,
    get_stations_by_metro_line,
    get_next_metro_at_station,
    get_next_bus_at_stop,
    get_next_scheduled_metro_at_station,
    get_metro_station_accesses,
    get_metro_station_connections,
    get_metro_station_alerts
)
import logging, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
)

import asyncio

from favorites_manager import FavoritesManager
from secrets_manager import SecretsManager
from mapper import Mapper

# Telegram token
sm = SecretsManager()
TELEGRAM_TOKEN = sm.get('TELEGRAM_TOKEN')

# Estados
MENU, ASK_METRO_LINE, ASK_METRO_STATION, ASK_BUS_LINE, ASK_BUS_STOP = range(5)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

favorites_manager = FavoritesManager()

station_update_tasks = {}
bot_messages_to_delete = []

# Cache
metro_lines_cache = {}
metro_stations_cache = {}

bus_lines_cache = {}
bus_stops_cache = {}

def add_to_metro_lines_cache(metro_line):
    metro_lines_cache[metro_line.CODI_LINIA] = {
        "name": metro_line.NOM_LINIA,
        "description": metro_line.DESC_LINIA,
        "original_name": metro_line.ORIGINAL_NOM_LINIA,
    }

def add_to_metro_stations_cache(metro_station, metro_line_name):
    metro_stations_cache[metro_station.CODI_ESTACIO] = {
        "metro_line_name": metro_line_name,
        "station_name": metro_station.NOM_ESTACIO,
        "station_group_code": metro_station.CODI_GRUP_ESTACIO,
        "coordinates": metro_station.coordinates
    }

def add_to_bus_stops_cache(bus_stop):
    bus_stops_cache[bus_stop.CODI_PARADA] = {
        "bus_stop_name": bus_stop.NOM_PARADA,
        "coordinates": bus_stop.coordinates
    }

# Utils
def chunk_buttons(buttons, n=2):
    return [buttons[i:i + n] for i in range(0, len(buttons), n)]

def push_history(context: CallbackContext, state: int):
    context.user_data.setdefault("history", []).append(state)

def pop_history(context: CallbackContext) -> int:
    return context.user_data.get("history", []).pop() if context.user_data.get("history") else MENU

def clear_history(context: CallbackContext):
    context.user_data["history"] = []



# Keyboards
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚇 Metro", callback_data="metro")],
        [InlineKeyboardButton("🚌 Bus", callback_data="bus")],
        [InlineKeyboardButton("♥️ Favorites", callback_data="favorites")]
    ])

def get_metro_lines_keyboard():
    metro_lines = get_metro_lines()
    [add_to_metro_lines_cache(metro_line) for metro_line in metro_lines]

    buttons = [
        [InlineKeyboardButton(f"{line.NOM_LINIA} - {line.DESC_LINIA}", callback_data=f"metro_line:{line.CODI_LINIA}")]
        for line in metro_lines
    ]
    buttons.append([InlineKeyboardButton("🔙 Volver", callback_data="back")])
    return InlineKeyboardMarkup(buttons)

def get_bus_lines_keyboard():
    bus_lines = get_bus_lines()
    buttons = [
        InlineKeyboardButton(f"{line.NOM_LINIA}", callback_data=f"bus_line:{line.CODI_LINIA}:{line.NOM_LINIA}")
        for line in bus_lines
    ]
    rows = chunk_buttons(buttons, 5)
    buttons.append([InlineKeyboardButton("🔙 Volver", callback_data="back")])
    return InlineKeyboardMarkup(rows)

def get_metro_stations_keyboard(line_id, line_name):
    stations = get_stations_by_metro_line(line_id)
    [add_to_metro_stations_cache(station, line_name) for station in stations]
    mapper = Mapper()
    encoded = mapper.map_metro_stations(stations)

    buttons = [
        InlineKeyboardButton(f"{station.ORDRE_ESTACIO}. {station.NOM_ESTACIO}", callback_data=f"metro_station:{station.CODI_ESTACIO}")
        for station in stations
    ]

    rows = []
    rows = chunk_buttons(buttons, 2)
    rows.append([InlineKeyboardButton("🗺️ Mapa", web_app=WebAppInfo(url=f"https://mg-diego.github.io/Metro-Bus-BCN/map.html?data={encoded}"))])
    rows.append([InlineKeyboardButton("🔙 Volver", callback_data="back")])
    return InlineKeyboardMarkup(rows)

def get_metro_station_access_keyboard(group_station_code):
    station_accesses = get_metro_station_accesses(group_station_code)
    buttons = [
        InlineKeyboardButton(f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}", url=f"https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}")
        for access in station_accesses
    ]
    rows = chunk_buttons(buttons, 2)
    return InlineKeyboardMarkup(rows)

def get_bus_line_stops_keyboard(line_id):
    from_origin, from_destination = get_bus_line_stops(line_id)

    [add_to_bus_stops_cache(stop) for stop in from_origin]
    [add_to_bus_stops_cache(stop) for stop in from_destination]
    
    mapper = Mapper()
    encoded = mapper.map_bus_stops(from_origin, from_destination)

    from_origin_buttons = [
        InlineKeyboardButton(
            f"⏩ ({stop.CODI_PARADA}) {stop.NOM_PARADA}",
            callback_data=f"bus_stop:{stop.CODI_PARADA}"
        )
        for stop in from_origin
    ]

    from_destination_buttons = [
        InlineKeyboardButton(
            f"⏪ ({stop.CODI_PARADA}) {stop.NOM_PARADA}",
            callback_data=f"bus_stop:{stop.CODI_PARADA}"
        )
        for stop in from_destination
    ]

    # Crear filas con dos columnas (una de cada sentido)
    rows = []
    max_len = max(len(from_origin_buttons), len(from_destination_buttons))
   # for i in range(max_len):
    #    col1 = from_origin_buttons[i] if i < len(from_origin_buttons) else None
   #     col2 = from_destination_buttons[i] if i < len(from_destination_buttons) else None
   #     row = [btn for btn in (col1, col2) if btn is not None]
   #     rows.append(row)

    # Botón de volver al final
    rows.append([InlineKeyboardButton("🗺️ Mapa", web_app=WebAppInfo(url=f"https://mg-diego.github.io/Metro-Bus-BCN/map.html?data={encoded}"))])
    rows.append([InlineKeyboardButton("🔙 Volver", callback_data="back")])

    return InlineKeyboardMarkup(rows)

def create_favorite_keyboard(is_favorite: bool, item_type:str, item_id: str):
    if is_favorite:
        fav_button = InlineKeyboardButton("💔 Quitar de Favoritos", callback_data=f"remove_fav:{item_type}:{item_id}")
    else:
        fav_button = InlineKeyboardButton("♥️ Añadir a Favoritos", callback_data=f"add_fav:{item_type}:{item_id}")

    keyboard = InlineKeyboardMarkup([
        [
            fav_button,
            InlineKeyboardButton("❌ Cerrar", callback_data="close_station_info")
        ]
    ])
    return keyboard




# Handlers
async def start(update: Update, context: CallbackContext) -> int:
    return await search(update, context)

async def search(update: Update, context: CallbackContext) -> int:
    message = await update.message.reply_text(
        f"👋 ¡Hola {update.effective_user.first_name}! \n\n¿Qué te gustaría hacer?",
        reply_markup=get_main_menu_keyboard()
    )
    bot_messages_to_delete.append(message)
    return MENU

async def go_back(query, context: CallbackContext) -> int:
    prev_state = pop_history(context)

    if prev_state == MENU:
        await query.edit_message_text("Bienvenido. Elige una opción:", reply_markup=get_main_menu_keyboard())
        return MENU
    elif prev_state == ASK_METRO_LINE:
        await query.edit_message_text(f"⏳ Cargando líneas de metro...")
        await query.edit_message_text("Selecciona una línea de metro:", reply_markup=get_metro_lines_keyboard())
        return ASK_METRO_LINE
    return MENU

async def menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        return await go_back(query, context)

    if data == "metro":
        push_history(context, MENU)
        await query.edit_message_text(f"⏳ Cargando líneas de metro...")
        await query.edit_message_text("Selecciona una línea de metro:", reply_markup=get_metro_lines_keyboard())
        return ASK_METRO_LINE

    if data == "bus":
        push_history(context, MENU)
        await query.edit_message_text(f"⏳ Cargando líneas de bus...")
        await query.edit_message_text("Selecciona una línea de bus:", reply_markup=get_bus_lines_keyboard())
        return ASK_BUS_LINE

    if data == "favorites":
        user_id = query.from_user.id
        favs = favorites_manager.get_all_favorites(user_id)

        fav_keyboard = []
        
        if not favs["metro"] and not favs["bus"]:
            await query.edit_message_text(
                f"Hola {query.from_user.first_name} 👋\nAún no tienes nada en tu lista de favoritos. ¡Empieza a añadir algunos para encontrarlos más rápido!"
            )
            clear_history(context)
            return ConversationHandler.END

        # Metro favorites
        if favs["metro"]:
            for item in favs["metro"]:
                metro_stations_cache[int(item.get('CODI_ESTACIO'))] = {
                    "metro_line_name": item.get('NOM_LINIA'),
                    "station_name": item.get('NOM_ESTACIO'),
                    "station_group_code": item.get("CODI_GRUP_ESTACIO"),
                    "coordinates": item.get('coordinates')
                }
                name = f"{item.get('NOM_LINIA', 'Sin nombre')} - {item.get('NOM_ESTACIO', '')}"
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚇 {name}", callback_data=f"metro_station:{item.get('CODI_ESTACIO')}")
                ])

        # Bus favorites
        if favs["bus"]:
            for item in favs["bus"]:
                bus_stops_cache[int(item.get('CODI_PARADA'))] = {
                    "bus_stop_name": item.get('NOM_PARADA'),
                    "coordinates": item.get('coordinates')
                }
                name = f"({item.get('CODI_PARADA', '')})  {item.get('NOM_PARADA', '')}"
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚌 {name}", callback_data=f"bus_stop:{item.get('CODI_PARADA')}")
                ])

        # Close button
        fav_keyboard.append([InlineKeyboardButton("❌ Cerrar", callback_data="close_favorites")])

        reply_markup = InlineKeyboardMarkup(fav_keyboard)

        await query.edit_message_text(
            "📌 Tus favoritos:",
            reply_markup=reply_markup
        )

        clear_history(context)
        return ConversationHandler.END

    return MENU

async def handle_metro_line(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    push_history(context, ASK_METRO_LINE)
    _, line_id = data.split(":")
    metro_line = metro_lines_cache.get(int(line_id))

    await query.edit_message_text(f"⏳ Cargando estaciones de la línea '{metro_line['name']}'...")

    reply_markup = get_metro_stations_keyboard(line_id, metro_line['original_name'])
    await query.edit_message_text(f"<b><u>{metro_line['name']} ({metro_line['description']})</u></b>\n\nSelecciona una estación de metro:", reply_markup=reply_markup, parse_mode="HTML")

    return ASK_METRO_STATION

async def handle_bus_line(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    push_history(context, ASK_BUS_LINE)
    _, line_id, line_name = data.split(":")
    await query.edit_message_text(f"⏳ Cargando la línea de bus '{line_id}'...")
    reply_markup = get_bus_line_stops_keyboard(line_id)
    await query.edit_message_text(
        f"🚌 - <b>Línea {line_name}</b>\n\n"
        "Selecciona una parada de bus:\n"
        "   ⏩ = sentido ida\n"
        "   ⏪ = sentido vuelta",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return ASK_BUS_STOP

async def handle_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back":
        return await go_back(query, context)

    return MENU

async def add_fav_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    _, item_type, item_id = data.split(":")

    # Añadir favorito
    cache = metro_stations_cache if item_type == "metro" else bus_stops_cache
    cache_item = cache.get(int(item_id))

    if item_type == "metro":
        new_fav_item = {
            "CODI_ESTACIO": item_id,
            "NOM_ESTACIO": cache_item["station_name"],
            "CODI_GRUP_ESTACIO": cache_item["station_group_code"],
            "NOM_LINIA": cache_item["metro_line_name"],
            "coordinates": cache_item["coordinates"]
        }
    if item_type == "bus":
        new_fav_item = {
            "CODI_PARADA": item_id,
            "NOM_PARADA": cache_item["bus_stop_name"],
            "coordinates": cache_item["coordinates"]
        }
    favorites_manager.add_favorite(user_id, item_type, new_fav_item)

    # Actualizar teclado con botón para quitar favorito
    keyboard = create_favorite_keyboard(is_favorite=True, item_type=item_type, item_id=item_id)
    await query.edit_message_reply_markup(reply_markup=keyboard)
    await query.answer(text="Añadido a favoritos ❤️", show_alert=True)

async def remove_fav_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    _, item_type, item_id = data.split(":")

    # Quitar favorito
    favorites_manager.remove_favorite(user_id, item_type, item_id)

    # Actualizar teclado con botón para añadir favorito
    keyboard = create_favorite_keyboard(is_favorite=False, item_type=item_type, item_id=item_id)
    await query.edit_message_reply_markup(reply_markup=keyboard)
    await query.answer(text="Eliminado de favoritos 💔", show_alert=True)

async def handle_detailed_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    user_id = query.from_user.id

    if data == "close_station_info":
        metro_lines_cache = {}
        task = station_update_tasks.pop(user_id, None)
        if task:
            task.cancel()

        # Editar el mensaje original para informar que se está limpiando
        await query.edit_message_text("🧹 Limpiando mensajes antiguos... un momento, por favor.")

        # Borrar los mensajes antiguos
        for message in bot_messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
            except Exception as e:
                logger.warning(f"No se pudo borrar mensaje: {e}")

        # Finalmente, enviar mensaje nuevo de confirmación
        await context.bot.send_message(chat_id=query.message.chat_id, text="✅ ¡Búsqueda finalizada!\n\n¿Te gustaría buscar otra vez?\n\nEscribe /search y la empezamos 🔍")

        return ConversationHandler.END

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

        return ASK_METRO_STATION

    if data.startswith("bus_stop:"):
        _, bus_stop_id = data.split(":")

        bus_stop = bus_stops_cache.get(int(bus_stop_id))

        desc_text = (
            f"🚏 <b>PARADA '{bus_stop["bus_stop_name"].upper()}'</b> 🚏"
        )
        await query.edit_message_text(text=desc_text, parse_mode='HTML')
        bot_messages_to_delete.append(query.message)

        location_message = await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=bus_stop["coordinates"][1],
            longitude=bus_stop["coordinates"][0]
        )
        
        bot_messages_to_delete.append(location_message)

        # Primer mensaje
        message = await context.bot.send_message(chat_id=query.message.chat_id, text="⏳ Cargando información de la parada...")
        bot_messages_to_delete.append(message)

        async def update_loop():
            while True:
                next_buses = get_next_bus_at_stop(bus_stop_id)
                formatted_routes = "\n\n".join(str(route) for route in next_buses)

                text = (
                    f"🚉 <u>Próximos Buses:</u>\n{formatted_routes} \n\n"
                    f"🚨 <u>Alertas:</u> \n - TBD"
                )

                is_fav = favorites_manager.has_favorite(user_id, "bus", bus_stop_id)
                keyboard = create_favorite_keyboard(is_fav, "bus", bus_stop_id)

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

        return ASK_BUS_STOP

    clear_history(context)
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operación cancelada.")
    clear_history(context)
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "ℹ️ <b>Ayuda del MetroBus Bot de Transporte</b> ℹ️\n\n"
        "Este bot te permite consultar información actualizada sobre el <b>Metro</b> y <b>Bus</b> de la ciudad de Barcelona de forma rápida.\n\n"
        "📋 <u>Comandos disponibles:</u>\n"
        "  • /start o /search – Inicia una nueva búsqueda\n"
        "  • /help – Muestra este mensaje de ayuda\n\n"
        "🚇 Para ver los próximos metros:\n"
        "  1. Pulsa en 'Metro' en el menú.\n"
        "  2. Selecciona una línea.\n"
        "  3. Selecciona una estación.\n"
        "  4. Verás los horarios actualizados y más detalles.\n\n"
        "🚌 Función de Bus y Favoritos estará disponible pronto 😉\n\n"
        "¿Tienes dudas o sugerencias? ¡Estoy aquí para ayudarte!\n\n"
        "📬 <b>Contacto:</b> <a href='https://github.com/mg-diego'>github.com/mg-diego</a>"

    )

    await update.message.reply_text(help_text, parse_mode='HTML')

# Main
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search), CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu)],
            ASK_METRO_LINE: [CallbackQueryHandler(handle_metro_line)],
            ASK_BUS_LINE: [CallbackQueryHandler(handle_bus_line)],
        },
        fallbacks=[MessageHandler(filters.Regex("^cancelar$"), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_detailed_selection, pattern=r"^metro_station:|^bus_stop:|close_station_info"))
    application.add_handler(CallbackQueryHandler(add_fav_callback, pattern=r"^add_fav:"))
    application.add_handler(CallbackQueryHandler(remove_fav_callback, pattern=r"^remove_fav:"))
    application.run_polling()

if __name__ == "__main__":
    main()
