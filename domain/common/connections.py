

from dataclasses import dataclass
from domain.common.line import Line


@dataclass
class Connections:
    lines: list[Line]