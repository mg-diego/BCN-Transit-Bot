import re

class HtmlHelper:

    @staticmethod
    def clean_text(text):
        # 1. Quitar etiquetas HTML como <br>
        text = re.sub(r'<.*?>', '', text)

        # 2. Decodificar secuencias de escape unicode (como \u00b7)
        text = bytes(text, "utf-8").decode("unicode_escape")

        # 3. Quitar secuencias como \n o \t si quedan
        text = text.replace('\\n', '\n').replace('\\t', '\t')

        # 4. Opcional: limpiar espacios extra
        text = text.strip()
        return text