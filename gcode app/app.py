# code app/app.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from domain import MachineState, GCodeLine, GCodeCommand
from parser import parse_gcode
from services import execute_line, calculate_distance_to_go


class GCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("G-Code Simulator with Step & Speed Control")
        self.root.geometry("1200x800")

        self.lines = []
        self.state = MachineState()
        self.current_line_idx = 0
        self.is_playing = False
        self.animation_id = None

        # --- Layout ---
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left: Editor
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)

        ttk.Label(left_frame, text="G-Code Input:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5)
        self.editor = scrolledtext.ScrolledText(left_frame, font=("Consolas", 11), undo=True)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.editor.tag_config("current_line", background="yellow")

        # Right: Controls + Output + Plot
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Controls
        ctrl_frame = ttk.LabelFrame(right_frame, text="Simulation Controls")
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(ctrl_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.step_btn = ttk.Button(btn_frame, text="Step →", command=self.step_simulation)
        self.step_btn.pack(side=tk.LEFT, padx=5)

        self.play_btn = ttk.Button(btn_frame, text="Play ▶", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Speed slider
        speed_frame = ttk.Frame(ctrl_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=0.5)
        self.speed_slider = ttk.Scale(speed_frame, from_=0.1, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="0.5s")
        self.speed_label.pack(side=tk.LEFT)
        self.speed_var.trace("w", self.update_speed_label)

        # Progress
        self.progress_var = tk.StringVar(value="Line: 0 / 0")
        ttk.Label(ctrl_frame, textvariable=self.progress_var).pack(pady=5)

        # Results
        ttk.Label(right_frame, text="Machine State", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5, pady=(10,0))
        self.result_text = tk.Text(right_frame, height=10, font=("Consolas", 10), bg="#f0f0f0")
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Backplot
        ttk.Label(right_frame, text="Top View Backplot (X-Y)", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5, pady=(10,0))
        self.canvas = tk.Canvas(right_frame, bg="white", height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.load_sample()

    def update_speed_label(self, *args):
        delay = self.speed_var.get()
        self.speed_label.config(text=f"{delay:.2f}s")

    def load_sample(self):
        sample = """G21         ; Set millimeters
G90         ; Absolute positioning
G0 Z5       ; Rapid to safe height
G0 X0 Y0    ; Home XY
G1 Z-2 F100 ; Plunge
G1 X100 Y0  ; Cut right
G1 X100 Y100 ; Cut up
G1 X0 Y100  ; Cut left
G1 X0 Y0    ; Cut down
G0 Z5       ; Retract
M30         ; End program"""
        self.editor.insert("1.0", sample)

    def parse_and_prepare(self):
        code = self.editor.get("1.0", tk.END)
        self.lines = parse_gcode(code)
        if not self.lines:
            messagebox.showwarning("No Code", "No valid G-code lines found.")
            return False
        return True

    def reset_simulation(self):
        if self.is_playing:
            self.toggle_play()
        self.state = MachineState()
        self.current_line_idx = 0
        self.update_display()
        self.clear_highlight()
        self.progress_var.set(f"Line: 0 / {len(self.lines)}")

    def step_simulation(self):
        if not self.lines and not self.parse_and_prepare():
            return

        if self.current_line_idx >= len(self.lines):
            messagebox.showinfo("Complete", "Simulation finished!")
            return

        line = self.lines[self.current_line_idx]
        execute_line(self.state, line)

        # Highlight current line in editor
        self.highlight_current_line()

        self.current_line_idx += 1
        self.update_display()
        self.progress_var.set(f"Line: {self.current_line_idx} / {len(self.lines)}")

    def toggle_play(self):
        if not self.lines and not self.parse_and_prepare():
            return

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.config(text="Pause ❚❚")
            self.step_btn.config(state=tk.DISABLED)
            self.animate()
        else:
            self.play_btn.config(text="Play ▶")
            self.step_btn.config(state=tk.NORMAL)
            if self.animation_id:
                self.root.after_cancel(self.animation_id)
                self.animation_id = None

    def animate(self):
        if not self.is_playing or self.current_line_idx >= len(self.lines):
            self.toggle_play()  # auto-stop
            messagebox.showinfo("Complete", "Simulation finished!")
            return

        self.step_simulation()
        delay_ms = int(self.speed_var.get() * 1000)
        self.animation_id = self.root.after(delay_ms, self.animate)

    def highlight_current_line(self):
        self.clear_highlight()
        if self.current_line_idx == 0:
            return
        line_num = self.current_line_idx  # 1-based for editor
        start = f"{line_num}.0"
        end = f"{line_num}.end"
        self.editor.tag_add("current_line", start, end)
        self.editor.see(start)

    def clear_highlight(self):
        self.editor.tag_remove("current_line", "1.0", tk.END)

    def update_display(self):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "=== Current Machine State ===\n")
        x, y, z = self.state.position
        self.result_text.insert(tk.END, f"Position: X{x:.3f} Y{y:.3f} Z{z:.3f}\n")
        self.result_text.insert(tk.END, f"Distance to Go: {calculate_distance_to_go(self.state)} mm\n\n")
        self.result_text.insert(tk.END, "=== Modals ===\n")
        for k, v in self.state.modals.items():
            self.result_text.insert(tk.END, f"{k.replace('_', ' ').title()}: {v}\n")
        self.result_text.insert(tk.END, f"\nMoves executed: {len(self.state.toolpath)}\n")

        self.draw_backplot()

    def draw_backplot(self):
        self.canvas.delete("all")
        toolpath = self.state.toolpath
        if not toolpath:
            return

        # Bounds
        xs = [p for seg in toolpath for p in (seg[0][0], seg[1][0])]
        ys = [p for seg in toolpath for p in (seg[0][1], seg[1][1])]
        margin = 30
        w = self.canvas.winfo_width() - 2*margin if self.canvas.winfo_width() > 1 else 500
        h = 280

        if max(xs) == min(xs): xs.append(min(xs) + 1)
        if max(ys) == min(ys): ys.append(min(ys) + 1)

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_range = x_max - x_min if x_max > x_min else 1
        y_range = y_max - y_min if y_max > y_min else 1

        def to_canvas(x, y):
            cx = margin + (x - x_min) / x_range * w
            cy = margin + (1 - (y - y_min) / y_range) * (h - 2*margin)
            return cx, cy

        # Draw path
        for i, (start, end) in enumerate(toolpath):
            sx, sy = to_canvas(start[0], start[1])
            ex, ey = to_canvas(end[0], end[1])
            color = "red" if start[2] != end[2] or (abs(end[0]-start[0]) < 0.001 and abs(end[1]-start[1]) < 0.001) else "blue"
            width = 3 if i == len(toolpath)-1 else 2  # highlight current move
            self.canvas.create_line(sx, sy, ex, ey, fill=color, width=width, arrow=tk.LAST if color=="blue" else tk.NONE)

        # Start point
        if toolpath:
            fx, fy = to_canvas(toolpath[0][0][0], toolpath[0][0][1])
            self.canvas.create_oval(fx-6, fy-6, fx+6, fy+6, fill="green", outline="darkgreen", width=2)

        # Current position
        cx, cy = to_canvas(self.state.position[0], self.state.position[1])
        self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill="orange", outline="black")

# --------------------------- Main ---------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeApp(root)
    root.mainloop()