# code app/parser.py

from typing import List
import re
from domain import MachineState, GCodeLine, GCodeCommand

def parse_gcode(text: str) -> List[GCodeLine]:
    lines = []
    for raw_line in text.splitlines():
        line_str = raw_line.strip().upper()
        if not line_str or line_str.startswith('%'):
            continue

        comment = None
        if ';' in line_str:
            line_str, comment = line_str.split(';', 1)
            comment = comment.strip()

        number = None
        if line_str.startswith('N'):
            parts = line_str.split(maxsplit=1)
            if len(parts) > 1 and parts[0][1:].isdigit():
                number = int(parts[0][1:])
                line_str = parts[1]

        commands = []
        matches = re.finditer(r'([A-Z])([-+]?\d*\.?\d+)', line_str)
        for m in matches:
            code = m.group(1)
            value_str = m.group(2)
            try:
                value = float(value_str)
            except ValueError:
                value = value_str
            commands.append(GCodeCommand(code, value))

        if commands or comment:
            lines.append(GCodeLine(number, commands, comment))

    return lines
