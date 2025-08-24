import json
import os
from providers.helpers import logger

class LanguageManager:
    """
    Manages application translations by loading JSON language files
    and providing translation lookups.
    """

    def __init__(self, locales_path="locales", default_lang="en"):
        """
        Initialize the LanguageManager.

        Args:
            locales_path (str): Path to folder containing language JSON files.
            default_lang (str): Default language code.
        """
        self.locales_path = locales_path
        self.default_lang = default_lang
        self.locales = {}
        logger.info(f"[{self.__class__.__name__}] Initializing LanguageManager with default language '{default_lang}'")
        self._load_locales()

    def _load_locales(self):
        """Load all JSON files from the locales folder."""
        if not os.path.exists(self.locales_path):
            logger.warning(f"[{self.__class__.__name__}] Locales path '{self.locales_path}' does not exist")
            return

        for filename in os.listdir(self.locales_path):
            if filename.endswith(".json"):
                lang_code = filename.replace(".json", "")
                try:
                    with open(os.path.join(self.locales_path, filename), "r", encoding="utf-8") as f:
                        self.locales[lang_code] = json.load(f)
                        logger.info(f"[{self.__class__.__name__}] Loaded translations for language '{lang_code}'")
                except Exception as e:
                    logger.error(f"[{self.__class__.__name__}] Failed to load '{filename}': {e}")   
    
    def t(self, key: str, lang: str = None, **kwargs):
        """
        Return translation for the given key and language, with optional interpolation.

        Args:
            key (str): Translation key.
            lang (str, optional): Language code. Defaults to default_lang.
            **kwargs: Optional variables for string formatting.

        Returns:
            str: Translated and formatted string.
        """
        lang = lang or self.default_lang
        template = self.locales.get(lang, {}).get(key) or self.locales[self.default_lang].get(key)
        if template is None:
            return key
        if "{s}" in template:
            plural_suffix = "s" if kwargs.get("count", 0) != 1 else ""
            template = template.replace("{s}", plural_suffix)
        return template.format(**kwargs)
    
    def set_language(self, new_language: str):
        """
        Set the default language for translations.

        Args:
            new_language (str): New default language code.
        """
        logger.info(f"[{self.__class__.__name__}] Changing default language from '{self.default_lang}' to '{new_language}'")
        self.default_lang = new_language

    def get_available_languages(self):
        """
        Get the list of supported languages.

        Returns:
            List[str]: Supported language codes.
        """
        available = list(self.locales.keys())
        logger.debug(f"[{self.__class__.__name__}] Available languages: {available}")
        return available
