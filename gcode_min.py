"""
Minimal Single-File G-Code Editor & Simulator (January 2026)

A standalone, zero-dependency Python script that lets you:
- Paste or type G-code directly
- See syntax-highlighted code (basic colors)
- Run a simple simulation
- View:
    • Current position (X, Y, Z)
    • Modal state (Absolute/Incremental, Units, etc.)
    • Distance to go (remaining linear moves)
    • Basic backplot (2D top view)

Perfect for quickly testing how the core of our full app will feel.
Run with: python gcode_minimal.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# --------------------------- Domain Models ---------------------------

@dataclass
class GCodeCommand:
    code: str          # e.g., "G", "X", "M"
    value: float | str # numeric or string (rare)

@dataclass
class GCodeLine:
    number: Optional[int]
    commands: List[GCodeCommand]
    comment: Optional[str]

@dataclass
class MachineState:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # X, Y, Z
    modals: Dict[str, str | float] = None
    toolpath: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None

    def __post_init__(self):
        if self.modals is None:
            self.modals = {
                "motion": "G0",           # G0 rapid, G1 linear
                "position_mode": "G90",   # G90 absolute, G91 incremental
                "units": "G21",           # G20 inches, G21 mm
                "feed_rate": 0.0,
            }
        if self.toolpath is None:
            self.toolpath = []

# --------------------------- Simple Parser ---------------------------

def parse_gcode(text: str) -> List[GCodeLine]:
    lines = []
    for raw_line in text.splitlines():
        line_str = raw_line.strip().upper()
        if not line_str or line_str.startswith('%'):
            continue

        # Extract comment
        if ';' in line_str:
            line_str, comment = line_str.split(';', 1)
            comment = comment.strip()
        else:
            comment = None

        # Optional line number
        number = None
        if line_str.startswith('N'):
            parts = line_str.split(maxsplit=1)
            if len(parts) > 1 and parts[0][1:].isdigit():
                number = int(parts[0][1:])
                line_str = parts[1]

        # Parse commands: letter + value
        commands = []
        matches = re.finditer(r'([A-Z])([-+]?\d*\.?\d+)', line_str)
        for m in matches:
            code = m.group(1)
            value_str = m.group(2)
            try:
                value = float(value_str)
            except ValueError:
                value = value_str  # rare string values
            commands.append(GCodeCommand(code, value))

        if commands or comment:
            lines.append(GCodeLine(number, commands, comment))

    return lines

# --------------------------- Simple Simulator ---------------------------

def simulate(lines: List[GCodeLine]) -> MachineState:
    state = MachineState()
    current_pos = list(state.position)

    for line in lines:
        for cmd in line.commands:
            code = cmd.code
            val = cmd.value if isinstance(cmd.value, (int, float)) else 0.0

            # Modal G codes
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

            # Axis moves
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

            # Feed rate
            elif code == "F":
                state.modals["feed_rate"] = val

    return state

# --------------------------- Distance to Go ---------------------------

def calculate_distance_to_go(state: MachineState) -> float:
    remaining = 0.0
    for start, end in state.toolpath:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        remaining += math.sqrt(dx*dx + dy*dy + dz*dz)
    return round(remaining, 3)

# --------------------------- GUI Application ---------------------------

class GCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimal G-Code Editor & Simulator")
        self.root.geometry("1100x700")

        # --- Layout ---
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: Editor
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)

        ttk.Label(left_frame, text="G-Code Input (paste or type):", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5)
        self.editor = scrolledtext.ScrolledText(left_frame, font=("Consolas", 11), undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right: Output & Plot
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Simulation Results", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5)

        self.result_text = tk.Text(right_frame, height=12, font=("Consolas", 10), bg="#f0f0f0")
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas for simple backplot
        ttk.Label(right_frame, text="Top View Backplot (X-Y)", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5, pady=(10,0))
        self.canvas = tk.Canvas(right_frame, bg="white", height=250)
        self.canvas.pack(fill=tk.X, padx=5, pady=5)

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Simulate", command=self.run_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Sample G-code
        self.load_sample()

    def load_sample(self):
        sample = """G21         ; millimeters
G90         ; absolute positioning
G0 Z5       ; rapid to safe height
G0 X0 Y0
G1 Z-2 F100 ; plunge
G1 X100 Y0
G1 X100 Y100
G1 X0 Y100
G1 X0 Y0
G0 Z5       ; retract
M30         ; end program"""
        self.editor.insert("1.0", sample)

    def clear_all(self):
        self.editor.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.canvas.delete("all")

    def run_simulation(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Empty", "Please enter some G-code.")
            return

        try:
            lines = parse_gcode(code)
            state = simulate(lines)
            dist_to_go = calculate_distance_to_go(state)

            # --- Update results ---
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "=== Machine State ===\n")
            self.result_text.insert(tk.END, f"Position: X{state.position[0]:.3f} Y{state.position[1]:.3f} Z{state.position[2]:.3f}\n")
            self.result_text.insert(tk.END, f"Distance to Go: {dist_to_go} mm\n\n")
            self.result_text.insert(tk.END, "=== Modals ===\n")
            for k, v in state.modals.items():
                self.result_text.insert(tk.END, f"{k.replace('_', ' ').title()}: {v}\n")

            self.result_text.insert(tk.END, f"\nTotal moves simulated: {len(state.toolpath)}\n")

            # --- Simple backplot ---
            self.draw_backplot(state.toolpath)

        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed:\n{str(e)}")

    def draw_backplot(self, toolpath: List[Tuple[Tuple[float,float,float], Tuple[float,float,float]]]):
        self.canvas.delete("all")
        if not toolpath:
            return

        # Find bounds
        xs = [p[0] for seg in toolpath for p in seg]
        ys = [p[1] for seg in toolpath for p in seg]
        margin = 20
        w = self.canvas.winfo_width() - 2*margin if self.canvas.winfo_width() > 1 else 400
        h = 230

        if max(xs) == min(xs):
            xs.append(min(xs) + 1)
        if max(ys) == min(ys):
            ys.append(min(ys) + 1)

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_range = x_max - x_min if x_max > x_min else 1
        y_range = y_max - y_min if y_max > y_min else 1

        def to_canvas(x, y):
            cx = margin + (x - x_min) / x_range * (w)
            cy = margin + (1 - (y - y_min) / y_range) * (h - 2*margin)
            return cx, cy

        # Draw moves
        for start, end in toolpath:
            sx, sy = to_canvas(start[0], start[1])
            ex, ey = to_canvas(end[0], end[1])
            color = "red" if start == end else ("blue" if any(abs(c) > 0.001 for c in (end[0]-start[0], end[1]-start[1])) else "gray")
            self.canvas.create_line(sx, sy, ex, ey, fill=color, width=2, arrow=tk.LAST if color=="blue" else tk.NONE)

        # Start point
        if toolpath:
            fx, fy = to_canvas(toolpath[0][0][0], toolpath[0][0][1])
            self.canvas.create_oval(fx-5, fy-5, fx+5, fy+5, fill="green", outline="black")

# --------------------------- Main Entry ---------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeApp(root)
    root.mainloop()