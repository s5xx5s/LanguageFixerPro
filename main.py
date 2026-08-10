"""
Language Fixer Pro v1.5.0
=========================
Open Source Arabic ↔ English keyboard layout fixer.
GitHub: https://github.com/s5xx5s/LanguageFixerPro

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
import subprocess
import webbrowser

# ---------------------------------------------------------
# App Info
# ---------------------------------------------------------

APP_NAME = "Language Fixer Pro"
APP_VERSION = "1.5.0"
APP_AUTHOR = "s5xx5s"
APP_GITHUB = "https://github.com/s5xx5s/LanguageFixerPro"
APP_LICENSE = "MIT License"
UPDATE_CHECK_URL = "https://api.github.com/repos/s5xx5s/LanguageFixerPro/releases/latest"

APP_ID = "s5xx5s.LanguageFixerPro"          # taskbar grouping identity
# "Local\" scopes the mutex to the logon session, which is what we want: one copy
# per signed-in user. "Global\" needs SeCreateGlobalPrivilege, which a standard
# user does not have — CreateMutexW then fails and the guard silently never fires.
MUTEX_NAME = "Local\\LanguageFixerPro_SingleInstance"

# ---------------------------------------------------------
# Windows API
# ---------------------------------------------------------

user32 = ctypes.windll.user32
# use_last_error so GetLastError reflects CreateMutexW and not some later ctypes call
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_instance_mutex = None

IS_FROZEN = getattr(sys, "frozen", False)


def resource_path(name):
    """Resolve a bundled resource, both from source and from a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def app_icon_path():
    p = resource_path("app_icon.ico")
    return p if os.path.exists(p) else None


def set_app_user_model_id():
    """Give the app its own taskbar / tray identity instead of inheriting python.exe."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def already_running():
    """True when another copy already holds the single-instance mutex."""
    global _instance_mutex
    ERROR_ALREADY_EXISTS = 183
    try:
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        err = ctypes.get_last_error()
        if not handle:
            return False          # could not create it — better to run than to block
        _instance_mutex = handle  # hold it open for the life of the process
        return err == ERROR_ALREADY_EXISTS
    except Exception:
        return False


def activate_existing_instance():
    """Surface the copy that is already running, rather than nagging with a dialog."""
    SW_RESTORE = 9
    try:
        hwnd = user32.FindWindowW(None, APP_NAME)
        if not hwnd:
            return False
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# Run at Windows startup (HKCU — no admin rights needed)
# ---------------------------------------------------------

STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_REG_NAME = "LanguageFixerPro"


def _startup_command():
    if IS_FROZEN:
        return f'"{sys.executable}" --minimized'
    script = os.path.abspath(__file__)
    return f'"{sys.executable}" "{script}" --minimized'


def is_startup_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH) as key:
            value, _ = winreg.QueryValueEx(key, STARTUP_REG_NAME)
            return bool(value)
    except Exception:
        return False


def set_startup_enabled(enabled):
    """Register/unregister the app in HKCU Run. Returns True on success."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, STARTUP_REG_NAME, 0, winreg.REG_SZ,
                                  _startup_command())
            else:
                try:
                    winreg.DeleteValue(key, STARTUP_REG_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


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
    "start_with_windows": False,
    "close_to_tray": True,
    "show_floating_button": True,
    "language": "en",
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
# Interface language
# ---------------------------------------------------------

TR = {
    "en": {
        "dir": "ltr",
        "tagline": "Select text  ·  {hk}",
        "paused": "Paused",
        "conversions_one": "1 conversion",
        "conversions_many": "{n} conversions",
        "enable": "Enable",
        "floating_button": "Floating Button",
        "always_on_top": "Always on Top",
        "sound_feedback": "Sound Feedback",
        "start_with_windows": "Start with Windows",
        "conversion_mode": "Conversion Mode",
        "auto_detect": "Auto Detect",
        "ar_to_en": "Arabic  →  English",
        "en_to_ar": "English  →  Arabic",
        "keyboard_shortcut": "Keyboard Shortcut",
        "click_to_record": "Click to record",
        "press_keys": "Press keys...",
        "press_shortcut": "Press your shortcut",
        "saved": "Saved!",
        "hide_to_tray": "Hide to Tray",
        "exit": "Exit",
        "footer_parts": ["v{v}", "·", "Open Source", "·", "MIT License"],
        "startup_on": "Startup enabled",
        "startup_off": "Startup disabled",
        "startup_failed": "Could not update startup",
        "floating_on": "Floating button on",
        "floating_off": "Shortcut only",
        "update_available": "Update available: v{v}",
        "lang_switch": "العربية",
        # tray
        "tray_show": "Show",
        "tray_enabled": "Enabled",
        "tray_exit": "Exit",
        # about
        "about_title": "About {app}",
        "version": "Version {v}",
        "developer": "Developer",
        "license": "License",
        "total_conversions": "Total Conversions",
        "github": "GitHub",
        "check_updates": "Check Updates",
        "checking": "Checking...",
        "up_to_date": "You're up to date!",
        "check_failed": "Could not check for updates",
        "new_version": "New version available: v{v}!",
        # welcome
        "welcome_title": "Welcome!",
        "welcome_sub": "Welcome to {app} v{v}",
        "step1": "Select any mistyped text",
        "step2": "Click the floating blue button",
        "step3": "Text converts to the right language!",
        "shortcut_hint": "You can also use  {hk}  as a shortcut",
        "get_started": "Get Started",
        # updater
        "update_title": "Update Available",
        "update_body": "Version {new} is available.\nYou are running version {cur}.",
        "update_install": "Download & Install",
        "update_later": "Later",
        "update_downloading": "Downloading...  {pct}%",
        "update_verifying": "Preparing installer...",
        "update_launching": "Installing. The app will restart.",
        "update_failed": "Download failed: {err}",
        "update_portable": "You are running the portable version.\n"
                           "Download the new version from the releases page.",
        "open_releases": "Open Releases",
        "close": "Close",
    },
    "ar": {
        "dir": "rtl",
        "tagline": "حدّد نصاً  ·  {hk}",
        "paused": "متوقف",
        "conversions_one": "تحويل واحد",
        "conversions_many": "{n} تحويل",
        "enable": "تفعيل",
        "floating_button": "الزر العائم",
        "always_on_top": "دائماً في المقدمة",
        "sound_feedback": "تنبيه صوتي",
        "start_with_windows": "التشغيل مع ويندوز",
        "conversion_mode": "وضع التحويل",
        "auto_detect": "كشف تلقائي",
        "ar_to_en": "عربي  ←  إنجليزي",
        "en_to_ar": "إنجليزي  ←  عربي",
        "keyboard_shortcut": "اختصار لوحة المفاتيح",
        "click_to_record": "انقر للتسجيل",
        "press_keys": "...اضغط المفاتيح",
        "press_shortcut": "اضغط اختصارك",
        "saved": "تم الحفظ",
        "hide_to_tray": "إخفاء في الشريط",
        "exit": "خروج",
        # Tk has no bidi engine, so a mixed Arabic/Latin line comes out transposed.
        # The footer is laid out as one label per run instead (see create_widgets),
        # and the "v" prefix keeps the version in Latin digits.
        "footer_parts": ["مفتوح المصدر", "·", "رخصة", "MIT", "·", "v{v}"],
        "startup_on": "تم تفعيل التشغيل التلقائي",
        "startup_off": "تم إيقاف التشغيل التلقائي",
        "startup_failed": "تعذّر تحديث التشغيل التلقائي",
        "floating_on": "الزر العائم مُفعّل",
        "floating_off": "الاختصار فقط",
        "update_available": "يتوفر تحديث: v{v}",
        "lang_switch": "English",
        # tray
        "tray_show": "إظهار",
        "tray_enabled": "مُفعّل",
        "tray_exit": "خروج",
        # about
        "about_title": "عن {app}",
        "version": "الإصدار v{v}",
        "developer": "المطوّر",
        "license": "الرخصة",
        "total_conversions": "مجموع التحويلات",
        "github": "GitHub",
        "check_updates": "فحص التحديثات",
        "checking": "...جارٍ الفحص",
        "up_to_date": "أنت على أحدث إصدار",
        "check_failed": "تعذّر فحص التحديثات",
        "new_version": "يتوفر إصدار جديد: v{v}",
        # welcome
        "welcome_title": "مرحباً!",
        "welcome_sub": "أهلاً بك في {app} v{v}",
        "step1": "حدّد أي نص مكتوب بلغة خاطئة",
        "step2": "انقر الزر الأزرق العائم",
        "step3": "يتحوّل النص إلى اللغة الصحيحة",
        "shortcut_hint": "يمكنك أيضاً استخدام  {hk}  كاختصار",
        "get_started": "لنبدأ",
        # updater
        "update_title": "يتوفر تحديث",
        "update_body": "الإصدار v{new} متاح الآن.\nأنت تستخدم الإصدار v{cur}.",
        "update_install": "تنزيل وتثبيت",
        "update_later": "لاحقاً",
        "update_downloading": "جارٍ التنزيل...  {pct}%",
        "update_verifying": "جارٍ تجهيز المُثبِّت...",
        "update_launching": "جارٍ التثبيت. سيُعاد تشغيل التطبيق.",
        "update_failed": "فشل التنزيل: {err}",
        "update_portable": "أنت تستخدم النسخة المحمولة.\n"
                           "نزّل الإصدار الجديد من صفحة الإصدارات.",
        "open_releases": "فتح صفحة الإصدارات",
        "close": "إغلاق",
    },
}


def tr(lang, key, **kw):
    """Translate. Falls back to English so a missing key never breaks the UI."""
    table = TR.get(lang) or TR["en"]
    text = table.get(key) or TR["en"].get(key, key)
    return text.format(**kw) if kw else text


def is_rtl(lang):
    return TR.get(lang, TR["en"])["dir"] == "rtl"


def make_globe_image(px=64, color="#94A3B8"):
    """A simple line-art globe, drawn at 4x and downsampled so it stays crisp."""
    s = px * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = max(2, s // 22)
    pad = w
    d.ellipse((pad, pad, s - pad, s - pad), outline=color, width=w)
    # meridians
    for shrink in (0.30, 0.62):
        rx = (s - 2 * pad) * shrink / 2
        cx = s / 2
        d.ellipse((cx - rx, pad, cx + rx, s - pad), outline=color, width=w)
    # parallels
    for fy in (0.32, 0.5, 0.68):
        y = pad + (s - 2 * pad) * fy
        half = ((s - 2 * pad) / 2) * (1 - abs(fy - 0.5) * 2) ** 0.5
        d.line((s / 2 - half, y, s / 2 + half, y), fill=color, width=w)
    return img.resize((px, px), Image.LANCZOS)


# ---------------------------------------------------------
# Version compare
# ---------------------------------------------------------

def version_tuple(v):
    """'1.10.2' -> (1, 10, 2). Non-numeric parts are dropped rather than crashing."""
    parts = []
    for chunk in str(v).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def is_newer(candidate, current):
    a, b = version_tuple(candidate), version_tuple(current)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


# ---------------------------------------------------------
# Updater
# ---------------------------------------------------------

SETUP_ASSET_NAME = "LanguageFixerPro-Setup.exe"
UNINSTALL_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\LanguageFixerPro"

# Downloads are only ever fetched from GitHub's own hosts. An asset URL that
# points anywhere else is treated as untrusted and refused.
ALLOWED_DOWNLOAD_HOSTS = (
    "github.com", "www.github.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
)


def _urlopen(url, timeout=15):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": f"LangFixer/{APP_VERSION}"})
    return urllib.request.urlopen(req, timeout=timeout)


def fetch_latest_release():
    """Returns {version, notes, url, size} for the newest release, or None."""
    try:
        with _urlopen(UPDATE_CHECK_URL) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    version = (data.get("tag_name") or "").lstrip("vV")
    if not version:
        return None

    asset = None
    for a in data.get("assets") or []:
        if a.get("name") == SETUP_ASSET_NAME:
            asset = a
            break

    return {
        "version": version,
        "notes": data.get("body") or "",
        "url": (asset or {}).get("browser_download_url"),
        "size": (asset or {}).get("size") or 0,
    }


def installed_location():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_PATH) as key:
            return winreg.QueryValueEx(key, "InstallLocation")[0]
    except Exception:
        return None


def running_installed_copy():
    """True when this exe is the installed one, so replacing it in place is right."""
    if not IS_FROZEN:
        return False
    loc = installed_location()
    if not loc:
        return False
    try:
        return os.path.normcase(os.path.dirname(os.path.abspath(sys.executable))) == \
               os.path.normcase(os.path.abspath(loc))
    except Exception:
        return False


def download_update(url, dest, on_progress=None, cancelled=None):
    """Stream an update to dest. Raises on a non-GitHub host or a truncated file."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError(f"refusing to download from {parsed.hostname or url!r}")

    tmp = dest + ".part"
    with _urlopen(url, timeout=30) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        with open(tmp, "wb") as f:
            while True:
                if cancelled and cancelled():
                    raise RuntimeError("cancelled")
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if on_progress:
                    on_progress(done, total)
    if total and done < total:
        os.remove(tmp)
        raise IOError("download truncated")
    if os.path.exists(dest):
        os.remove(dest)
    os.replace(tmp, dest)
    return dest


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
    def __init__(self, master, lang="en"):
        super().__init__(master)
        self.lang = lang
        rtl = is_rtl(lang)
        lead, trail = ("right", "left") if rtl else ("left", "right")

        self.title(tr(lang, "welcome_sub", app=APP_NAME, v=APP_VERSION))
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        ctk.CTkLabel(
            self, text=tr(lang, "welcome_title"),
            font=("Segoe UI", 28, "bold"), text_color=C["text"]
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self, text=tr(lang, "welcome_sub", app=APP_NAME, v=APP_VERSION),
            font=("Segoe UI", 14), text_color=C["accent_l"]
        ).pack(pady=(0, 15))

        steps_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12)
        steps_frame.pack(padx=25, fill="x")
        steps_inner = ctk.CTkFrame(steps_frame, fg_color="transparent")
        steps_inner.pack(padx=20, pady=16, fill="x")

        for i, key in enumerate(("step1", "step2", "step3"), start=1):
            row = ctk.CTkFrame(steps_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text=str(i), width=28, height=28,
                corner_radius=14, fg_color=C["accent"],
                font=("Segoe UI", 12, "bold"), text_color="white"
            ).pack(side=lead, padx=(0, 12) if not rtl else (12, 0))
            ctk.CTkLabel(
                row, text=tr(lang, key),
                font=("Segoe UI", 12), text_color=C["text2"],
                anchor="e" if rtl else "w"
            ).pack(side=lead, fill="x")

        hk = (master.settings.get("hotkey", "ctrl+shift+f9")
              if hasattr(master, "settings") else "ctrl+shift+f9")
        ctk.CTkLabel(
            self, text=tr(lang, "shortcut_hint", hk=hk.upper().replace("+", " + ")),
            font=("Segoe UI", 11), text_color=C["muted"]
        ).pack(pady=(15, 0))

        ctk.CTkButton(
            self, text=tr(lang, "get_started"), width=200, height=40,
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
    def __init__(self, master, settings, lang="en", on_update=None):
        super().__init__(master)
        self.lang = lang
        self.on_update = on_update
        self._release = None
        rtl = is_rtl(lang)
        self._lead, self._trail = ("right", "left") if rtl else ("left", "right")
        self.title(tr(lang, "about_title", app=APP_NAME))
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
            self, text=tr(lang, "version", v=APP_VERSION),
            font=("Segoe UI", 12), text_color=C["accent_l"]
        ).pack(pady=(0, 12))

        # معلومات
        info_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12)
        info_frame.pack(padx=25, fill="x")
        info_inner = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_inner.pack(padx=18, pady=14, fill="x")

        total = settings.get("total_conversions", 0)
        infos = [
            (tr(lang, "developer"), APP_AUTHOR),
            (tr(lang, "license"), APP_LICENSE),
            (tr(lang, "total_conversions"), f"{total:,}"),
        ]
        for i, (label, value) in enumerate(infos):
            row = ctk.CTkFrame(info_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12),
                         text_color=C["muted"]).pack(side=self._lead)
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 12, "bold"),
                         text_color=C["text"]).pack(side=self._trail)
            if i < len(infos) - 1:
                ctk.CTkFrame(info_inner, fg_color=C["border"], height=1).pack(fill="x", pady=4)

        # أزرار
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=18)

        ctk.CTkButton(
            btn_frame, text=tr(lang, "github"), width=120, height=36,
            corner_radius=10, font=("Segoe UI", 12),
            fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            command=lambda: webbrowser.open(APP_GITHUB)
        ).pack(side="left", padx=5)

        self.update_btn = ctk.CTkButton(
            btn_frame, text=tr(lang, "check_updates"), width=140, height=36,
            corner_radius=10, font=("Segoe UI", 12),
            fg_color=C["accent"], hover_color=C["accent_l"],
            command=self._check_update
        )
        self.update_btn.pack(side="left", padx=5)

        self.update_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11), text_color=C["muted"]
        )
        self.update_label.pack()

        self.protocol("WM_DELETE_WINDOW", self._close)

    def _check_update(self):
        if self._release and self.on_update:
            # second click: the user has seen the version and asked to proceed
            self._close()
            self.on_update(self._release)
            return
        self.update_label.configure(text=tr(self.lang, "checking"), text_color=C["warning"])
        self.update_btn.configure(state="disabled")
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        release = fetch_latest_release()
        self.after(0, lambda: self._show_check_result(release))

    def _show_check_result(self, release):
        self.update_btn.configure(state="normal")
        if not release:
            self.update_label.configure(text=tr(self.lang, "check_failed"),
                                        text_color=C["danger"])
            return
        if is_newer(release["version"], APP_VERSION):
            self._release = release
            self.update_label.configure(
                text=tr(self.lang, "new_version", v=release["version"]),
                text_color=C["success"])
            if self.on_update:
                self.update_btn.configure(text=tr(self.lang, "update_install"))
        else:
            self.update_label.configure(text=tr(self.lang, "up_to_date"),
                                        text_color=C["success"])

    def _close(self):
        self.grab_release()
        self.destroy()


# ---------------------------------------------------------
# Update Dialog
# ---------------------------------------------------------

class UpdateDialog(ctk.CTkToplevel):
    """Asks before downloading anything. Nothing is fetched until the user agrees."""

    def __init__(self, master, release, lang, on_quit):
        super().__init__(master)
        self.release = release
        self.lang = lang
        self.on_quit = on_quit
        self._cancelled = False
        self._busy = False

        self.title(self.t("update_title"))
        self.geometry("420x300")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.protocol("WM_DELETE_WINDOW", self._close)

        anchor = "e" if is_rtl(lang) else "w"
        just = "right" if is_rtl(lang) else "left"

        ctk.CTkLabel(self, text=self.t("update_title"),
                     font=("Segoe UI Semibold", 20),
                     text_color=C["text"]).pack(pady=(26, 6))

        ctk.CTkLabel(
            self,
            text=self.t("update_body", new=release["version"], cur=APP_VERSION),
            font=("Segoe UI", 12), text_color=C["text2"], justify=just,
        ).pack(pady=(0, 4))

        self.portable = not running_installed_copy()
        if self.portable:
            ctk.CTkLabel(self, text=self.t("update_portable"), font=("Segoe UI", 11),
                         text_color=C["muted"], justify=just).pack(pady=(6, 0))
        elif release.get("size"):
            ctk.CTkLabel(self, text=f"{release['size'] / (1024 * 1024):.1f} MB",
                         font=("Segoe UI", 11), text_color=C["muted"]).pack(pady=(2, 0))

        self.status = ctk.CTkLabel(self, text="", font=("Segoe UI", 11),
                                   text_color=C["muted"], anchor=anchor)
        self.status.pack(pady=(14, 4), padx=30, fill="x")

        self.progress = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                           progress_color=C["accent"],
                                           fg_color=C["border"])
        self.progress.set(0)
        self.progress.pack(padx=30, fill="x")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=20)

        self.later_btn = ctk.CTkButton(
            row, text=self.t("update_later"), width=110, height=38, corner_radius=10,
            font=("Segoe UI", 12), fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            command=self._close)
        self.later_btn.pack(side="left", padx=6)

        self.go_btn = ctk.CTkButton(
            row,
            text=self.t("open_releases") if self.portable else self.t("update_install"),
            width=170, height=38, corner_radius=10,
            font=("Segoe UI Semibold", 13), fg_color=C["accent"],
            hover_color=C["accent_l"], text_color="white", command=self._go)
        self.go_btn.pack(side="left", padx=6)

        if not self.portable and not release.get("url"):
            # release published without the installer asset — nothing to install
            self.go_btn.configure(text=self.t("open_releases"))
            self.portable = True

    def t(self, key, **kw):
        return tr(self.lang, key, **kw)

    def _close(self):
        if self._busy:
            return
        self._cancelled = True
        self.grab_release()
        self.destroy()

    def _go(self):
        if self.portable:
            webbrowser.open(f"{APP_GITHUB}/releases/latest")
            self._close()
            return
        self._busy = True
        self.go_btn.configure(state="disabled")
        self.later_btn.configure(state="disabled")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        dest = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")),
                            SETUP_ASSET_NAME)
        try:
            def progress(done, total):
                pct = int(done * 100 / total) if total else 0
                self.after(0, lambda: self._set_progress(pct))

            download_update(self.release["url"], dest, progress,
                            cancelled=lambda: self._cancelled)

            self.after(0, lambda: self.status.configure(
                text=self.t("update_launching"), text_color=C["success"]))
            self.after(600, lambda: self._launch(dest))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._failed(msg))

    def _set_progress(self, pct):
        self.progress.set(pct / 100)
        self.status.configure(text=self.t("update_downloading", pct=pct),
                              text_color=C["text2"])

    def _failed(self, msg):
        self._busy = False
        self.progress.set(0)
        self.status.configure(text=self.t("update_failed", err=msg), text_color=C["danger"])
        self.go_btn.configure(state="normal")
        self.later_btn.configure(state="normal")

    def _launch(self, setup_path):
        try:
            # the installer stops this app, swaps the exe, and starts it again
            subprocess.Popen([setup_path, "--silent", "--launch"],
                             creationflags=0x08000000)
        except Exception as e:
            self._failed(str(e))
            return
        self.grab_release()
        self.on_quit()


# ---------------------------------------------------------
# Main App
# ---------------------------------------------------------

class App(ctk.CTk):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.settings = load_settings()

        # keep the saved preference honest if the user changed it outside the app
        self.settings["start_with_windows"] = is_startup_enabled()

        self.lang = self.settings.get("language", "en")
        if self.lang not in TR:
            self.lang = "en"
        self._pending_release = None

        self.title(f"{APP_NAME}")
        self.geometry("380x730")
        self.resizable(False, False)

        ico = app_icon_path()
        if ico:
            try:
                self.iconbitmap(ico)
            except Exception:
                pass

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
        self._counter_job = None

        self.create_widgets()
        self.floating_btn = FloatingButton(self, self._do_convert)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._start_mouse_listener()
        self._start_keyboard_listener()
        self._start_hotkey_listener()

        # أيقونة شريط المهام تعمل دائماً في الخلفية
        self._start_tray()

        # التشغيل مع بدء ويندوز: ابدأ مصغّراً في شريط المهام
        if start_minimized:
            self.after(0, self.withdraw)
        elif self.settings.get("first_run", True):
            # رسالة الترحيب أول مرة
            self.after(500, self._show_welcome)

        # فحص التحديثات عند التشغيل
        if self.settings.get("check_updates", True):
            threading.Thread(target=self._silent_update_check, daemon=True).start()

    # ── Language ──

    def t(self, key, **kw):
        return tr(self.lang, key, **kw)

    @property
    def rtl(self):
        return is_rtl(self.lang)

    def _anchor(self):
        return "e" if self.rtl else "w"

    def _lead(self):
        """Side that reads first in the current direction."""
        return "right" if self.rtl else "left"

    def _trail(self):
        return "left" if self.rtl else "right"

    def _toggle_language(self):
        self.lang = "ar" if self.lang == "en" else "en"
        self.settings["language"] = self.lang
        save_settings(self.settings)
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Language changes flip layout direction, so rebuild rather than retitle."""
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkToplevel):
                continue
            child.destroy()
        self.create_widgets()
        self._update_floating_label()
        if self._pending_release:
            self._announce_update(self._pending_release)

    def _update_floating_label(self):
        try:
            self.floating_btn.btn.configure(text="ع⇄A")
        except Exception:
            pass

    # ── Welcome / Updates ──

    def _show_welcome(self):
        WelcomeDialog(self, self.lang)
        self.settings["first_run"] = False
        save_settings(self.settings)

    def _silent_update_check(self):
        """Background check on launch. Only ever reads — never downloads by itself."""
        time.sleep(3)
        release = fetch_latest_release()
        if not release or not is_newer(release["version"], APP_VERSION):
            return
        self._pending_release = release
        self.after(0, lambda: self._announce_update(release))

    def _announce_update(self, release):
        try:
            self.status_label.configure(
                text=self.t("update_available", v=release["version"]),
                text_color=C["warning"],
            )
        except Exception:
            pass

    def _open_update_dialog(self, release=None):
        release = release or self._pending_release
        if not release:
            return
        UpdateDialog(self, release, self.lang, self._cleanup)

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

        # Language + About buttons
        self._globe_img = ctk.CTkImage(
            light_image=make_globe_image(40, C["muted"]),
            dark_image=make_globe_image(40, C["muted"]),
            size=(17, 17),
        )
        ctk.CTkButton(
            title_row, text="", image=self._globe_img,
            width=28, height=28, corner_radius=14,
            fg_color=C["border"], hover_color=C["card_hover"],
            command=self._toggle_language,
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            title_row, text="?", width=28, height=28, corner_radius=14,
            font=("Segoe UI", 13, "bold"),
            fg_color=C["border"], hover_color=C["card_hover"],
            text_color=C["muted"], command=self._show_about
        ).pack(side="right", padx=(6, 0))

        hotkey_display = self.settings.get("hotkey", "ctrl+shift+f9").upper().replace("+", " + ")
        self.status_label = ctk.CTkLabel(
            header,
            text=self.t("tagline", hk=hotkey_display),
            text_color=C["accent_l"], font=("Segoe UI", 11)
        )
        self.status_label.pack(pady=(6, 0))
        self.status_label.bind("<Button-1>", lambda e: self._open_update_dialog())

        # Counter
        self.counter_label = ctk.CTkLabel(
            self, text=self.t("conversions_many", n=0),
            font=("Segoe UI", 11), text_color=C["muted"]
        )
        self.counter_label.pack(pady=(8, 0))
        self._update_counter()

        # ── Options Card ──
        opts_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        opts_card.pack(pady=(8, 0), padx=16, fill="x")
        opts = ctk.CTkFrame(opts_card, fg_color="transparent")
        opts.pack(padx=16, pady=12, fill="x")

        self.switch_var = ctk.BooleanVar(value=self.is_active)
        self._switch_row(opts, self.t("enable"), self.switch_var, self._toggle_active)
        self._divider(opts)

        self.floating_var = ctk.BooleanVar(value=self.settings.get("show_floating_button", True))
        self._switch_row(opts, self.t("floating_button"), self.floating_var, self._toggle_floating)
        self._divider(opts)

        self.topmost_var = ctk.BooleanVar(value=self.settings.get("always_on_top", True))
        self._switch_row(opts, self.t("always_on_top"), self.topmost_var, self._toggle_topmost)
        self._divider(opts)

        self.sound_var = ctk.BooleanVar(value=self.settings.get("sound_enabled", True))
        self._switch_row(opts, self.t("sound_feedback"), self.sound_var, self._toggle_sound)
        self._divider(opts)

        self.startup_var = ctk.BooleanVar(value=self.settings.get("start_with_windows", False))
        self._switch_row(opts, self.t("start_with_windows"), self.startup_var, self._toggle_startup)

        # ── Mode Card ──
        mode_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        mode_card.pack(pady=(8, 0), padx=16, fill="x")
        mode = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode.pack(padx=16, pady=12, fill="x")

        ctk.CTkLabel(mode, text=self.t("conversion_mode"), font=("Segoe UI Semibold", 13),
                     text_color=C["text"]).pack(anchor=self._anchor(), pady=(0, 6))

        self.direction_var = ctk.StringVar(value=self.settings.get("direction", "auto"))
        for key, val in [("auto_detect", "auto"), ("ar_to_en", "ar_to_en"), ("en_to_ar", "en_to_ar")]:
            ctk.CTkRadioButton(
                mode, text=self.t(key), variable=self.direction_var, value=val,
                command=self._change_dir, font=("Segoe UI", 12),
                text_color=C["text2"], fg_color=C["accent"],
                hover_color=C["accent_l"], border_color=C["border"],
            ).pack(pady=2, anchor=self._anchor(), padx=4)

        # ── Hotkey Card ──
        hk_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=14)
        hk_card.pack(pady=(8, 0), padx=16, fill="x")
        hk = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk.pack(padx=16, pady=12, fill="x")

        hk_top = ctk.CTkFrame(hk, fg_color="transparent")
        hk_top.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(hk_top, text=self.t("keyboard_shortcut"), font=("Segoe UI Semibold", 13),
                     text_color=C["text"]).pack(side=self._lead())
        self.hotkey_hint = ctk.CTkLabel(hk_top, text=self.t("click_to_record"),
                                        font=("Segoe UI", 10), text_color=C["muted"])
        self.hotkey_hint.pack(side=self._trail())

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
            bf, text=self.t("hide_to_tray"), width=155, height=36, corner_radius=10,
            font=("Segoe UI", 12), fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            command=self.hide_window
        ).pack(side=self._lead(), padx=(0, 6) if not self.rtl else (6, 0))

        ctk.CTkButton(
            bf, text=self.t("exit"), width=100, height=36, corner_radius=10,
            font=("Segoe UI", 12), fg_color=C["danger"], hover_color=C["danger_h"],
            text_color="white", command=self._full_quit
        ).pack(side=self._trail())

        # ── Footer ──
        # One label per script run, packed in reading order. Tk transposes mixed
        # Arabic/Latin text inside a single label, so we place the runs ourselves.
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(pady=(2, 8))
        parts = TR.get(self.lang, TR["en"]).get("footer_parts", TR["en"]["footer_parts"])
        for part in parts:
            ctk.CTkLabel(
                footer, text=part.format(v=APP_VERSION),
                font=("Segoe UI", 10), text_color=C["muted"]
            ).pack(side=self._lead(), padx=3)

    def _switch_row(self, parent, text, var, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text=text, font=("Segoe UI", 12),
                     text_color=C["text2"]).pack(side=self._lead())
        ctk.CTkSwitch(
            row, text="", command=cmd, variable=var, width=44,
            progress_color=C["accent"], button_color="white",
            button_hover_color="#E2E8F0", fg_color=C["border"],
        ).pack(side=self._trail())

    def _divider(self, parent):
        ctk.CTkFrame(parent, fg_color=C["border"], height=1).pack(fill="x", pady=7)

    def _show_about(self):
        AboutDialog(self, self.settings, self.lang, self._open_update_dialog)

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

    def _floating_enabled(self):
        return self.settings.get("show_floating_button", True)

    def _check_and_show(self, x, y):
        if not self.is_active or self.processing or not self._floating_enabled():
            # bailing out here also skips the clipboard probe below, so with the
            # button off nothing touches the clipboard until you press the hotkey
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
        self.hotkey_entry.insert(0, self.t("press_keys"))
        self.hotkey_entry.configure(border_color=C["accent"], text_color=C["warning"])
        self.hotkey_hint.configure(text=self.t("press_shortcut"), text_color=C["warning"])

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
        self.hotkey_hint.configure(text=self.t("saved"), text_color=C["success"])
        self.after(2000, lambda: self.hotkey_hint.configure(
            text=self.t("click_to_record"), text_color=C["muted"]))

        self.status_label.configure(text=self.t("tagline", hk=display))
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

    def _show_button_at_cursor(self):
        if self.is_active and not self.processing and self._floating_enabled():
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
        self._reset_status()
        if not self.is_active:
            self.floating_btn.hide()

    def _toggle_topmost(self):
        v = self.topmost_var.get()
        self.attributes("-topmost", v)
        self.settings["always_on_top"] = v
        save_settings(self.settings)

    def _toggle_sound(self):
        self.settings["sound_enabled"] = self.sound_var.get()
        save_settings(self.settings)

    def _toggle_floating(self):
        v = self.floating_var.get()
        self.settings["show_floating_button"] = v
        save_settings(self.settings)
        if not v:
            self.floating_btn.hide()
        self.status_label.configure(
            text=self.t("floating_on") if v else self.t("floating_off"),
            text_color=C["accent_l"] if v else C["muted"],
        )
        self.after(2500, self._reset_status)

    def _toggle_startup(self):
        want = self.startup_var.get()
        if set_startup_enabled(want):
            self.settings["start_with_windows"] = want
            save_settings(self.settings)
            self.status_label.configure(
                text=self.t("startup_on") if want else self.t("startup_off"),
                text_color=C["success"] if want else C["muted"],
            )
            self.after(2500, self._reset_status)
        else:
            self.startup_var.set(not want)
            self.status_label.configure(text=self.t("startup_failed"), text_color=C["danger"])
            self.after(2500, self._reset_status)

    def _reset_status(self):
        # an available update outranks the idle tagline
        if self._pending_release:
            self._announce_update(self._pending_release)
            return
        hk = self.settings.get("hotkey", "ctrl+shift+f9").upper().replace("+", " + ")
        if self.is_active:
            self.status_label.configure(text=self.t("tagline", hk=hk), text_color=C["accent_l"])
        else:
            self.status_label.configure(text=self.t("paused"), text_color=C["danger"])

    def _change_dir(self):
        self.settings["direction"] = self.direction_var.get()
        save_settings(self.settings)

    def _update_counter(self):
        # create_widgets() calls this again after a language rebuild, so drop any
        # tick already queued — otherwise every switch leaves an extra loop running
        if self._counter_job is not None:
            try:
                self.after_cancel(self._counter_job)
            except Exception:
                pass
            self._counter_job = None
        n = self.conversion_count
        key = "conversions_one" if n == 1 else "conversions_many"
        try:
            self.counter_label.configure(text=self.t(key, n=n))
        except Exception:
            return
        self._counter_job = self.after(1000, self._update_counter)

    # ── System Tray ──

    def _make_tray_img(self):
        """Prefer the bundled multi-size icon so the tray stays crisp on HiDPI."""
        ico = app_icon_path()
        if ico:
            try:
                img = Image.open(ico)
                img.load()
                return img.convert("RGBA")
            except Exception:
                pass
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((2, 2, 62, 62), radius=14, fill=C["accent"])
        d.text((10, 18), "ع/A", fill="white")
        return img

    def _start_tray(self):
        """The tray icon lives for the whole session, so the app is always reachable."""
        if self.tray_icon:
            return
        # labels are callables so the menu follows the interface language
        menu = pystray.Menu(
            pystray.MenuItem(lambda item: self.t("tray_show"),
                             self._show_from_tray, default=True),
            pystray.MenuItem(lambda item: self.t("tray_enabled"), self._tray_toggle_active,
                             checked=lambda item: self.is_active),
            pystray.MenuItem(lambda item: self.t("start_with_windows"),
                             self._tray_toggle_startup,
                             checked=lambda item: self.settings.get("start_with_windows", False)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self.t("tray_exit"), self._quit_from_tray),
        )
        self.tray_icon = pystray.Icon("LangFixer", self._make_tray_img(), APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        """Close button and 'Hide to Tray' both park the app in the system tray."""
        self.withdraw()
        self._start_tray()

    def _show_from_tray(self, icon=None, item=None):
        self.after(0, self._restore_window)

    def _restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_toggle_active(self, icon=None, item=None):
        self.after(0, self._tray_toggle_active_ui)

    def _tray_toggle_active_ui(self):
        self.switch_var.set(not self.switch_var.get())
        self._toggle_active()
        if self.tray_icon:
            self.tray_icon.update_menu()

    def _tray_toggle_startup(self, icon=None, item=None):
        self.after(0, self._tray_toggle_startup_ui)

    def _tray_toggle_startup_ui(self):
        self.startup_var.set(not self.startup_var.get())
        self._toggle_startup()
        if self.tray_icon:
            self.tray_icon.update_menu()

    def _quit_from_tray(self, icon=None, item=None):
        # marshal back to the Tk thread — destroying widgets off-thread deadlocks
        self.after(0, self._cleanup)

    def _full_quit(self):
        self._cleanup()

    def _cleanup(self):
        save_settings(self.settings)
        self.floating_btn.hide()
        if self.tray_icon:
            try: self.tray_icon.stop()
            except: pass
            self.tray_icon = None
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    start_minimized = any(a in ("--minimized", "--startup", "/minimized")
                          for a in sys.argv[1:])

    set_app_user_model_id()

    if already_running():
        # a second copy would fight over the hotkey and the clipboard
        if not activate_existing_instance():
            try:
                user32.MessageBoxW(
                    None,
                    f"{APP_NAME} is already running.\nLook for it in the system tray.",
                    APP_NAME, 0x40,
                )
            except Exception:
                pass
        sys.exit(0)

    try:
        app = App(start_minimized=start_minimized)
        app.mainloop()
    except SystemExit:
        raise
    except Exception as exc:
        # windowed build: without this the user gets PyInstaller's raw traceback box
        import traceback
        try:
            user32.MessageBoxW(
                None,
                f"{APP_NAME} could not start.\n\n{type(exc).__name__}: {exc}\n\n"
                + traceback.format_exc(limit=3),
                APP_NAME, 0x10,
            )
        except Exception:
            pass
        sys.exit(1)