import re

from domain.common.line import Line


class Utils:

    @staticmethod
    def sort_lines(line: Line):
        # Buscar número y sufijo opcional
        match = re.match(r"L(\d+)([A-Z]?)", line.name)
        if not match:
            return (999, "")  # Los que no encajan van al final

        num = int(match.group(1))          # Número principal
        suffix = match.group(2) or ""      # Sufijo opcional

        # Queremos que los que no tienen sufijo vayan después de N/S
        suffix_order = {"N": 0, "S": 1, "": 2}
        return (num, suffix_order.get(suffix, 3))