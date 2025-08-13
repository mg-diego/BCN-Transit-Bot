class NavigationHistory:
    def __init__(self):
        self.history = {}  # {user_id: [menu_stack]}

    def push(self, user_id: int, menu_id: str):
        """
        Añade un nuevo menú al historial del usuario.
        Evita añadir duplicados consecutivos.
        """
        if user_id not in self.history:
            self.history[user_id] = []
        if not self.history[user_id] or self.history[user_id][-1] != menu_id:
            self.history[user_id].append(menu_id)

    def pop(self, user_id: int) -> str | None:
        """
        Retrocede un paso y devuelve el menú anterior.
        Si no hay historial, devuelve None.
        """
        if user_id in self.history and len(self.history[user_id]) > 1:
            self.history[user_id].pop()  # Eliminar menú actual
            return self.history[user_id][-1]  # Devolver anterior
        return None

    def clear(self, user_id: int):
        """Borra el historial del usuario."""
        self.history.pop(user_id, None)

    def get_current(self, user_id: int) -> str | None:
        """Devuelve el menú actual del usuario."""
        if user_id in self.history and self.history[user_id]:
            return self.history[user_id][-1]
        return None
