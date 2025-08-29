import unicodedata
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
    

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza un texto eliminando acentos, símbolos especiales y espacios extra.

        Args:
            text (str): Texto original.

        Returns:
            str: Texto limpio, sin acentos ni caracteres especiales.
        """
        # 1. Normalizar el texto a forma NFD para separar caracteres base y diacríticos
        text = unicodedata.normalize('NFD', text)

        # 2. Eliminar los diacríticos (acentos, tildes, etc.)
        text = ''.join(
            char for char in text 
            if unicodedata.category(char) != 'Mn'
        )

        # 3. Eliminar cualquier caracter que no sea alfanumérico, espacio o guion bajo
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # 4. Convertir múltiples espacios en uno solo
        text = re.sub(r'\s+', ' ', text)

        # 5. Eliminar espacios al inicio y final
        return text.strip()
