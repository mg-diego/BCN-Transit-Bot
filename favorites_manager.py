import json
import os
from typing import Dict, List, Any

class FavoritesManager:
    def __init__(self, storage_path: str = "favorites.json"):
        self.storage_path = storage_path
        self._favorites: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._load()

    # --- Internal persistence helpers ---
    def _load(self):
        """Load favorites from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._favorites = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._favorites = {}
        else:
            self._favorites = {}

    def _save(self):
        """Save favorites to JSON file."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._favorites, f, ensure_ascii=False, indent=2)

    # --- Public API ---
    def add_favorite(self, user_id: int, fav_type: str, item: Dict[str, Any]):
        """
        Add an item to the user's favorites.
        fav_type: 'metro' or 'bus'
        item: dict with minimal data (e.g., ID, name, coordinates)
        """
        user_id_str = str(user_id)
        if user_id_str not in self._favorites:
            self._favorites[user_id_str] = {"metro": [], "bus": []}

        # Avoid duplicates by ID
        favorite_type_key = "CODI_ESTACIO" if fav_type == "metro" else "CODI_PARADA"
        existing_ids = {f.get(favorite_type_key) for f in self._favorites[user_id_str][fav_type]}
        if item.get(favorite_type_key) not in existing_ids:
            self._favorites[user_id_str][fav_type].append(item)
            self._save()
            return True
        return False

    def remove_favorite(self, user_id: int, fav_type: str, item_id: Any):
        """
        Remove an item from the user's favorites by ID.
        """
        user_id_str = str(user_id)
        
        if user_id_str in self._favorites and fav_type in self._favorites[user_id_str]:
            before_count = len(self._favorites[user_id_str][fav_type])
            favorite_type_key = "CODI_ESTACIO" if fav_type == "metro" else "CODI_PARADA"

            self._favorites[user_id_str][fav_type] = [
                fav for fav in self._favorites[user_id_str][fav_type] if fav.get(favorite_type_key) != str(item_id)
            ]
            if len(self._favorites[user_id_str][fav_type]) != before_count:
                self._save()
                return True
        return False

    def list_favorites(self, user_id: int, fav_type: str) -> List[Dict[str, Any]]:
        """
        Get all favorites for a given type ('metro' or 'bus') for a user.
        """
        return self._favorites.get(str(user_id), {}).get(fav_type, [])

    def has_favorite(self, user_id: int, fav_type: str, item_id: Any) -> bool:
        """
        Check if an item is already in favorites.
        """
        if fav_type == "metro":
            return any(fav.get("CODI_ESTACIO") == item_id for fav in self.list_favorites(user_id, fav_type))
        if fav_type == "bus":
            return any(fav.get("CODI_PARADA") == item_id for fav in self.list_favorites(user_id, fav_type))


    def get_all_favorites(self, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return all favorites grouped by type for the user.
        """
        return self._favorites.get(str(user_id), {"metro": [], "bus": []})

        