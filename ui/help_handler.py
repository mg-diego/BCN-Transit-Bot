from telegram import Update
from telegram.ext import ContextTypes

class HelpHandler:

    def __init__(self, message_service, keyboard_factory):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory

    HELP_TEXT = (
        "ℹ️ <b>Ayuda del MetroBus Bot de Transporte</b> ℹ️\n\n"
        "Este bot te permite consultar información actualizada sobre el <b>Metro</b> y <b>Bus</b> de la ciudad de Barcelona de forma rápida.\n\n"
        "📋 <u>Comandos disponibles:</u>\n"
        "  • /start – Inicia una nueva búsqueda\n"
        "  • /help – Muestra este mensaje de ayuda\n\n"
        "🚇 Para ver los próximos metros:\n"
        "  1. Pulsa en 'Metro' en el menú.\n"
        "  2. Selecciona una línea.\n"
        "  3. Selecciona una estación.\n"
        "  4. Verás los horarios actualizados y más detalles.\n\n"
        "🚌 Para ver los próximos buses:\n"
        "  1. Pulsa en 'Bus' en el menú.\n"
        "  2. Selecciona una línea.\n"
        "  3. Selecciona una estación desde el mapa interactivo.\n"
        "  4. Verás los horarios actualizados y más detalles.\n\n"        
        "⭐ Para ver tus favoritos:\n"
        "  1. Pulsa en 'Favoritos' en el menú.\n"
        "  2. Selecciona uno de tus favoritos (necesitas haberlo guardado previamente).\n"
        "  3. Verás los horarios actualizados y más detalles.\n\n"
        "¿Tienes dudas o sugerencias? ¡Estoy aquí para ayudarte!\n\n"
        "📬 <b>Contacto:</b> <a href='https://github.com/mg-diego'>github.com/mg-diego</a>"
    )

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, self.HELP_TEXT, reply_markup=self.keyboard_factory.help_menu())
