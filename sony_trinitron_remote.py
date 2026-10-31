#!/usr/bin/env python3
"""Visual Sony RM-833 / Trinitron KV-C2983E remote via BroadLink RM3 Mini.

Windows: install broadlink==0.19.0; no local web server is required.
IR codes were shared by the Home Assistant community:
https://community.home-assistant.io/t/tv-sony-trinitron-broadlink-and-base-64-codes-for-remote-control/768889
The TV/AV1/RGB source menu is described in the Sony BE-3B service manual.

Not all IR codes are verified on the KV-C2983E. The app sends only
commands chosen by the user, and service controls should be used cautiously.
"""

from __future__ import annotations

import base64
import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from typing import Any

try:
    import broadlink
except ImportError:
    broadlink = None

WINDOW_TITLE = "Sony Trinitron · BroadLink Remote"
CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "SonyTrinitronBroadLink"
CONFIG_FILE = CONFIG_DIR / "remote_config.json"

# BroadLink Base64 captures for the RM-833 remote family. Exact compatibility
# depends on the TV model; some functions were tested on a KV-C2983E.
CODES = {
    "power": "JgEcAFIQKREWESkRFhEpERYRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "info": "JgEcAFEQFhApEBYQKRApECkQFhApEBYQFhAWEBYAA3QNBQAAAAAAAAAAAAA=",
    "tv": "JgEcAFIQFhEWERYRKREpESkRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "source": "JgEcAFIQKREWESkRFhEWESkRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "menu": "JgEcAFIQFhEWERYRFhEWESkRKREpERYRFhEWERUAA1oNBQAAAAAAAAAAAAA=",
    "red": "JgEcAFIQFhEWESkRKREWERYRKREpESkRFhEWERUAAzINBQAAAAAAAAAAAAA=",
    "green": "JgEcAFIQKREWESkRKREWERYRKREpESkRFhEWERUAAx8NBQAAAAAAAAAAAAA=",
    "yellow": "JgEcAFIQFhEpESkRKREWERYRKREpESkRFhEWERUAAx8NBQAAAAAAAAAAAAA=",
    "blue": "JgEcAFIQKREpESkRKREWERYRKREpESkRFhEWERUAAwsNBQAAAAAAAAAAAAA=",
    "white": "JgEcAFIQFhEWERYRKREWERYRKREpESkRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "up": "JgEcAFIQFhEWESkRFhEpESkRKREpERYRFhEWERUAAzINBQAAAAAAAAAAAAA=",
    "down": "JgEcAFIQKREWESkRFhEpESkRKREpERYRFhEWERUAAx8NBQAAAAAAAAAAAAA=",
    "center": "JgEcAFIQFhEpESkRFhEpERYRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "vol+": "JgEcAE8TExMnExMTExMnExMTExMnExMTExMTExMAA2cNBQAAAAAAAAAAAAA=",
    "vol-": "JgEcAE8TJxMnExMTExMnExMTExMnExMTExMTExMAA1QNBQAAAAAAAAAAAAA=",
    "mute": "JgEcAFIQFhEWESkRFhEpERYRFhEpERYRFhEWERUAA1oNBQAAAAAAAAAAAAA=",
    "ch+": "JgEcAE8TExMTExMTExMnExMTExMnExMTExMTExMAA3kNBQAAAAAAAAAAAAA=",
    "ch-": "JgEcAE4TJxMTExMTExMnExMTExMnExMTExMTExMAA2INBQAAAAAAAAAAAAA=",
    "tenplus": "JgEcAFIQKREWESkRKREpERYRFhEpERYRFhEWERUAAzINBQAAAAAAAAAAAAA=",
    "clear": "JgEcAFIQFhEpESkRKREWERYRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "0": "JgEcAFIQKREWERYRKREWERYRFhEpERYRFhEWERUAA1oNBQAAAAAAAAAAAAA=",
    "1": "JgEcAFIQFhEWERYRFhEWERYRFhEpERYRFhEWERUAA4ENBQAAAAAAAAAAAAA=",
    "2": "JgEcAFIQKREWERYRFhEWERYRFhEpERYRFhEWERUAA20NBQAAAAAAAAAAAAA=",
    "3": "JgEcAFIQFhEpERYRFhEWERYRFhEpERYRFhEWERUAA20NBQAAAAAAAAAAAAA=",
    "4": "JgEcAFIQKREpERYRFhEWERYRFhEpERYRFhEWERUAA1oNBQAAAAAAAAAAAAA=",
    "5": "JgEcAE8TExMTEycTExMTExMTExMnExMTExMTExMAA3kNBQAAAAAAAAAAAAA=",
    "6": "JgEcAE4TJxMTEycTExMTExMTExMnExMTExMTExMAA1wNBQAAAAAAAAAAAAA=",
    "7": "JgEcAFIQFhEpESkRFhEWERYRFhEpERYRFhEWERUAA1oNBQAAAAAAAAAAAAA=",
    "8": "JgEcAFIQKREpESkRFhEWERYRFhEpERYRFhEWERUAA0YNBQAAAAAAAAAAAAA=",
    "9": "JgEcAFIQFhEWERYRKREWERYRFhEpERYRFhEWERUAA20NBQAAAAAAAAAAAAA=",
}

# Physical RM-833 keys with unverified IR codes can be assigned manually
# or learned from a working remote.
EXTRA_BUTTONS = {
    "teletext": "Teletext",
    "text_hold": "Text hold",
    "text_size": "Text size",
    "text_reveal": "Text reveal",
    "text_mix": "Text mix",
    "text_index": "Text index",
    "text_clock": "Text clock",
    "picture": "Picture / screen",
    "view": "View program",
    "vtr_power": "VTR Power",
    "vtr_rew": "VTR ◀◀",
    "vtr_play": "VTR ▶",
    "vtr_ff": "VTR ▶▶",
    "vtr_stop": "VTR ■",
    "vtr_pause": "VTR ❚❚",
    "vtr_rec": "VTR ●",
    "vtr_chup": "VTR PROG +",
    "vtr_chdown": "VTR PROG −",
}

COLORS = {
    "bg": "#0c1322", "panel": "#141f31", "panel2": "#1b2940",
    "text": "#edf3ff", "muted": "#9fb3d2", "accent": "#4aa9ff",
    "border": "#31455f", "green": "#1a9f74", "orange": "#e8a449",
}


def is_valid_b64(raw: str) -> bool:
    try:
        payload = base64.b64decode(raw.strip(), validate=True)
        return len(payload) >= 10 and payload[0] == 0x26
    except Exception:
        return False


def ir_packet(key: str, saved: dict[str, str], repeats: int = 3) -> bytes:
    if not 1 <= repeats <= 8:
        raise ValueError("IR repeat count must be between 1 and 8")
    encoded = saved.get(key) or CODES.get(key)
    if not encoded:
        raise LookupError(f"No IR code has been assigned to button '{key}' yet")
    raw = bytearray(base64.b64decode(encoded))
    if len(raw) < 10 or raw[0] != 0x26:
        raise ValueError(f"The IR code for {key} is not a valid BroadLink packet")
    # BroadLink: byte 1 is the number of ADDITIONAL transmissions.
    raw[1] = repeats - 1
    return bytes(raw)


class Remote:
    def __init__(self):
        self.device: Any = None
        self.devices: list[Any] = []

    def discover(self):
        self.devices = [d for d in broadlink.discover(timeout=7) if hasattr(d, "send_data")]
        return self.devices

    def connect(self, index: int):
        d = self.devices[index]
        d.auth()
        self.device = d
        return d

    def send(self, key: str, codes: dict[str, str], repeats: int = 3):
        if self.device is None:
            raise RuntimeError("Connect to BroadLink first")
        self.device.send_data(ir_packet(key, codes, repeats))


class UI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("1020x810")
        self.root.minsize(850, 640)
        self.root.configure(bg=COLORS["bg"])
        self.remote = Remote()
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.settings = self._load_settings()
        self.saved_codes: dict[str, str] = dict(self.settings.get("codes", {}))
        self.source_steps = tk.IntVar(value=int(self.settings.get("rgb_steps", 2)))
        self.vtr_mode = tk.StringVar(value=self.settings.get("vtr_mode", "VTR1"))
        self.status = tk.StringVar(value="Disconnected")
        self.selected_device = tk.StringVar(value="Find RM3 Mini")
        self.devices: list[str] = []
        self.logtext = None
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()
        self.build()
        self.root.after(100, self._poll)
        self.root.after(200, lambda: self.enqueue("discover"))
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _load_settings(self) -> dict:
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_settings(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps({
                "rgb_steps": int(self.source_steps.get()),
                "vtr_mode": self.vtr_mode.get(),
                "codes": self.saved_codes,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            messagebox.showwarning("Settings", f"Could not save settings: {exc}")

    def build(self):
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=22, pady=15)
        header.pack(fill="x")
        tk.Label(header, text="SONY  /  TRINITRON", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(header, text="RM-833 virtual  ·  KV-C2983E  ·  BroadLink RM3 Mini", bg=COLORS["bg"],
                 fg=COLORS["muted"], font=("Segoe UI", 10)).pack(anchor="w")

        connect = tk.Frame(self.root, bg=COLORS["panel"], padx=14, pady=10)
        connect.pack(fill="x", padx=20, pady=(0, 10))
        self.action(connect, "Find", lambda: self.enqueue("discover"), width=10).pack(side="left", padx=(0, 7))
        self.combo = ttk.Combobox(connect, textvariable=self.selected_device, state="readonly", width=34)
        self.combo.pack(side="left", padx=(0, 8))
        self.action(connect, "Connect", self.connect, width=11, bg=COLORS["green"]).pack(side="left")
        tk.Label(connect, textvariable=self.status, bg=COLORS["panel"], fg="#87edc5",
                 font=("Segoe UI", 10)).pack(side="right", padx=8)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=20)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 9],
                        background=COLORS["panel2"], foreground=COLORS["text"])
        style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])],
                  foreground=[("selected", COLORS["bg"])])
        self.scroll_surfaces = []
        self.tab_tv = self.tab("TV & Sources")
        self.tab_full = self.tab("Full RM-833")
        self.tab_service = self.tab("Service & Geometry")
        self.tab_setup = self.tab("Configure Buttons")
        self.build_tv_tab()
        self.build_full_tab()
        self.build_service_tab()
        self.build_setup_tab()

        bottom = tk.Frame(self.root, bg=COLORS["bg"], padx=22, pady=8)
        bottom.pack(fill="x")
        tk.Label(bottom, text="Activity:", bg=COLORS["bg"], fg=COLORS["muted"]).pack(side="left")
        self.activity = tk.Label(bottom, text="Starting...", bg=COLORS["bg"], fg=COLORS["text"],
                                 anchor="w", font=("Segoe UI", 9))
        self.activity.pack(side="left", padx=10, fill="x", expand=True)

    def tab(self, title: str):
        outer = tk.Frame(self.tabs, bg=COLORS["bg"])
        self.tabs.add(outer, text=title)
        canvas = tk.Canvas(outer, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=COLORS["bg"], padx=14, pady=12)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.bind("<Configure>", lambda e, c=canvas, w=window_id: c.itemconfigure(w, width=e.width))
        self.scroll_surfaces.append(canvas)
        # Scrolling is also enabled when hovering over child buttons.
        self.root.bind_all("<MouseWheel>", self._mousewheel)
        return inner

    def _mousewheel(self, event):
        if not self.scroll_surfaces:
            return
        idx = self.tabs.index(self.tabs.select())
        if event.delta:
            self.scroll_surfaces[idx].yview_scroll(-1 if event.delta > 0 else 1, "units")

    def panel(self, parent, title: str):
        area = tk.Frame(parent, bg=COLORS["panel"], padx=15, pady=13)
        area.pack(fill="x", pady=(0, 12))
        tk.Label(area, text=title, bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 9))
        return area

    def action(self, parent, text, callback, width=12, bg=None, fg=None, height=1):
        base = bg or COLORS["panel2"]
        b = tk.Button(parent, text=text, command=callback, width=width, height=height,
                      bg=base, fg=fg or COLORS["text"], activebackground=COLORS["accent"],
                      activeforeground="#101929", relief="flat", cursor="hand2", bd=0,
                      highlightthickness=0, font=("Segoe UI", 10, "bold"), padx=8, pady=5)
        return b

    def btn(self, parent, text: str, key: str, width=12, color=None):
        self.action(parent, text, lambda k=key: self.send(k), width=width, bg=color).pack(side="left", padx=4, pady=4)

    def note(self, parent, text: str):
        tk.Label(parent, text=text, justify="left", anchor="w", wraplength=820,
                 bg=parent["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(fill="x", pady=(5, 5))

    def build_tv_tab(self):
        p = self.panel(self.tab_tv, "Video inputs")
        buttons = tk.Frame(p, bg=COLORS["panel"])
        buttons.pack(anchor="w", fill="x")
        self.btn(buttons, "SOURCE / AV", "source", width=18, color="#23619a")
        self.btn(buttons, "TV (tuner)", "tv", width=17)
        self.action(buttons, "RGB SCART  /  RGB-Pi", self.rgb_macro, width=23,
                    bg=COLORS["green"], height=2).pack(side="left", padx=8, pady=4)
        self.note(p, "RGB SCART sends TV → SOURCE → SOURCE (input sequence: TV, AV1, RGB). "
                     "BroadLink cannot read the selected input: check that your TV actually shows RGB. "
                     "Do not use this shortcut while in TT/service mode.")
        r = tk.Frame(p, bg=COLORS["panel"])
        r.pack(anchor="w", fill="x", pady=(5, 0))
        tk.Label(r, text="SOURCE presses after TV:", bg=COLORS["panel"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Spinbox(r, from_=1, to=7, width=4, textvariable=self.source_steps,
                   command=self._save_settings, bg=COLORS["panel2"], fg=COLORS["text"],
                   buttonbackground=COLORS["panel2"]).pack(side="left", padx=(10, 6))
        self.action(r, "Save", self._save_settings, width=9).pack(side="left")

        p = self.panel(self.tab_tv, "Basic controls")
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        self.btn(r, "⏻  POWER", "power", 15, "#bf3b4d")
        self.btn(r, "Mute", "mute", 14)
        self.btn(r, "i+ / INFO", "info", 14)
        self.btn(r, "MENU", "menu", 14)
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        self.btn(r, "VOL −", "vol-", 15)
        self.btn(r, "VOL +", "vol+", 14)
        self.btn(r, "PROG −", "ch-", 14)
        self.btn(r, "PROG +", "ch+", 14)
        p = self.panel(self.tab_tv, "Number pad")
        num = tk.Frame(p, bg=COLORS["panel"]); num.pack(anchor="w")
        for ridx, line in enumerate((("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9"), ("-/--", "0", "C"))):
            for cidx, label in enumerate(line):
                key = {"-/--": "tenplus", "C": "clear"}.get(label, label)
                self.action(num, label, lambda k=key: self.send(k), width=10).grid(row=ridx, column=cidx, padx=5, pady=4)

    def build_full_tab(self):
        p = self.panel(self.tab_full, "Front panel · Sony RM-833")
        rows = [
            [("⏻", "power"), ("Mute", "mute"), ("TV", "tv"), ("SOURCE", "source")],
            [("i+", "info"), ("Teletext", "teletext"), ("Size", "text_size"), ("Hold", "text_hold")],
            [("Index", "text_index"), ("Reveal", "text_reveal"), ("Mix", "text_mix"), ("Screen", "picture")],
            [("MENU", "menu"), ("Vol +", "vol+"), ("Vol −", "vol-"), ("C / Clear", "clear")],
            [("PROG +", "ch+"), ("PROG −", "ch-"), ("MENU +", "up"), ("MENU −", "down")],
        ]
        for line in rows:
            r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
            for label, key in line: self.btn(r, label, key, width=15)
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w", pady=(4, 0))
        for label, key, color in (("RED","red","#9d354c"),("GREEN","green","#168560"),
                                  ("YELLOW","yellow","#b78e22"),("BLUE","blue","#235ca7"),
                                  ("WHITE","white","#64738c")):
            self.btn(r, label, key, width=12, color=color)
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        self.btn(r, "↔ / Center", "center", 15)
        self.btn(r, "−/−−", "tenplus", 15)
        self.btn(r, "Text clock", "text_clock", 15)
        self.btn(r, "View program", "view", 15)
        self.note(p, "Unverified special keys open a dialog to assign or learn their IR codes; "
                     "basic controls already include built-in codes.")

        p = self.panel(self.tab_full, "Lower panel · VTR / MDP (configurable)")
        modebar = tk.Frame(p, bg=COLORS["panel"]); modebar.pack(anchor="w", pady=(0, 8))
        tk.Label(modebar, text="Original mode switch:", bg=COLORS["panel"],
                 fg=COLORS["muted"]).pack(side="left", padx=(0, 8))
        modecombo = ttk.Combobox(modebar, textvariable=self.vtr_mode, state="readonly",
                                 values=["VTR1", "VTR2", "VTR3", "MDP"], width=10)
        modecombo.pack(side="left")
        modecombo.bind("<<ComboboxSelected>>", lambda event: self._save_settings())
        rows = [[("⏻ VTR", "vtr_power"), ("◀◀", "vtr_rew"), ("▶", "vtr_play"), ("▶▶", "vtr_ff")],
                [("■", "vtr_stop"), ("❚❚", "vtr_pause"), ("● REC", "vtr_rec"), ("PROG +", "vtr_chup")],
                [("PROG −", "vtr_chdown")]]
        for line in rows:
            r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
            for label, key in line: self.btn(r, label, key, width=14)
        self.note(p, "These keys are for Sony video recorders (VTR/MDP), not the TV. "
                     "VTR1/2/3/MDP keeps separate learned codes for each mode. "
                     "They require device-specific codes; unknown signals are never guessed.")

    def build_service_tab(self):
        p = self.panel(self.tab_service, "Sony BE-3B service mode")
        self.note(p, "Use only when the TV is in STANDBY. Service sequence verified on some Sony models: "
                     "Display ×5 → 5 ×5 → VOL+ ×5 → TV ×5.")
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        self.action(r, "Enter service / TT", self.service_macro, width=23, bg="#ac732a", height=2).pack(side="left", padx=4)
        self.action(r, "Send MENU", lambda: self.send("menu"), width=17).pack(side="left", padx=4)
        self.action(r, "Exit TT (00)", self.exit_tt, width=17).pack(side="left", padx=4)
        p = self.panel(self.tab_service, "Navigation & adjustments")
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        for txt, key in (("RED / next", "red"), ("GREEN / previous", "green"),
                         ("WHITE / enter", "white")):
            self.btn(r, txt, key, width=18)
        r = tk.Frame(p, bg=COLORS["panel"]); r.pack(anchor="w")
        self.btn(r, "MENU + / increase", "up", width=18)
        self.btn(r, "MENU − / decrease", "down", width=18)
        self.btn(r, "i+ / INFO", "info", width=18)
        self.note(p, "Photograph all original settings. Never enter TT reset codes or change unfamiliar "
                     "parameters. To fully exit, power the TV off and back on.")

    def build_setup_tab(self):
        p = self.panel(self.tab_setup, "Assign codes to special buttons")
        self.note(p, "Paste a BroadLink Base64 code or learn an IR signal from a working remote. "
                     "Codes are saved only on your PC, not in the cloud.")
        container = tk.Frame(p, bg=COLORS["panel"]); container.pack(anchor="w")
        self.custom_pick = ttk.Combobox(container, state="readonly", width=30,
                                         values=[f"{label}  [{key}]" for key,label in EXTRA_BUTTONS.items()])
        self.custom_pick.current(0)
        self.custom_pick.pack(side="left", padx=(0, 8))
        self.action(container, "Configure", self.configure_selected, 13).pack(side="left", padx=4)
        self.action(container, "Learn IR", self.learn_selected, 13).pack(side="left", padx=4)
        self.action(container, "Delete", self.delete_selected, 12, "#704c56").pack(side="left", padx=4)

        p = self.panel(self.tab_setup, "Diagnostics")
        self.action(p, "Show log", self.show_logs, width=16).pack(anchor="w")
        self.note(p, "Your PC and RM3 Mini must be on the same local network. "
                     "If authentication fails, disable 'Lock device' in the BroadLink app.")
        self.note(p, f"Settings file: {CONFIG_FILE}")

    def effective_key(self, key: str):
        return key + ":" + self.vtr_mode.get() if key.startswith("vtr_") else key

    def extra_label(self, key: str):
        base = key.split(":", 1)[0]
        return EXTRA_BUTTONS.get(base, key) + (" (" + key.split(":", 1)[1] + ")" if ":" in key else "")

    def current_extra_key(self):
        i = self.custom_pick.current()
        return self.effective_key(list(EXTRA_BUTTONS)[i]) if i >= 0 else None

    def _show_code_dialog(self, key: str):
        code = simpledialog.askstring("Assign IR code", "Paste the BroadLink Base64 code for:\n" + self.extra_label(key),
                                      initialvalue=self.saved_codes.get(key, ""), parent=self.root)
        if code is None:
            return
        code = code.strip().removeprefix("b64:")
        if not is_valid_b64(code):
            messagebox.showerror("Invalid code", "Enter a valid BroadLink Base64 IR packet (typically starting with Jg...).")
            return
        self.saved_codes[key] = code
        self._save_settings()
        self.log(f"Assigned: {self.extra_label(key)}")

    def configure_selected(self):
        k = self.current_extra_key()
        if k:
            self._show_code_dialog(k)

    def learn_selected(self):
        k = self.current_extra_key()
        if not k:
            return
        if self.remote.device is None:
            messagebox.showwarning("Connect", "Connect the RM3 Mini first.")
            return
        if not messagebox.askokcancel("Learn IR", "Point a working remote at the RM3 Mini and press the key to learn.\n\nYou have about 12 seconds after clicking OK."):
            return
        self.enqueue("learn", k)

    def delete_selected(self):
        k = self.current_extra_key()
        if k in self.saved_codes:
            del self.saved_codes[k]
            self._save_settings()
            self.log(f"Removed saved code: {k}")

    def show_logs(self):
        if getattr(self, "logwin", None) is not None and self.logwin.winfo_exists():
            self.logwin.lift(); return
        self.logwin = tk.Toplevel(self.root)
        self.logwin.title("Activity log")
        self.logwin.geometry("700x430")
        txt = tk.Text(self.logwin, bg=COLORS["panel"], fg=COLORS["text"])
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", "\n".join(getattr(self, "logs", [])))
        txt.configure(state="disabled")
        self.logtext = txt

    def log(self, text):
        stamp = time.strftime("%H:%M:%S")
        val = f"[{stamp}] {text}"
        if not hasattr(self, "logs"):
            self.logs = []
        self.logs.append(val)
        self.logs = self.logs[-200:]
        self.activity.configure(text=text)
        if self.logtext and self.logtext.winfo_exists():
            self.logtext.configure(state="normal")
            self.logtext.insert("end", val + "\n")
            self.logtext.see("end")
            self.logtext.configure(state="disabled")

    def enqueue(self, action: str, *args):
        self.task_queue.put((action, args))

    def connect(self):
        idx = self.combo.current()
        if idx < 0:
            messagebox.showwarning("BroadLink", "Click Find first and select a device.")
            return
        self.enqueue("connect", idx)

    def send(self, key: str):
        key = self.effective_key(key)
        if key.split(":", 1)[0] in EXTRA_BUTTONS and not self.saved_codes.get(key):
            self._show_code_dialog(key)
            return
        if self.remote.device is None:
            messagebox.showwarning("BroadLink", "Connect the RM3 Mini before using the remote.")
            return
        self.enqueue("send", key, 5 if key == "info" else 3)

    def rgb_macro(self):
        if self.remote.device is None:
            messagebox.showwarning("BroadLink", "Connect the RM3 Mini first.")
            return
        if not messagebox.askokcancel("Switch to RGB SCART",
                "The TV must be ON and OUTSIDE service mode.\n\n"
                "The app will send: TV (tuner) → SOURCE / AV × " + str(self.source_steps.get()) +
                "\n\nContinue?\n\nCheck on the TV that RGB is selected."):
            return
        self._save_settings()
        self.enqueue("rgb", max(1, min(7, self.source_steps.get())))

    def service_macro(self):
        if self.remote.device is None:
            messagebox.showwarning("BroadLink", "Connect the RM3 Mini first.")
            return
        if not messagebox.askyesno("Enter service mode",
                  "Is the TV in STANDBY (screen off, power connected)?\n\n"
                  "This sends the service5 sequence documented for this app.\n\n"
                  "Do not change settings unless you know their original values."):
            return
        self.enqueue("service")

    def exit_tt(self):
        if self.remote.device is None:
            messagebox.showwarning("BroadLink", "Connect the RM3 Mini first.")
            return
        if not messagebox.askyesno("Exit TT", "The app will send 0,0. Do not press other keys during this operation.\nContinue?"):
            return
        self.enqueue("exit_tt")

    def _worker(self):
        while True:
            action, args = self.task_queue.get()
            if action == "close":
                return
            try:
                if broadlink is None:
                    raise RuntimeError("Missing 'broadlink'. Install it with: py -m pip install broadlink==0.19.0")
                if action == "discover":
                    found = self.remote.discover()
                    labels = [f"{getattr(d, 'model', 'RM Mini')} — {d.host[0]}  ({hex(d.devtype)})"
                              for d in found]
                    self.result_queue.put(("found", labels))
                elif action == "connect":
                    d = self.remote.connect(args[0])
                    self.result_queue.put(("connected", d.host[0]))
                elif action == "send":
                    k, reps = args
                    self.remote.send(k, self.saved_codes, reps)
                    self.result_queue.put(("ok", f"Sent: {k}"))
                elif action == "rgb":
                    n, = args
                    self.remote.send("tv", self.saved_codes, 3)
                    time.sleep(0.85)
                    for i in range(n):
                        self.remote.send("source", self.saved_codes, 3)
                        time.sleep(0.85)
                    self.result_queue.put(("ok", f"RGB SCART: sent TV + SOURCE ×{n}; verify RGB on the TV"))
                elif action == "service":
                    for k in ("info", "5", "vol+", "tv"):
                        self.remote.send(k, self.saved_codes, 5)
                        time.sleep(0.55)
                    self.result_queue.put(("ok", "Service5 sent. Is TT displayed? Press MENU to continue."))
                elif action == "exit_tt":
                    self.remote.send("0", self.saved_codes, 3)
                    time.sleep(0.42)
                    self.remote.send("0", self.saved_codes, 3)
                    self.result_queue.put(("ok", "Sent 0,0"))
                elif action == "learn":
                    k, = args
                    self.remote.device.enter_learning()
                    packet = None
                    for _ in range(24):
                        time.sleep(0.5)
                        try:
                            packet = self.remote.device.check_data()
                        except (ValueError, TimeoutError):
                            packet = None
                        if packet:
                            break
                    if not packet:
                        raise TimeoutError("No IR signal received within 12 seconds")
                    self.result_queue.put(("learned", (k, base64.b64encode(packet).decode())))
                else:
                    self.result_queue.put(("error", "Unknown action: " + action))
            except Exception as exc:
                self.result_queue.put(("error", f"{action}: {exc}"))
            finally:
                self.task_queue.task_done()

    def _poll(self):
        try:
            while True:
                kind, value = self.result_queue.get_nowait()
                if kind == "found":
                    self.devices = value
                    self.combo["values"] = value
                    if value:
                        self.combo.current(0)
                        self.status.set(f"Found: {len(value)}")
                        self.log("Found: " + value[0])
                        # Automatically connect when a single BroadLink is found.
                        if len(value) == 1:
                            self.enqueue("connect", 0)
                    else:
                        self.status.set("No BroadLink found")
                        self.log("No BroadLink discovered")
                elif kind == "connected":
                    self.status.set(f"Connected · {value}")
                    self.log(f"Connected to {value}")
                elif kind == "learned":
                    k, code = value
                    self.saved_codes[k] = code
                    self._save_settings()
                    self.log("Learned and saved: " + self.extra_label(k))
                    messagebox.showinfo("Learning successful", "Saved IR code for: " + self.extra_label(k))
                elif kind == "error":
                    self.log("Error: " + value)
                    if "connect" in value or "discover" in value:
                        self.status.set("Connection error")
                else:
                    self.log(value)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def close(self):
        self._save_settings()
        self.enqueue("close")
        self.root.destroy()


def main():
    root = tk.Tk()
    UI(root)
    root.mainloop()


if __name__ == "__main__":
    main()