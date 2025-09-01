import unicodedata
import re

class HtmlHelper:

    @staticmethod
    def clean_text(text):
        # Quitar etiquetas HTML
        text = re.sub(r'<.*?>', '', text)

        # Si el texto contiene secuencias \uXXXX, las decodificamos
        if r"\u" in text:
            try:
                text = text.encode("utf-8").decode("unicode_escape")
            except UnicodeDecodeError:
                pass  # Si falla, lo dejamos tal cual

        # Reemplazar \n y \t por saltos reales
        text = text.replace('\\n', '\n').replace('\\t', '\t')

        # Limpiar espacios extra
        return text.strip()

    

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
    
    @staticmethod
    def custom_sort_key(line: str):
        # Buscar número y sufijo opcional
        match = re.match(r"L(\d+)([A-Z]?)", line)
        if not match:
            return (999, "")  # Los que no encajan van al final

        num = int(match.group(1))          # Número principal
        suffix = match.group(2) or ""      # Sufijo opcional

        # Queremos que los que no tienen sufijo vayan después de N/S
        suffix_order = {"N": 0, "S": 1, "": 2}
        return (num, suffix_order.get(suffix, 3))
