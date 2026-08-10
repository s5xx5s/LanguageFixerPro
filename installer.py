"""
Installer - Language Fixer Pro
==============================
Builds into LanguageFixerPro-Setup.exe. The same binary is copied into the
install folder as uninstall.exe and handles removal when run from there.

Per-user install under %LOCALAPPDATA%\\Programs — no admin rights, no UAC prompt.
"""

import customtkinter as ctk
import ctypes
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import winreg

APP_NAME = "Language Fixer Pro"
APP_VERSION = "1.5.0"
APP_PUBLISHER = "s5xx5s"
APP_GITHUB = "https://github.com/s5xx5s/LanguageFixerPro"
EXE_NAME = "LanguageFixerPro.exe"
UNINST_NAME = "uninstall.exe"
REG_APP_KEY = "LanguageFixerPro"

UNINSTALL_REG_PATH = "\\".join(
    [r"Software\Microsoft\Windows\CurrentVersion\Uninstall", REG_APP_KEY])
STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_REG_NAME = "LanguageFixerPro"

NO_WINDOW = 0x08000000

C = {
    "bg": "#0F1117", "card": "#1A1D27", "card_hover": "#222636",
    "accent": "#1A6FD4", "accent_l": "#2B88ED",
    "success": "#22C55E", "danger": "#EF4444", "danger_h": "#DC2626",
    "text": "#F1F5F9", "text2": "#94A3B8", "muted": "#64748B", "border": "#2A2E3B",
}


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def default_install_dir():
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local, "Programs", "LanguageFixerPro")


def start_menu_dir():
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")


def desktop_dir():
    return os.path.join(os.path.expanduser("~"), "Desktop")


def payload_exe():
    """The app binary bundled inside this installer."""
    return resource_path(os.path.join("payload", EXE_NAME))


# ---------------------------------------------------------
# Windows integration helpers
# ---------------------------------------------------------

def run_hidden(args):
    return subprocess.run(args, creationflags=NO_WINDOW,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_shortcut(link_path, target, icon=None, args="", workdir=None):
    """WScript.Shell via PowerShell keeps this dependency-free (no pywin32)."""
    ps = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}');"
        "$s.TargetPath = '{target}';"
        "$s.Arguments = '{args}';"
        "$s.WorkingDirectory = '{wd}';"
        "$s.IconLocation = '{icon}';"
        "$s.Description = '{desc}';"
        "$s.Save()"
    ).format(
        link=link_path.replace("'", "''"),
        target=target.replace("'", "''"),
        args=args.replace("'", "''"),
        wd=(workdir or os.path.dirname(target)).replace("'", "''"),
        icon=(icon or target).replace("'", "''"),
        desc=APP_NAME,
    )
    run_hidden(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps])
    return os.path.exists(link_path)


def set_startup(enabled, exe_path):
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH) as key:
            if enabled:
                winreg.SetValueEx(key, STARTUP_REG_NAME, 0, winreg.REG_SZ,
                                  f'"{exe_path}" --minimized')
            else:
                try:
                    winreg.DeleteValue(key, STARTUP_REG_NAME)
                except FileNotFoundError:
                    pass
    except Exception:
        pass


def register_uninstall(install_dir):
    """Puts the app in Settings > Apps > Installed apps."""
    exe = os.path.join(install_dir, EXE_NAME)
    size_kb = 0
    for root, _, files in os.walk(install_dir):
        for f in files:
            try:
                size_kb += os.path.getsize(os.path.join(root, f)) // 1024
            except OSError:
                pass
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_PATH) as key:
            values = {
                "DisplayName": APP_NAME,
                "DisplayVersion": APP_VERSION,
                "Publisher": APP_PUBLISHER,
                "DisplayIcon": exe,
                "InstallLocation": install_dir,
                "UninstallString": f'"{os.path.join(install_dir, UNINST_NAME)}"',
                "URLInfoAbout": APP_GITHUB,
            }
            for k, v in values.items():
                winreg.SetValueEx(key, k, 0, winreg.REG_SZ, v)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
    except Exception:
        pass


def unregister_uninstall():
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_PATH)
    except Exception:
        pass


def app_is_running():
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {EXE_NAME}", "/NH"],
                             capture_output=True, text=True, creationflags=NO_WINDOW)
        return EXE_NAME.lower() in (out.stdout or "").lower()
    except Exception:
        return False


def stop_running_app(timeout=10.0):
    """taskkill returns before Windows releases the exe lock — wait for the real exit."""
    run_hidden(["taskkill", "/F", "/IM", EXE_NAME])
    deadline = time.time() + timeout
    while time.time() < deadline and app_is_running():
        time.sleep(0.25)


def copy_with_retry(src, dst, attempts=12, delay=0.4):
    """Even after the process is gone the file can stay locked for a moment
    (antivirus scan, lazy handle release). Retry instead of failing the install."""
    last = None
    for _ in range(attempts):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as e:
            last = e
            time.sleep(delay)
    raise last


def installed_dir_from_registry():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_PATH) as key:
            return winreg.QueryValueEx(key, "InstallLocation")[0]
    except Exception:
        return None


# ---------------------------------------------------------
# Shared UI bits
# ---------------------------------------------------------

class BaseWindow(ctk.CTk):
    def __init__(self, title, height):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.title(title)
        self.geometry(f"520x{height}")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        ico = resource_path("app_icon.ico")
        if os.path.exists(ico):
            try:
                self.iconbitmap(ico)
            except Exception:
                pass
        self._center(520, height)
        self.after(120, self._bring_to_front)

    def _bring_to_front(self):
        """Setup windows are easy to lose behind a maximised app — flash to front once."""
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force()
            self.after(600, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _center(self, w, h):
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"{w}x{h}+{x}+{y}")

    def header(self, subtitle):
        head = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=92)
        head.pack(fill="x")
        head.pack_propagate(False)
        row = ctk.CTkFrame(head, fg_color="transparent")
        row.pack(expand=True)
        ctk.CTkLabel(row, text="  ع A  ", font=("Segoe UI", 13, "bold"),
                     fg_color=C["accent"], corner_radius=8,
                     text_color="white").pack(side="left", padx=(0, 12))
        col = ctk.CTkFrame(row, fg_color="transparent")
        col.pack(side="left")
        ctk.CTkLabel(col, text=APP_NAME, font=("Segoe UI Semibold", 20),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(col, text=subtitle, font=("Segoe UI", 11),
                     text_color=C["muted"]).pack(anchor="w")


# ---------------------------------------------------------
# Installer
# ---------------------------------------------------------

class Installer(BaseWindow):
    def __init__(self):
        super().__init__(f"{APP_NAME} Setup", 560)
        self.install_dir = ctk.StringVar(value=default_install_dir())
        self.opt_startup = ctk.BooleanVar(value=True)
        self.opt_desktop = ctk.BooleanVar(value=True)
        self.opt_startmenu = ctk.BooleanVar(value=True)
        self.opt_launch = ctk.BooleanVar(value=True)
        self.busy = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _build(self):
        self.header(f"Version {APP_VERSION}  ·  Setup")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=(16, 0))

        ctk.CTkLabel(body, text="Install location", font=("Segoe UI Semibold", 13),
                     text_color=C["text"]).pack(anchor="w")

        loc = ctk.CTkFrame(body, fg_color="transparent")
        loc.pack(fill="x", pady=(6, 14))
        self.loc_entry = ctk.CTkEntry(loc, textvariable=self.install_dir, height=36,
                                      font=("Segoe UI", 11), fg_color=C["card"],
                                      border_color=C["border"], corner_radius=10,
                                      text_color=C["text2"])
        self.loc_entry.pack(side="left", fill="x", expand=True)
        self.browse_btn = ctk.CTkButton(loc, text="Browse", width=84, height=36,
                                        corner_radius=10, font=("Segoe UI", 11),
                                        fg_color=C["card"], hover_color=C["card_hover"],
                                        text_color=C["text2"], border_width=1,
                                        border_color=C["border"], command=self._browse)
        self.browse_btn.pack(side="left", padx=(8, 0))

        card = ctk.CTkFrame(body, fg_color=C["card"], corner_radius=14)
        card.pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner, text="Options", font=("Segoe UI Semibold", 13),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 8))

        self.checks = []
        for text, var in [
            ("Start with Windows (minimized to tray)", self.opt_startup),
            ("Create a Desktop shortcut", self.opt_desktop),
            ("Create a Start Menu shortcut", self.opt_startmenu),
            ("Run Language Fixer Pro after install", self.opt_launch),
        ]:
            cb = ctk.CTkCheckBox(inner, text=text, variable=var, font=("Segoe UI", 12),
                                 text_color=C["text2"], fg_color=C["accent"],
                                 hover_color=C["accent_l"], border_color=C["border"],
                                 checkbox_width=20, checkbox_height=20, corner_radius=6)
            cb.pack(anchor="w", pady=4)
            self.checks.append(cb)

        self.status = ctk.CTkLabel(body, text="Ready to install.", font=("Segoe UI", 11),
                                   text_color=C["muted"])
        self.status.pack(anchor="w", pady=(14, 4))

        self.progress = ctk.CTkProgressBar(body, height=6, corner_radius=3,
                                           progress_color=C["accent"], fg_color=C["border"])
        self.progress.set(0)
        self.progress.pack(fill="x")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=22, pady=16)
        ctk.CTkLabel(footer, text="MIT License  ·  Open Source", font=("Segoe UI", 10),
                     text_color=C["muted"]).pack(side="left")
        self.cancel_btn = ctk.CTkButton(footer, text="Cancel", width=92, height=38,
                                        corner_radius=10, font=("Segoe UI", 12),
                                        fg_color=C["card"], hover_color=C["card_hover"],
                                        text_color=C["text2"], border_width=1,
                                        border_color=C["border"], command=self._on_close)
        self.cancel_btn.pack(side="right", padx=(8, 0))
        self.install_btn = ctk.CTkButton(footer, text="Install", width=128, height=38,
                                         corner_radius=10, font=("Segoe UI Semibold", 13),
                                         fg_color=C["accent"], hover_color=C["accent_l"],
                                         text_color="white", command=self._start)
        self.install_btn.pack(side="right")

    def _browse(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Choose install folder")
        if path:
            self.install_dir.set(os.path.join(path, "LanguageFixerPro")
                                 if os.path.basename(path) != "LanguageFixerPro" else path)

    def _on_close(self):
        if not self.busy:
            self.destroy()

    def _set_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for w in [self.install_btn, self.browse_btn, self.loc_entry, *self.checks]:
            w.configure(state=state)

    def _report(self, text, value, color=None):
        self.after(0, lambda: (self.status.configure(text=text, text_color=color or C["text2"]),
                               self.progress.set(value)))

    def _start(self):
        self.busy = True
        self._set_enabled(False)
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        target = self.install_dir.get().strip()
        try:
            src = payload_exe()
            if not os.path.exists(src):
                raise FileNotFoundError("Bundled application binary is missing.")

            self._report("Closing any running copy...", 0.1)
            stop_running_app()

            self._report("Creating install folder...", 0.25)
            os.makedirs(target, exist_ok=True)

            self._report("Copying application files...", 0.45)
            copy_with_retry(src, os.path.join(target, EXE_NAME))
            if getattr(sys, "frozen", False):
                # this same binary doubles as the uninstaller
                copy_with_retry(sys.executable, os.path.join(target, UNINST_NAME))

            exe_path = os.path.join(target, EXE_NAME)

            self._report("Creating shortcuts...", 0.65)
            if self.opt_startmenu.get():
                create_shortcut(os.path.join(start_menu_dir(), f"{APP_NAME}.lnk"), exe_path)
            if self.opt_desktop.get():
                create_shortcut(os.path.join(desktop_dir(), f"{APP_NAME}.lnk"), exe_path)

            self._report("Applying settings...", 0.82)
            set_startup(self.opt_startup.get(), exe_path)

            self._report("Registering application...", 0.94)
            register_uninstall(target)

            self._report("Installation complete.", 1.0, C["success"])
            self.after(0, lambda: self._finish(exe_path))
        except Exception as e:
            msg = str(e)
            self._report(f"Failed: {msg}", 0, C["danger"])
            self.busy = False
            self.after(0, lambda: self._set_enabled(True))

    def _finish(self, exe_path):
        self.busy = False
        self.install_btn.configure(text="Finish", state="normal",
                                   command=lambda: self._close_and_launch(exe_path))
        self.cancel_btn.configure(state="disabled")
        if self.opt_launch.get():
            # let the success state land before the window disappears
            self.after(1200, lambda: self._close_and_launch(exe_path))

    def _close_and_launch(self, exe_path):
        if self.opt_launch.get():
            try:
                subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path),
                                 creationflags=NO_WINDOW)
            except Exception:
                pass
        self.destroy()


# ---------------------------------------------------------
# Uninstaller
# ---------------------------------------------------------

class Uninstaller(BaseWindow):
    def __init__(self, install_dir):
        super().__init__(f"{APP_NAME} Uninstall", 330)
        self.install_dir = install_dir
        self.busy = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _build(self):
        self.header(f"Version {APP_VERSION}  ·  Uninstall")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=(18, 0))

        ctk.CTkLabel(body, text="Remove Language Fixer Pro from this computer?",
                     font=("Segoe UI Semibold", 13), text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(body, text=self.install_dir, font=("Segoe UI", 10),
                     text_color=C["muted"], wraplength=460,
                     justify="left").pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(body,
                     text="Shortcuts and the startup entry will also be removed.\n"
                          "Your settings file (~/.langfixer_pro.json) is kept.",
                     font=("Segoe UI", 11), text_color=C["text2"],
                     justify="left").pack(anchor="w", pady=(10, 0))

        self.status = ctk.CTkLabel(body, text="", font=("Segoe UI", 11),
                                   text_color=C["muted"])
        self.status.pack(anchor="w", pady=(14, 0))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=22, pady=16)
        self.cancel_btn = ctk.CTkButton(footer, text="Cancel", width=92, height=38,
                                        corner_radius=10, font=("Segoe UI", 12),
                                        fg_color=C["card"], hover_color=C["card_hover"],
                                        text_color=C["text2"], border_width=1,
                                        border_color=C["border"], command=self._on_close)
        self.cancel_btn.pack(side="right", padx=(8, 0))
        self.remove_btn = ctk.CTkButton(footer, text="Uninstall", width=128, height=38,
                                        corner_radius=10, font=("Segoe UI Semibold", 13),
                                        fg_color=C["danger"], hover_color=C["danger_h"],
                                        text_color="white", command=self._start)
        self.remove_btn.pack(side="right")

    def _on_close(self):
        if not self.busy:
            self.destroy()

    def _start(self):
        self.busy = True
        self.remove_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.status.configure(text="Removing...", text_color=C["text2"])
        self.after(100, self._uninstall)

    def _uninstall(self):
        stop_running_app()
        set_startup(False, "")
        for link in [os.path.join(start_menu_dir(), f"{APP_NAME}.lnk"),
                     os.path.join(desktop_dir(), f"{APP_NAME}.lnk")]:
            try:
                os.remove(link)
            except OSError:
                pass
        unregister_uninstall()

        # remove everything except this still-running binary, then let a detached
        # shell delete the folder once we have exited
        for root, dirs, files in os.walk(self.install_dir):
            for f in files:
                p = os.path.join(root, f)
                if os.path.normcase(p) == os.path.normcase(sys.executable):
                    continue
                try:
                    os.remove(p)
                except OSError:
                    pass

        subprocess.Popen(
            f'ping 127.0.0.1 -n 3 >nul & rmdir /s /q "{self.install_dir}"',
            shell=True, creationflags=NO_WINDOW,
        )
        self.status.configure(text="Uninstalled.", text_color=C["success"])
        self.after(700, self.destroy)


# ---------------------------------------------------------

def silent_install(target=None, launch=False):
    """Unattended install with the default options. Returns an exit code."""
    target = target or default_install_dir()
    src = payload_exe()
    if not os.path.exists(src):
        print("ERROR: bundled application binary is missing.")
        return 1
    stop_running_app()
    os.makedirs(target, exist_ok=True)
    exe_path = os.path.join(target, EXE_NAME)
    try:
        copy_with_retry(src, exe_path)
        if getattr(sys, "frozen", False):
            copy_with_retry(sys.executable, os.path.join(target, UNINST_NAME))
    except OSError as e:
        print(f"ERROR: could not write to {target}: {e}")
        return 1
    create_shortcut(os.path.join(start_menu_dir(), f"{APP_NAME}.lnk"), exe_path)
    create_shortcut(os.path.join(desktop_dir(), f"{APP_NAME}.lnk"), exe_path)
    set_startup(True, exe_path)
    register_uninstall(target)
    if launch:
        subprocess.Popen([exe_path], cwd=target, creationflags=NO_WINDOW)
    print(f"Installed to {target}")
    return 0


def silent_uninstall(target=None):
    target = target or installed_dir_from_registry()
    if not target:
        print("ERROR: no installation found.")
        return 1
    stop_running_app()
    set_startup(False, "")
    for link in [os.path.join(start_menu_dir(), f"{APP_NAME}.lnk"),
                 os.path.join(desktop_dir(), f"{APP_NAME}.lnk")]:
        try:
            os.remove(link)
        except OSError:
            pass
    unregister_uninstall()
    for root, _, files in os.walk(target):
        for f in files:
            p = os.path.join(root, f)
            if os.path.normcase(p) == os.path.normcase(sys.executable):
                continue
            try:
                os.remove(p)
            except OSError:
                pass
    subprocess.Popen(f'ping 127.0.0.1 -n 3 >nul & rmdir /s /q "{target}"',
                     shell=True, creationflags=NO_WINDOW)
    print(f"Uninstalled from {target}")
    return 0


def main():
    args = [a.lower() for a in sys.argv[1:]]
    self_name = os.path.basename(sys.executable if getattr(sys, "frozen", False)
                                 else sys.argv[0]).lower()
    uninstall_mode = "--uninstall" in args or "/uninstall" in args or \
                     self_name.startswith("uninstall")
    silent = "--silent" in args or "/silent" in args or "/s" in args

    if uninstall_mode:
        if silent:
            sys.exit(silent_uninstall())
        install_dir = installed_dir_from_registry() or os.path.dirname(
            os.path.abspath(sys.executable))
        Uninstaller(install_dir).mainloop()
    else:
        if silent:
            sys.exit(silent_install(launch="--launch" in args))
        Installer().mainloop()


def fatal(message):
    """A windowed build has no console, so an uncaught error would otherwise show
    PyInstaller's raw traceback dialog. Say something a person can act on."""
    try:
        ctypes.windll.user32.MessageBoxW(None, message, f"{APP_NAME} Setup", 0x10)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        fatal(
            f"Setup could not finish.\n\n{type(exc).__name__}: {exc}\n\n"
            "If Language Fixer Pro is running, close it from the system tray "
            "and try again.\n\n" + traceback.format_exc(limit=3)
        )
        sys.exit(1)
