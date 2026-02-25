"""
Language Fixer Pro v1.0.0
=========================
Open Source Arabic ↔ English keyboard layout fixer.
GitHub: https://github.com/YOUR_USERNAME/LanguageFixerPro

License: MIT
"""

import customtkinter as ctk
import pyperclip
import pystray
from pynput import mouse as pynput_mouse
from pynput import keyboard as pynput_keyboard
from PIL import Image, ImageDraw
import threading
import time
import sys
import os
import json
import ctypes
import webbrowser

# ---------------------------------------------------------
# App Info
# ---------------------------------------------------------

APP_NAME = "Language Fixer Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"
APP_GITHUB = "https://github.com/YOUR_USERNAME/LanguageFixerPro"
APP_LICENSE = "MIT License"
UPDATE_CHECK_URL = "https://api.github.com/repos/YOUR_USERNAME/LanguageFixerPro/releases/latest"

# ---------------------------------------------------------
# Windows API
# ---------------------------------------------------------

user32 = ctypes.windll.user32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def send_key_combo(keys):
    VK = {
        'ctrl': 0x11, 'shift': 0x10, 'alt': 0x12,
        'a': 0x41, 'c': 0x43, 'v': 0x56, 'x': 0x58,
    }
    KEYUP = 0x0002
    codes = [VK[k.lower()] for k in keys if k.lower() in VK]
    for vk in codes:
        user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.04)
    for vk in reversed(codes):
        user32.keybd_event(vk, 0, KEYUP, 0)

def beep_sound():
    try:
        import winsound
        winsound.Beep(1000, 50)
    except Exception:
        pass

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".langfixer_pro.json")

DEFAULT_SETTINGS = {
    "always_on_top": True,
    "sound_enabled": True,
    "direction": "auto",
    "hotkey": "ctrl+shift+f9",
    "first_run": True,
    "check_updates": True,
    "total_conversions": 0,
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                s = DEFAULT_SETTINGS.copy()
                s.update(json.load(f))
                return s
    except Exception:
        pass
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------------------------------------------------------
# Character Maps
# ---------------------------------------------------------

EN_TO_AR_MAP = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ',
    'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'د',
    'a': 'ش', 's': 'س', 'd': 'ي', 'f': 'ب', 'g': 'ل', 'h': 'ا',
    'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ك', "'": 'ط',
    'z': 'ئ', 'x': 'ء', 'c': 'ؤ', 'v': 'ر', 'b': 'لا', 'n': 'ى',
    'm': 'ة', ',': 'و', '.': 'ز', '/': 'ظ',
    '`': 'ذ', '~': 'ّ',
    'Q': 'َ', 'W': 'ً', 'E': 'ُ', 'R': 'ٌ', 'T': 'لإ', 'Y': 'إ',
    'U': '`', 'I': '÷', 'O': '×', 'P': '؛', '{': '<', '}': '>',
    'A': 'ِ', 'S': 'ٍ', 'D': ']', 'F': '[', 'G': 'لأ', 'H': 'أ',
    'J': 'ـ', 'K': '،', 'L': '/', ':': ':', '"': '"',
    'Z': '~', 'X': 'ْ', 'C': '{', 'V': '}', 'B': 'لآ', 'N': 'آ',
    'M': "'", '<': ',', '>': '.', '?': '؟'
}

AR_TO_EN_MAP = {}
for k, v in EN_TO_AR_MAP.items():
    if len(v) == 1:
        AR_TO_EN_MAP[v] = k

COMPOUND_AR = [('لآ', 'B'), ('لأ', 'G'), ('لإ', 'T'), ('لا', 'b')]

def convert_text(text, direction="auto"):
    ar_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    en_count = sum(1 for c in text if c.isascii() and c.isalpha())

    if direction == "auto":
        is_arabic = ar_count >= en_count
    elif direction == "ar_to_en":
        is_arabic = True
    else:
        is_arabic = False

    result = []
    if is_arabic:
        temp = text
        for ar, en in COMPOUND_AR:
            temp = temp.replace(ar, en)
        for ch in temp:
            result.append(AR_TO_EN_MAP.get(ch, ch))
    else:
        for ch in text:
            result.append(EN_TO_AR_MAP.get(ch, ch))

    return "".join(result)


# ---------------------------------------------------------
# Colors
# ---------------------------------------------------------

C = {
    "bg":           "#0F1117",
    "card":         "#1A1D27",
    "card_hover":   "#222636",
    "accent":       "#1A6FD4",
    "accent_l":     "#2B88ED",
    "accent_glow":  "#1A6FD430",
    "success":      "#22C55E",
    "warning":      "#FBBF24",
    "danger":       "#EF4444",
    "danger_h":     "#DC2626",
    "text":         "#F1F5F9",
    "text2":        "#94A3B8",
    "muted":        "#64748B",
    "border":       "#2A2E3B",
}


# ---------------------------------------------------------
# Floating Button
# ---------------------------------------------------------

class FloatingButton(ctk.CTkToplevel):
    def __init__(self, master, on_click_callback):
        super().__init__(master)
        self.on_click_callback = on_click_callback
        self._visible = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        BG = "#010101"
        self.configure(fg_color=BG)
        try:
            self.attributes("-transparentcolor", BG)
        except Exception:
            pass

        s = 42
        self.btn = ctk.CTkButton(
            self, text="ع⇄A", width=s, height=s, corner_radius=21,
            font=("Segoe UI", 13, "bold"),
            fg_color=C["accent"], hover_color=C["accent_l"],
            text_color="white", command=self._on_click,
        )
        self.btn.pack(padx=1, pady=1)
        self.geometry(f"{s+2}x{s+2}")
        self.withdraw()

    def show_at(self, x, y):
        self.geometry(f"+{x+10}+{y-52}")
        if not self._visible:
            self._visible = True
            self.deiconify()
            self.lift()
            self.attributes("-alpha", 0.95)

    def hide(self):
        if self._visible:
            self._visible = False
            self.withdraw()

    def _on_click(self):
        self.hide()
        self.after(80, self.on_click_callback)

    @property
    def is_visible(self):
        return self._visible

    def get_window_rect(self):
        try:
            x, y = self.winfo_x(), self.winfo_y()
            return (x, y, x + self.winfo_width(), y + self.winfo_height())
        except Exception:
            return (0, 0, 0, 0)


# ---------------------------------------------------------
# Welcome Dialog
# ---------------------------------------------------------

class WelcomeDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Welcome to {APP_NAME}")
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        # محتوى
        ctk.CTkLabel(
            self, text="!مرحباً",
            font=("Segoe UI", 28, "bold"), text_color=C["text"]
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self, text=f"Welcome to {APP_NAME} v{APP_VERSION}",
            font=("Segoe UI", 14), text_color=C["accent_l"]
        ).pack(pady=(0, 15))

        # تعليمات
        steps_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12)
        steps_frame.pack(padx=25, fill="x")
        steps_inner = ctk.CTkFrame(steps_frame, fg_color="transparent")
        steps_inner.pack(padx=20, pady=16)

        steps = [
            ("1", "Select any mistyped text"),
            ("2", "Click the floating blue button"),
            ("3", "Text converts to the right language!"),
        ]
        for num, text in steps:
            row = ctk.CTkFrame(steps_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text=num, width=28, height=28,
                corner_radius=14, fg_color=C["accent"],
                font=("Segoe UI", 12, "bold"), text_color="white"
            ).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                row, text=text,
                font=("Segoe UI", 12), text_color=C["text2"], anchor="w"
            ).pack(side="left", fill="x")

        # اختصار
        ctk.CTkLabel(
            self, text="You can also use  Ctrl + Shift + F9  as a shortcut",
            font=("Segoe UI", 11), text_color=C["muted"]
        ).pack(pady=(15, 0))

        # زر البدء
        ctk.CTkButton(
            self, text="Get Started", width=200, height=40,
            corner_radius=10, font=("Segoe UI", 14, "bold"),
            fg_color=C["accent"], hover_color=C["accent_l"],
            command=self._close
        ).pack(pady=18)

        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        self.grab_release()
        self.destroy()


# ---------------------------------------------------------
# About Dialog
# ---------------------------------------------------------

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master, settings):
        super().__init__(master)
        self.title(f"About {APP_NAME}")
        self.geometry("380x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        # أيقونة
        ctk.CTkLabel(
            self, text="  ع A  ", width=60, height=60,
            corner_radius=16, fg_color=C["accent"],
            font=("Segoe UI", 20, "bold"), text_color="white"
        ).pack(pady=(25, 8))

        ctk.CTkLabel(
            self, text=APP_NAME,
            font=("Segoe UI", 22, "bold"), text_color=C["text"]
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            self, text=f"Version {APP_VERSION}",
            font=("Segoe UI", 12), text_color=C["accent_l"]
        ).pack(pady=(0, 12))

        # معلومات
        info_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12)
        info_frame.pack(padx=25, fill="x")
        info_inner = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_inner.pack(padx=18, pady=14, fill="x")

        total = settings.get("total_conversions", 0)
        infos = [
            ("Developer", APP_AUTHOR),
            ("License", APP_LICENSE),
            ("Total Conversions", f"{total:,}"),
        ]
        for i, (label, value) in enumerate(infos):
            row = ctk.CTkFrame(info_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12), text_color=C["muted"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 12, "bold"), text_color=C["text"]).pack(side="right")
            if i < len(infos) - 1:
                ctk.CTkFrame(info_inner, fg_color=C["border"], height=1).pack(fill="x", pady=4)

        # أزرار
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=18)

        ctk.CTkButton(
            btn_frame, text="GitHub", width=120, height=36,
            corner_radius=10, font=("Segoe UI", 12),
            fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            command=lambda: webbrowser.open(APP_GITHUB)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Check Updates", width=140, height=36,
            corner_radius=10, font=("Segoe UI", 12),
            fg_color=C["accent"], hover_color=C["accent_l"],
            command=lambda: self._check_update()
        ).pack(side="left", padx=5)

        self.update_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11), text_color=C["muted"]
        )
        self.update_label.pack()

        self.protocol("WM_DELETE_WINDOW", self._close)

    def _check_update(self):
        self.update_label.configure(text="Checking...", text_color=C["warning"])
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        try:
            import urllib.request
            req = urllib.request.Request(UPDATE_CHECK_URL, headers={"User-Agent": "LangFixer"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                latest = data.get("tag_name", "").lstrip("v")
                if latest and latest != APP_VERSION:
                    self.after(0, lambda: self.update_label.configure(
                        text=f"New version available: v{latest}!", text_color=C["success"]
                    ))
                else:
                    self.after(0, lambda: self.update_label.configure(
                        text="You're up to date!", text_color=C["success"]
                    ))
        except Exception:
            self.after(0, lambda: self.update_label.configure(
                text="Could not check for updates", text_color=C["danger"]
            ))

    def _close(self):
        self.grab_release()
        self.destroy()


# ---------------------------------------------------------
# Main App
# ---------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()

        self.title(f"{APP_NAME}")
        self.geometry("380x680")
        self.resizable(False, False)

        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=C["bg"])

        if self.settings.get("always_on_top", True):
            self.attributes("-topmost", True)

        self.tray_icon = None
        self.conversion_count = 0
        self.is_active = True
        self.processing = False
        self._recording_hotkey = False
        self._recorded_keys = set()

        self._drag_start_x = 0
        self._drag_start_y = 0
        self._mouse_is_down = False

        self.create_widgets()
        self.floating_btn = FloatingButton(self, self._do_convert)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._start_mouse_listener()
        self._start_keyboard_listener()
        self._start_hotkey_listener()

        # رسالة الترحيب أول مرة
        if self.settings.get("first_run", True):
            self.after(500, self._show_welcome)

        # فحص التحديثات عند التشغيل
        if self.settings.get("check_updates", True):
            threading.Thread(target=self._silent_update_check, daemon=True).start()

    def _show_welcome(self):
        WelcomeDialog(self)
        self.settings["first_run"] = False
        save_settings(self.settings)

    def _silent_update_check(self):
        """فحص صامت للتحديثات"""
        try:
            time.sleep(3)
            import urllib.request
            req = urllib.request.Request(UPDATE_CHECK_URL, headers={"User-Agent": "LangFixer"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                latest = data.get("tag_name", "").lstrip("v")
                if latest and latest != APP_VERSION:
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Update available: v{latest}",
                        text_color=C["warning"]
                    ))
        except Exception:
            pass

    def create_widgets(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, height=100)
        header.pack(pady=(12, 0), padx=16, fill="x")
        header.pack_propagate(False)

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(pady=(14, 0))

        ctk.CTkLabel(
            title_row, text="  ع A  ",
            font=("Segoe UI", 12, "bold"),
            fg_color=C["accent"], corner_radius=8, text_color="white",
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            title_row, text=APP_NAME,
            font=("Segoe UI Semibold", 20), text_color=C["text"]
        ).pack(side="left")

        # About button
        ctk.CTkButton(
            title_row, text="?", width=28, height=28, corner_radius=14,
            font=("Segoe UI", 13, "bold"),
            fg_color=C["border"], hover_color=C["card_hover"],
            text_color=C["muted"], command=self._show_about
        ).pack(side="right", padx=(10, 0))

        hotkey_display = self.settings.get("hotkey", "ctrl+shift+f9").upper().replace("+", " + ")
        self.status_label = ctk.CTkLabel(
            header,
            text=f"Select text  ·  {hotkey_display}",
            text_color=C["accent_l"], font=("Segoe UI", 11)
        )
        self.status_label.pack(pady=(6, 0))

        # Counter
        self.counter_label = ctk.CTkLabel(
            self, text="0 conversions",
            font=("Segoe UI", 11), text_color=C["muted"]
        )
        self.counter_label.pack(pady=(8, 0))
        self._update_counter()

        # ── Options Card ──
        opts_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        opts_card.pack(pady=(8, 0), padx=16, fill="x")
        opts = ctk.CTkFrame(opts_card, fg_color="transparent")
        opts.pack(padx=16, pady=12, fill="x")

        self.switch_var = ctk.BooleanVar(value=True)
        self._switch_row(opts, "Enable", self.switch_var, self._toggle_active)
        self._divider(opts)

        self.topmost_var = ctk.BooleanVar(value=self.settings.get("always_on_top", True))
        self._switch_row(opts, "Always on Top", self.topmost_var, self._toggle_topmost)
        self._divider(opts)

        self.sound_var = ctk.BooleanVar(value=self.settings.get("sound_enabled", True))
        self._switch_row(opts, "Sound Feedback", self.sound_var, self._toggle_sound)

        # ── Mode Card ──
        mode_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        mode_card.pack(pady=(8, 0), padx=16, fill="x")
        mode = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode.pack(padx=16, pady=12, fill="x")

        ctk.CTkLabel(mode, text="Conversion Mode", font=("Segoe UI Semibold", 13), text_color=C["text"]).pack(anchor="w", pady=(0, 6))

        self.direction_var = ctk.StringVar(value=self.settings.get("direction", "auto"))
        for label, val in [("Auto Detect", "auto"), ("Arabic  →  English", "ar_to_en"), ("English  →  Arabic", "en_to_ar")]:
            ctk.CTkRadioButton(
                mode, text=label, variable=self.direction_var, value=val,
                command=self._change_dir, font=("Segoe UI", 12),
                text_color=C["text2"], fg_color=C["accent"],
                hover_color=C["accent_l"], border_color=C["border"],
            ).pack(pady=2, anchor="w", padx=4)

        # ── Hotkey Card ──
        hk_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        hk_card.pack(pady=(8, 0), padx=16, fill="x")
        hk = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk.pack(padx=16, pady=12, fill="x")

        hk_top = ctk.CTkFrame(hk, fg_color="transparent")
        hk_top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(hk_top, text="Keyboard Shortcut", font=("Segoe UI Semibold", 13), text_color=C["text"]).pack(side="left")
        self.hotkey_hint = ctk.CTkLabel(hk_top, text="Click to record", font=("Segoe UI", 10), text_color=C["muted"])
        self.hotkey_hint.pack(side="right")

        hk_display = self.settings.get("hotkey", "ctrl+shift+f9").upper().replace("+", " + ")
        self.hotkey_entry = ctk.CTkEntry(
            hk, height=36, font=("Segoe UI Semibold", 13), justify="center",
            text_color=C["accent_l"], fg_color=C["bg"],
            border_color=C["border"], corner_radius=10, state="normal",
        )
        self.hotkey_entry.insert(0, hk_display)
        self.hotkey_entry.configure(state="disabled")
        self.hotkey_entry.pack(fill="x")
        self.hotkey_entry.bind("<Button-1>", self._start_hotkey_recording)

        # ── Buttons ──
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=12, padx=16, fill="x")

        ctk.CTkButton(
            bf, text="Hide to Tray", width=155, height=36, corner_radius=10,
            font=("Segoe UI", 12), fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            command=self.hide_window
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            bf, text="Exit", width=100, height=36, corner_radius=10,
            font=("Segoe UI", 12), fg_color=C["danger"], hover_color=C["danger_h"],
            text_color="white", command=self._full_quit
        ).pack(side="right")

        # ── Footer ──
        ctk.CTkLabel(
            self, text=f"v{APP_VERSION}  ·  Open Source  ·  MIT License",
            font=("Segoe UI", 10), text_color=C["muted"]
        ).pack(pady=(2, 8))

    def _switch_row(self, parent, text, var, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text=text, font=("Segoe UI", 12), text_color=C["text2"]).pack(side="left")
        ctk.CTkSwitch(
            row, text="", command=cmd, variable=var, width=44,
            progress_color=C["accent"], button_color="white",
            button_hover_color="#E2E8F0", fg_color=C["border"],
        ).pack(side="right")

    def _divider(self, parent):
        ctk.CTkFrame(parent, fg_color=C["border"], height=1).pack(fill="x", pady=7)

    def _show_about(self):
        AboutDialog(self, self.settings)

    # ── Mouse Listener ──

    def _start_mouse_listener(self):
        self._last_click_time = 0
        self._click_count = 0

        def on_click(x, y, button, pressed):
            if button != pynput_mouse.Button.left:
                return
            if pressed:
                self._drag_start_x = x
                self._drag_start_y = y
                self._mouse_is_down = True
                now = time.time()
                if now - self._last_click_time < 0.4:
                    self._click_count += 1
                else:
                    self._click_count = 1
                self._last_click_time = now
                if self.floating_btn.is_visible:
                    rect = self.floating_btn.get_window_rect()
                    if not (rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]):
                        self.after(0, self.floating_btn.hide)
            else:
                if self._mouse_is_down:
                    self._mouse_is_down = False
                    if not self.is_active:
                        return
                    if self._click_count >= 2:
                        self.after(50, lambda: self._check_and_show(x, y))
                        return
                    dx = abs(x - self._drag_start_x)
                    dy = abs(y - self._drag_start_y)
                    if dx > 3 or dy > 3:
                        self.after(50, lambda: self._check_and_show(x, y))

        listener = pynput_mouse.Listener(on_click=on_click)
        listener.daemon = True
        listener.start()

    def _check_and_show(self, x, y):
        if not self.is_active or self.processing:
            return
        def check():
            try:
                old_clip = pyperclip.paste()
            except Exception:
                old_clip = ""
            try:
                pyperclip.copy("")
                time.sleep(0.02)
                send_key_combo(['ctrl', 'c'])
                time.sleep(0.1)
                text = pyperclip.paste()
                if old_clip and not text:
                    pyperclip.copy(old_clip)
                if text and text.strip():
                    pyperclip.copy(old_clip)
                    self.after(0, lambda: self.floating_btn.show_at(x, y))
            except Exception:
                pass
        threading.Thread(target=check, daemon=True).start()

    # ── Keyboard Listener ──

    def _start_keyboard_listener(self):
        self._shift_held = False
        self._kb_timer = None

        def on_press(key):
            try:
                if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
                    self._shift_held = True
                if self._shift_held and key in (
                    pynput_keyboard.Key.left, pynput_keyboard.Key.right,
                    pynput_keyboard.Key.up, pynput_keyboard.Key.down,
                    pynput_keyboard.Key.home, pynput_keyboard.Key.end,
                ):
                    if self.is_active:
                        if self._kb_timer:
                            try: self.after_cancel(self._kb_timer)
                            except: pass
                        self._kb_timer = self.after(400, self._show_button_at_cursor)
                if not self._shift_held and hasattr(key, 'char') and key.char:
                    self.after(0, self.floating_btn.hide)
                if key == pynput_keyboard.Key.esc:
                    self.after(0, self.floating_btn.hide)
            except Exception:
                pass

        def on_release(key):
            try:
                if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
                    self._shift_held = False
            except Exception:
                pass

        listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()

    # ── Hotkey Recording ──

    def _start_hotkey_recording(self, event=None):
        if self._recording_hotkey:
            return
        self._recording_hotkey = True
        self._recorded_keys = set()

        self.hotkey_entry.configure(state="normal")
        self.hotkey_entry.delete(0, "end")
        self.hotkey_entry.insert(0, "Press keys...")
        self.hotkey_entry.configure(border_color=C["accent"], text_color=C["warning"])
        self.hotkey_hint.configure(text="Press your shortcut", text_color=C["warning"])

        self._record_listener = pynput_keyboard.Listener(
            on_press=self._on_record_press, on_release=self._on_record_release
        )
        self._record_listener.daemon = True
        self._record_listener.start()

    def _on_record_press(self, key):
        if not self._recording_hotkey:
            return
        name = self._full_key_name(key)
        if not name:
            return
        modifiers = {'ctrl', 'shift', 'alt'}
        has_mod = bool(self._recorded_keys & modifiers)
        has_reg = bool(self._recorded_keys - modifiers)
        if has_mod and has_reg:
            return
        self._recorded_keys.add(name)
        display = " + ".join(sorted(self._recorded_keys, key=self._key_sort)).upper()
        self.after(0, lambda: self._update_hk_display(display))
        has_mod = bool(self._recorded_keys & modifiers)
        has_reg = bool(self._recorded_keys - modifiers)
        if has_mod and has_reg:
            self.after(300, self._finish_hotkey_recording)

    def _on_record_release(self, key):
        pass

    def _update_hk_display(self, text):
        self.hotkey_entry.configure(state="normal")
        self.hotkey_entry.delete(0, "end")
        self.hotkey_entry.insert(0, text)

    def _finish_hotkey_recording(self):
        if not self._recording_hotkey:
            return
        self._recording_hotkey = False
        try: self._record_listener.stop()
        except: pass

        ordered = sorted(self._recorded_keys, key=self._key_sort)
        hotkey_str = "+".join(ordered)
        display = " + ".join(ordered).upper()

        self.settings["hotkey"] = hotkey_str
        save_settings(self.settings)

        self.hotkey_entry.configure(state="normal")
        self.hotkey_entry.delete(0, "end")
        self.hotkey_entry.insert(0, display)
        self.hotkey_entry.configure(state="disabled", border_color=C["border"], text_color=C["accent_l"])
        self.hotkey_hint.configure(text="Saved!", text_color=C["success"])
        self.after(2000, lambda: self.hotkey_hint.configure(text="Click to record", text_color=C["muted"]))

        self.status_label.configure(text=f"Select text  ·  {display}")
        self._restart_hotkey_listener()

    def _key_sort(self, key):
        return {'ctrl': 0, 'shift': 1, 'alt': 2}.get(key, 3)

    def _full_key_name(self, key):
        try:
            if key in (pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r): return 'ctrl'
            if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r): return 'shift'
            if key in (pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r): return 'alt'
            fkeys = {
                pynput_keyboard.Key.f1:'f1', pynput_keyboard.Key.f2:'f2', pynput_keyboard.Key.f3:'f3',
                pynput_keyboard.Key.f4:'f4', pynput_keyboard.Key.f5:'f5', pynput_keyboard.Key.f6:'f6',
                pynput_keyboard.Key.f7:'f7', pynput_keyboard.Key.f8:'f8', pynput_keyboard.Key.f9:'f9',
                pynput_keyboard.Key.f10:'f10', pynput_keyboard.Key.f11:'f11', pynput_keyboard.Key.f12:'f12',
            }
            if key in fkeys: return fkeys[key]
            special = {
                pynput_keyboard.Key.space:'space', pynput_keyboard.Key.enter:'enter',
                pynput_keyboard.Key.tab:'tab', pynput_keyboard.Key.backspace:'backspace',
                pynput_keyboard.Key.delete:'delete', pynput_keyboard.Key.home:'home',
                pynput_keyboard.Key.end:'end', pynput_keyboard.Key.insert:'insert',
            }
            if key in special: return special[key]
            if hasattr(key, 'char') and key.char: return key.char.lower()
        except Exception:
            pass
        return None

    # ── Hotkey Listener ──

    def _start_hotkey_listener(self):
        self._hotkey_keys = set()
        self._hotkey_target = set(self.settings.get("hotkey", "ctrl+shift+f9").split("+"))

        def on_press(key):
            if self._recording_hotkey:
                return
            try:
                name = self._full_key_name(key)
                if name:
                    self._hotkey_keys.add(name)
                if self._hotkey_target and self._hotkey_target.issubset(self._hotkey_keys):
                    self._hotkey_keys.clear()
                    if self.is_active and not self.processing:
                        self.after(0, self.floating_btn.hide)
                        threading.Thread(target=self._do_convert_direct, daemon=True).start()
            except Exception:
                pass

        def on_release(key):
            if self._recording_hotkey:
                return
            try:
                name = self._full_key_name(key)
                if name:
                    self._hotkey_keys.discard(name)
            except Exception:
                pass

        self._hk_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        self._hk_listener.daemon = True
        self._hk_listener.start()

    def _restart_hotkey_listener(self):
        try: self._hk_listener.stop()
        except: pass
        self._start_hotkey_listener()

    def _show_button_at(self, x, y):
        if self.is_active and not self.processing:
            self.floating_btn.show_at(x, y)

    def _show_button_at_cursor(self):
        if self.is_active and not self.processing:
            x, y = get_cursor_pos()
            self.floating_btn.show_at(x, y)

    # ── Convert ──

    def _do_convert(self):
        if self.processing: return
        self.processing = True
        threading.Thread(target=self._convert_worker, daemon=True).start()

    def _do_convert_direct(self):
        if self.processing: return
        self.processing = True
        self._convert_worker()

    def _convert_worker(self):
        try:
            try: old_clip = pyperclip.paste()
            except: old_clip = ""

            pyperclip.copy("")
            time.sleep(0.03)
            send_key_combo(['ctrl', 'x'])
            time.sleep(0.15)

            text = ""
            for _ in range(12):
                text = pyperclip.paste()
                if text: break
                time.sleep(0.04)

            if not text or not text.strip():
                pyperclip.copy("")
                time.sleep(0.03)
                send_key_combo(['ctrl', 'c'])
                time.sleep(0.15)
                for _ in range(12):
                    text = pyperclip.paste()
                    if text: break
                    time.sleep(0.04)
                if not text or not text.strip():
                    if old_clip: pyperclip.copy(old_clip)
                    self.processing = False
                    return

            converted = convert_text(text, self.settings.get("direction", "auto"))

            pyperclip.copy(converted)
            time.sleep(0.03)
            send_key_combo(['ctrl', 'v'])
            time.sleep(0.08)

            self.conversion_count += 1
            self.settings["total_conversions"] = self.settings.get("total_conversions", 0) + 1
            save_settings(self.settings)

            if self.settings.get("sound_enabled", True):
                threading.Thread(target=beep_sound, daemon=True).start()

        except Exception as e:
            print(f"Convert error: {e}")
        finally:
            time.sleep(0.2)
            self.processing = False

    # ── Settings ──

    def _toggle_active(self):
        self.is_active = self.switch_var.get()
        hk = self.settings.get("hotkey", "ctrl+shift+f9").upper().replace("+", " + ")
        if self.is_active:
            self.status_label.configure(text=f"Select text  ·  {hk}", text_color=C["accent_l"])
        else:
            self.status_label.configure(text="Paused", text_color=C["danger"])
            self.floating_btn.hide()

    def _toggle_topmost(self):
        v = self.topmost_var.get()
        self.attributes("-topmost", v)
        self.settings["always_on_top"] = v
        save_settings(self.settings)

    def _toggle_sound(self):
        self.settings["sound_enabled"] = self.sound_var.get()
        save_settings(self.settings)

    def _change_dir(self):
        self.settings["direction"] = self.direction_var.get()
        save_settings(self.settings)

    def _update_counter(self):
        n = self.conversion_count
        self.counter_label.configure(text=f"{n} conversion{'s' if n != 1 else ''}")
        self.after(1000, self._update_counter)

    # ── System Tray ──

    def _make_tray_img(self):
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((2, 2, 62, 62), radius=14, fill=C["accent"])
        d.text((10, 18), "ع/A", fill="white")
        return img

    def hide_window(self):
        self.withdraw()
        if self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
        img = self._make_tray_img()
        menu = pystray.Menu(
            pystray.MenuItem('Show', self._show_from_tray),
            pystray.MenuItem('Exit', self._quit_from_tray)
        )
        self.tray_icon = pystray.Icon("LangFixer", img, APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
            self.tray_icon = None
        self.after(0, self.deiconify)

    def _quit_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
        self._cleanup()

    def _full_quit(self):
        self._cleanup()

    def _cleanup(self):
        save_settings(self.settings)
        self.floating_btn.hide()
        if self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = App()
    app.mainloop()