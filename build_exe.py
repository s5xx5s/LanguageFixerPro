"""
Build Script - Language Fixer Pro
==================================
    pip install -r requirements.txt pyinstaller
    python build_exe.py

Produces in dist/:
    LanguageFixerPro.exe        portable app
    LanguageFixerPro-Setup.exe  installer (bundles the app + uninstaller)

Flags:
    --app-only    build just the portable app
    --no-inno     skip the Inno Setup build even if ISCC is on PATH
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")
APP_EXE = os.path.join(DIST, "LanguageFixerPro.exe")
SETUP_EXE = os.path.join(DIST, "LanguageFixerPro-Setup.exe")

INNO_CANDIDATES = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("  installing pyinstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def ctk_data_arg():
    """customtkinter ships .json themes and fonts PyInstaller does not auto-collect."""
    import customtkinter
    return f"--add-data={os.path.dirname(customtkinter.__file__)};customtkinter"


HIDDEN_IMPORTS = [
    "pynput", "pynput.mouse", "pynput.mouse._win32",
    "pynput.keyboard", "pynput.keyboard._win32",
    "pyperclip", "pystray", "pystray._win32",
    "PIL", "PIL.Image", "PIL.ImageDraw",
]


def run_pyinstaller(name, entry, icon, extra=()):
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--noconfirm", "--clean",
        f"--icon={icon}", f"--name={name}",
        f"--distpath={DIST}", f"--workpath={BUILD}",
        f"--specpath={BUILD}",
        ctk_data_arg(),
        f"--add-data={icon};.",
    ]
    for h in HIDDEN_IMPORTS:
        cmd.append(f"--hidden-import={h}")
    cmd.extend(extra)
    cmd.append(entry)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"  ERROR: PyInstaller failed for {name}.")


def build_app(icon):
    print("[2/4] Building portable app...")
    run_pyinstaller("LanguageFixerPro", os.path.join(ROOT, "main.py"), icon)


def build_installer(icon):
    print("[3/4] Building installer...")
    if not os.path.exists(APP_EXE):
        raise SystemExit("  ERROR: dist/LanguageFixerPro.exe missing — build the app first.")
    # PyInstaller refuses to overwrite a file it is also bundling, so stage the
    # payload outside dist/
    payload_dir = os.path.join(BUILD, "payload")
    os.makedirs(payload_dir, exist_ok=True)
    staged = os.path.join(payload_dir, "LanguageFixerPro.exe")
    shutil.copy2(APP_EXE, staged)

    run_pyinstaller(
        "LanguageFixerPro-Setup", os.path.join(ROOT, "installer.py"), icon,
        extra=[f"--add-data={staged};payload"],
    )


def build_inno(icon):
    iscc = next((p for p in INNO_CANDIDATES if os.path.exists(p)), shutil.which("ISCC"))
    if not iscc:
        print("[4/4] Inno Setup not found — skipping (optional).")
        return
    print("[4/4] Building Inno Setup installer...")
    subprocess.run([iscc, os.path.join(ROOT, "installer.iss")], cwd=ROOT)


def cleanup():
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT, "__pycache__"), ignore_errors=True)


def report(path, label):
    if os.path.exists(path):
        mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  OK  {label:<28} {os.path.relpath(path, ROOT)}  ({mb:.1f} MB)")
        return True
    print(f"  --  {label:<28} not produced")
    return False


def main():
    args = sys.argv[1:]
    print("=" * 58)
    print("  Language Fixer Pro - Build")
    print("=" * 58)

    ensure_pyinstaller()

    print("[1/4] Creating icon...")
    from make_icon import create_icon
    icon = create_icon()

    build_app(icon)
    if "--app-only" not in args:
        build_installer(icon)
        if "--no-inno" not in args:
            build_inno(icon)

    cleanup()

    print("\n" + "-" * 58)
    ok = report(APP_EXE, "Portable app")
    if "--app-only" not in args:
        ok &= report(SETUP_EXE, "Installer")
        report(os.path.join(DIST, "LanguageFixerPro-Setup-Inno.exe"), "Installer (Inno)")
    print("-" * 58)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
