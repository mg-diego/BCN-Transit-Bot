import json
import os

class LanguageManager:
    def __init__(self, locales_path="locales", default_lang="en"):
        """
        Initialize the LanguageManager.

        :param locales_path: Path to the folder containing language JSON files.
        :param default_lang: Default language code.
        """
        self.locales_path = locales_path
        self.default_lang = default_lang
        self.locales = {}
        self._load_locales()

    def _load_locales(self):
        """Load all JSON files in the locales folder."""
        for filename in os.listdir(self.locales_path):
            if filename.endswith(".json"):
                lang_code = filename.replace(".json", "")
                with open(os.path.join(self.locales_path, filename), "r", encoding="utf-8") as f:
                    self.locales[lang_code] = json.load(f)

    def t(self, key, lang=None, **kwargs):
        """
        Return translation for the given key and language, with optional interpolation.
        """
        lang = lang or self.default_lang
        text = self.locales.get(lang, self.locales.get(self.default_lang, {})).get(key, key)
        return text.format(**kwargs)
    
    def set_language(self, new_language: str):
        self.default_lang = new_language

    def get_available_languages(self):
        return ["en", "es", "ca"]
