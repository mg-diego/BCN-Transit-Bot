class BoolConverter:
    """
    Static utility class to safely convert strings to boolean values.
    Supports common textual representations:
    'true', 'false', '1', '0', 'yes', 'no', 'y', 'n', 't', 'f'.
    """

    TRUE_VALUES = {"true", "1", "yes", "y", "t"}
    FALSE_VALUES = {"false", "0", "no", "n", "f"}

    @staticmethod
    def from_string(value: str, default: bool = False) -> bool:
        """
        Converts a string to a boolean.

        Args:
            value (str): The string to convert.
            default (bool): Value to return if the string is unrecognized.

        Returns:
            bool: Converted boolean value.
        """
        if not isinstance(value, str):
            return bool(value)

        value_lower = value.strip().lower()
        if value_lower in BoolConverter.TRUE_VALUES:
            return True
        elif value_lower in BoolConverter.FALSE_VALUES:
            return False
        else:
            return default
