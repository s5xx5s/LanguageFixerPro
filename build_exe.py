"""
Build Script - Language Fixer Pro
==================================
pip install pyinstaller
python build_exe.py
"""

import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    print("[1/3] Creating icon...")
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        m = max(1, size // 16)
        d.rounded_rectangle((m, m, size-m, size-m), radius=size//4, fill="#1A6FD4")
        try:
            font = ImageFont.truetype("segoeui.ttf", size // 3)
        except:
            font = ImageFont.load_default()
        text = "ع A"
        bbox = d.textbbox((0,0), text, font=font)
        d.text(((size-bbox[2]+bbox[0])//2, (size-bbox[3]+bbox[1])//2), text, fill="white", font=font)
        images.append(img)
    path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
    images[0].save(path, format='ICO', sizes=[(s,s) for s in sizes], append_images=images[1:])
    return path

def build(icon):
    print("[2/3] Building EXE...")
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    main = os.path.join(os.path.dirname(__file__), "main.py")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--noconfirm",
        f"--icon={icon}", "--name=LanguageFixerPro",
        f"--add-data={ctk_path};customtkinter",
        "--hidden-import=pynput", "--hidden-import=pynput.mouse",
        "--hidden-import=pynput.mouse._win32",
        "--hidden-import=pynput.keyboard", "--hidden-import=pynput.keyboard._win32",
        "--hidden-import=pyperclip", "--hidden-import=pystray",
        "--hidden-import=pystray._win32", "--hidden-import=PIL",
        "--hidden-import=ctypes", "--hidden-import=winsound",
        main,
    ]
    subprocess.run(cmd)

def cleanup():
    print("[3/3] Cleaning up...")
    import shutil
    for f in ["build", "__pycache__"]:
        if os.path.exists(f): shutil.rmtree(f, ignore_errors=True)
    if os.path.exists("LanguageFixerPro.spec"): os.remove("LanguageFixerPro.spec")

if __name__ == "__main__":
    print("=" * 45)
    print("  Language Fixer Pro - EXE Builder")
    print("=" * 45)
    try:
        import PyInstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    icon = create_icon()
    build(icon)
    cleanup()
    exe = os.path.join("dist", "LanguageFixerPro.exe")
    if os.path.exists(exe):
        mb = os.path.getsize(exe) / (1024*1024)
        print(f"\n  SUCCESS! → dist/LanguageFixerPro.exe ({mb:.1f} MB)")
    else:
        print("\n  ERROR: Check output above.")