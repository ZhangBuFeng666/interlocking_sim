from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .interlocking import InterlockingController
from .model import SignalAspect, SwitchPosition, TrackState, build_station


TRACK_GEOMETRY = {
    "JXG": [(50, 170, 120, 170)],
    "IIAG-A": [(120, 170, 185, 170)],
    "IIAG-B": [(185, 170, 250, 170)],
    "3G-L": [(250, 170, 330, 90)],
    "3G-M": [(330, 90, 780, 90)],
    "3G-R": [(780, 90, 880, 170)],
    "IIG-L": [(250, 170, 460, 170)],
    "IIG-M": [(460, 170, 670, 170)],
    "IIG-R": [(670, 170, 880, 170)],
    "1G-L": [(320, 170, 420, 245)],
    "1G-M": [(420, 245, 680, 245)],
    "1G-R": [(680, 245, 880, 245)],
    "1G-RT": [(880, 245, 950, 170)],
    "右咽喉": [(880, 170, 950, 170)],
    "IIBG-A": [(950, 170, 1010, 170)],
    "IIBG-B": [(1010, 170, 1060, 170)],
    "JSG": [(1060, 170, 1150, 170)],
    "安全线-A": [(210, 245, 300, 245)],
    "安全线-B": [(300, 245, 420, 245)],
}
TRACK_LABELS = {
    "JXG": (78, 193), "IIAG": (182, 193), "3G": (540, 72), "IIG": (560, 152),
    "1G": (560, 228), "IIBG": (1006, 152), "JSG": (1105, 152), "安全线": (246, 226),
}
SWITCH_GEOMETRY = {"1": (250, 170), "3": (320, 170), "5": (360, 245), "4": (880, 170), "2": (950, 170)}
SIGNAL_GEOMETRY = {
    "X": (120, 150), "D1": (180, 150), "S3": (430, 110), "SII": (430, 190), "S1": (430, 265),
    "PZA": (330, 275), "X3": (760, 110), "XII": (760, 190), "X1": (760, 265), "D2": (1010, 190), "S": (1070, 190),
}
SIGNAL_TRACK_Y = {"X": 170, "D1": 170, "S3": 90, "SII": 170, "S1": 245, "PZA": 245, "X3": 90, "XII": 170, "X1": 245, "D2": 170, "S": 170}
BUTTON_SIGNALS = {"S3", "SII", "S1", "X3", "XII", "X1"}
TERMINAL_POINTS = {"PZA"}

TRACK_CLEAR = "#9a641f"
TRACK_LOCKED = "#2563eb"
TRACK_OCCUPIED = "#ef4444"
SIGNAL_OPEN = "#22c55e"
SIGNAL_CLOSED = "#bfc5cf"
SIGNAL_BROKEN = "#f97316"
BUTTON_PURPLE = "#d946ef"


class InterlockingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("计算机联锁模拟仿真系统")
        self.geometry("1280x880")
        self.state_model = build_station()
        self.controller = InterlockingController(self.state_model)
        self.selected_track = tk.StringVar(value="JXG")
        self.selected_signal = tk.StringVar(value="X")
        self._build_ui()
        self._refresh()
        self.after(1000, self._loop)

    def _build_ui(self) -> None:
        self.canvas = tk.Canvas(self, bg="white", width=1200, height=380, highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas.pack(fill=tk.X, padx=10, pady=8)
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.BOTH, padx=8)
        self._build_route_buttons(left)
        self._build_switch_buttons(left)
        self._build_sim_buttons(left)
        self._build_status_panel(right)

    def _build_route_buttons(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X)
        train = ttk.LabelFrame(frame, text="列车作业")
        train.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=3)
        for title, route in [
            ("接车至 3G", "X至3G接车"), ("接车至 IIG", "X至IIG接车"), ("接车至 1G", "X至1G接车"),
            ("3G 发车", "3G至S发车"), ("IIG 发车", "IIG至S发车"), ("1G 发车", "1G至S发车"), ("通过作业", "X至S通过"),
        ]:
            ttk.Button(train, text=title, command=lambda r=route: self.controller.request_route(r)).pack(side=tk.LEFT, padx=2, pady=4)
        shunt = ttk.LabelFrame(frame, text="调车作业")
        shunt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=3)
        for title, route in [("D1 至 1G 调车", "D1至1G调车"), ("D2 至 IIG 调车", "D2至IIG调车"), ("安全线调车", "安全线调车")]:
            ttk.Button(shunt, text=title, command=lambda r=route: self.controller.request_route(r)).pack(side=tk.LEFT, padx=2, pady=4)
        control = ttk.LabelFrame(parent, text="进路控制")
        control.pack(fill=tk.X, padx=4, pady=3)
        ttk.Button(control, text="取消当前进路", command=lambda: self.controller.cancel_route()).pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(control, text="人工解锁", command=lambda: self.controller.cancel_route(manual=True)).pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(control, text="自动解锁", command=self.controller.auto_unlock).pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(control, text="清除所有进路", command=self.controller.clear_all_routes).pack(side=tk.LEFT, padx=3, pady=4)

    def _build_switch_buttons(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="单道岔操作、单锁、封锁")
        frame.pack(fill=tk.X, padx=4, pady=3)
        for name in ["1", "2", "3", "4", "5"]:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=f"道岔{name}", width=7).pack(side=tk.LEFT)
            ttk.Button(row, text="定操", command=lambda n=name: self.controller.move_switch(n, SwitchPosition.NORMAL)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="反操", command=lambda n=name: self.controller.move_switch(n, SwitchPosition.REVERSE)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="单锁", command=lambda n=name: self.controller.set_switch_lock(n, True)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="单解", command=lambda n=name: self.controller.set_switch_lock(n, False)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="封锁", command=lambda n=name: self.controller.set_switch_block(n, True)).pack(side=tk.LEFT, padx=2)
            ttk.Button(row, text="解封", command=lambda n=name: self.controller.set_switch_block(n, False)).pack(side=tk.LEFT, padx=2)

    def _build_sim_buttons(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="仿真控制")
        frame.pack(fill=tk.X, padx=4, pady=3)
        ttk.Button(frame, text="模拟列车进入", command=self.controller.simulate_train_enter).pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Button(frame, text="模拟列车出清", command=self.controller.simulate_train_clear).pack(side=tk.LEFT, padx=3, pady=4)
        ttk.Label(frame, text="轨道").pack(side=tk.LEFT, padx=(12, 2))
        ttk.OptionMenu(frame, self.selected_track, self.selected_track.get(), *self.state_model.tracks.keys()).pack(side=tk.LEFT)
        ttk.Button(frame, text="模拟轨道占用", command=lambda: self.controller.set_track_occupied(self.selected_track.get(), True)).pack(side=tk.LEFT, padx=3)
        ttk.Button(frame, text="模拟轨道出清", command=lambda: self.controller.set_track_occupied(self.selected_track.get(), False)).pack(side=tk.LEFT, padx=3)
        ttk.Label(frame, text="信号").pack(side=tk.LEFT, padx=(12, 2))
        ttk.OptionMenu(frame, self.selected_signal, self.selected_signal.get(), *self.state_model.signals.keys()).pack(side=tk.LEFT)
        ttk.Button(frame, text="模拟信号断丝", command=lambda: self.controller.set_signal_broken(self.selected_signal.get(), True)).pack(side=tk.LEFT, padx=3)
        ttk.Button(frame, text="恢复信号", command=lambda: self.controller.set_signal_broken(self.selected_signal.get(), False)).pack(side=tk.LEFT, padx=3)
        ttk.Button(frame, text="重置系统", command=self.controller.reset).pack(side=tk.LEFT, padx=3)

    def _build_status_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="动态提示/状态")
        frame.pack(fill=tk.BOTH, expand=True)
        self.status_text = tk.Text(frame, width=44, height=24)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def _loop(self) -> None:
        self.controller.tick()
        self._refresh()
        self.after(1000, self._loop)

    def _refresh(self) -> None:
        self.canvas.delete("all")
        self._draw_station()
        self._draw_status()

    def _draw_station(self) -> None:
        self.canvas.create_text(600, 28, text="计算机联锁模拟仿真系统站场图", fill="#111827", font=("Arial", 18, "bold"))
        self.canvas.create_text(1000, 80, text="6‰", fill="#9ca3af", font=("Arial", 12))
        self.canvas.create_line(982, 86, 1034, 86, fill="#cbd5e1", width=1)
        locked_tracks = self._locked_tracks()
        for name, segments in TRACK_GEOMETRY.items():
            if self.state_model.tracks[name].state == TrackState.OCCUPIED:
                color, width = TRACK_OCCUPIED, 8
            elif name in locked_tracks:
                color, width = TRACK_LOCKED, 7
            else:
                color, width = TRACK_CLEAR, 4
            for x1, y1, x2, y2 in segments:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, capstyle=tk.ROUND)
        self._draw_buffer_stop(210, 245)
        self._draw_labels()
        self._draw_endpoint(43, 170)
        self._draw_endpoint(1158, 170)
        self._draw_button_square(95, 170)
        self._draw_button_square(1120, 170)
        for name, (x, y) in SWITCH_GEOMETRY.items():
            self._draw_switch(name, x, y)
        for name, (x, y) in SIGNAL_GEOMETRY.items():
            self._draw_signal(name, x, y)
        self._draw_trains()
        self._draw_legend()

    def _draw_labels(self) -> None:
        for text, (x, y) in TRACK_LABELS.items():
            self.canvas.create_text(x, y, text=text, fill="#111827", font=("Arial", 11, "bold"))
        for name, (x, y) in SWITCH_GEOMETRY.items():
            dy = 22 if name != "5" else 18
            self.canvas.create_text(x, y + dy, text=name, fill="#111827", font=("Arial", 11, "bold"))

    def _draw_switch(self, name: str, x: int, y: int) -> None:
        sw = self.state_model.switches[name]
        fill = "#a855f7" if sw.position == SwitchPosition.NORMAL else "#ec4899" if sw.position == SwitchPosition.REVERSE else "#facc15"
        outline = "#1d4ed8" if sw.locked else "#dc2626" if sw.blocked else "#111827" if sw.single_locked else "#374151"
        self.canvas.create_rectangle(x - 7, y - 7, x + 7, y + 7, fill=fill, outline=outline, width=3 if (sw.locked or sw.blocked or sw.single_locked) else 1)
        letter = "N" if sw.position == SwitchPosition.NORMAL else "R" if sw.position == SwitchPosition.REVERSE else "T"
        self.canvas.create_text(x, y, text=letter, fill="white" if letter != "T" else "#111827", font=("Arial", 8, "bold"))

    def _draw_signal(self, name: str, x: int, y: int) -> None:
        if name in TERMINAL_POINTS:
            self._draw_terminal_point(name, x, y)
            return
        sig = self.state_model.signals[name]
        track_y = SIGNAL_TRACK_Y[name]
        lamp_edge_y = y + 5 if y < track_y else y - 5
        self.canvas.create_line(x, track_y, x, lamp_edge_y, fill="#4b5563", width=2)
        if name in BUTTON_SIGNALS:
            self._draw_button_square(x + 32, track_y)
        color = SIGNAL_OPEN if sig.aspect == SignalAspect.GREEN else SIGNAL_BROKEN if sig.aspect == SignalAspect.BROKEN else SIGNAL_CLOSED
        self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=color, outline="#111827")
        self.canvas.create_oval(x + 16, y - 5, x + 26, y + 5, fill=color if sig.aspect == SignalAspect.GREEN else SIGNAL_CLOSED, outline="#111827")
        label_y = y + 20 if name in {"S3", "SII", "X3", "XII", "S", "D2", "S1", "X1", "PZA"} else y - 18
        self.canvas.create_text(x + 8, label_y, text=name, fill="#111827", font=("Arial", 10, "bold"))
        if sig.aspect == SignalAspect.BROKEN:
            self.canvas.create_text(x + 58, y, text="断丝", fill="#c2410c", font=("Arial", 10, "bold"))

    def _draw_terminal_point(self, name: str, x: int, y: int) -> None:
        self.canvas.create_line(x, SIGNAL_TRACK_Y[name], x, y - 8, fill="#4b5563", width=2)
        self.canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="white", outline="#6b7280", width=2)
        self.canvas.create_text(x + 10, y + 20, text=name, fill="#111827", font=("Arial", 10, "bold"))

    def _draw_button_square(self, x: int, y: int) -> None:
        self.canvas.create_rectangle(x - 6, y - 6, x + 6, y + 6, fill=BUTTON_PURPLE, outline="#111827")

    def _draw_endpoint(self, x: int, y: int) -> None:
        self.canvas.create_rectangle(x - 8, y - 11, x + 8, y + 11, fill="#d1d5db", outline="#111827")

    def _draw_buffer_stop(self, x: int, y: int) -> None:
        self.canvas.create_line(x, y - 18, x, y + 18, fill=TRACK_CLEAR, width=3)
        self.canvas.create_line(x - 13, y - 18, x + 13, y - 18, fill=TRACK_CLEAR, width=3)
        self.canvas.create_line(x - 13, y + 18, x + 13, y + 18, fill=TRACK_CLEAR, width=3)

    def _draw_trains(self) -> None:
        for train in self.state_model.trains.values():
            track = train.current_track
            if train.active and track in TRACK_GEOMETRY:
                x1, y1, x2, y2 = TRACK_GEOMETRY[track][0]
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_rectangle(cx - 20, cy - 25, cx + 20, cy - 9, fill="#06b6d4", outline="#083344")
                self.canvas.create_text(cx, cy - 34, text=train.name, fill="#0f172a", font=("Arial", 10, "bold"))

    def _draw_legend(self) -> None:
        items = [(TRACK_CLEAR, "轨道出清"), (TRACK_LOCKED, "进路锁闭"), (TRACK_OCCUPIED, "轨道占压"), (SIGNAL_OPEN, "信号开放"), (SIGNAL_CLOSED, "信号关闭"), (SIGNAL_BROKEN, "信号断丝"), ("#a855f7", "道岔定位"), ("#ec4899", "道岔反位")]
        x = 60
        y = 335
        for color, text in items:
            self.canvas.create_rectangle(x, y - 8, x + 18, y + 4, fill=color, outline="#9ca3af")
            self.canvas.create_text(x + 58, y - 2, text=text, fill="#111827", font=("Arial", 9))
            x += 135

    def _locked_tracks(self) -> set[str]:
        locked = set()
        for route in self.state_model.routes.values():
            if route.locked:
                locked.update(route.tracks)
        return locked

    def _draw_status(self) -> None:
        lines = [f"仿真秒: {self.state_model.tick_no}", f"当前进路: {self.state_model.current_route or '无'}", ""]
        lines.append("进路状态:")
        for route in self.state_model.routes.values():
            cd = f", 倒计时 {route.cancel_countdown}s" if route.cancel_countdown else ""
            lines.append(f"{route.name}: {'锁闭' if route.locked else '未锁'}{cd}")
        lines.append("\n道岔状态:")
        for sw in self.state_model.switches.values():
            flags = []
            if sw.locked:
                flags.append("进路锁闭")
            if sw.single_locked:
                flags.append("单锁")
            if sw.blocked:
                flags.append("封锁")
            lines.append(f"道岔{sw.name}: {sw.position.value} {'/'.join(flags) if flags else '可用'}")
        lines.append("\n轨道状态:")
        lines.append("  ".join(f"{k}:{v.state.value}" for k, v in self.state_model.tracks.items()))
        lines.append("\n操作提示:")
        lines.extend(self.state_model.messages[-10:])
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "\n".join(lines))


def main() -> None:
    InterlockingApp().mainloop()


if __name__ == "__main__":
    main()
