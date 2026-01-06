# code app/services.py

import math
from domain import MachineState, GCodeLine, GCodeCommand

def execute_line(state: MachineState, line: GCodeLine):
    current_pos = list(state.position)

    for cmd in line.commands:
        code = cmd.code
        val = cmd.value if isinstance(cmd.value, (int, float)) else 0.0

        if code == "G":
            g_val = int(val)
            if g_val in (0, 1):
                state.modals["motion"] = f"G{g_val}"
            elif g_val == 90:
                state.modals["position_mode"] = "G90"
            elif g_val == 91:
                state.modals["position_mode"] = "G91"
            elif g_val == 20:
                state.modals["units"] = "G20"
            elif g_val == 21:
                state.modals["units"] = "G21"

        elif code in "XYZ":
            idx = {"X": 0, "Y": 1, "Z": 2}[code]
            if state.modals["position_mode"] == "G90":
                target = val
            else:
                target = current_pos[idx] + val

            start_pos = tuple(current_pos)
            current_pos[idx] = target
            end_pos = tuple(current_pos)

            if state.modals["motion"] in ("G0", "G1"):
                state.toolpath.append((start_pos, end_pos))

            state.position = end_pos

        elif code == "F":
            state.modals["feed_rate"] = val


def calculate_distance_to_go(state: MachineState) -> float:
    remaining = 0.0
    for start, end in state.toolpath:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        remaining += math.sqrt(dx*dx + dy*dy + dz*dz)
    return round(remaining, 3)
