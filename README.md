# Language Fixer Pro ع⇄A


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue)](https://www.microsoft.com/windows)
[![Built With](https://img.shields.io/badge/Built%20With-Vibe%20Coding-purple)](https://github.com/s5xx5s)

> **Fix text typed in the wrong keyboard layout — instantly.**

Ever typed `hgsghl` when you meant **السلام**?  
Or `اثممخ` when you meant **hello**?

**Language Fixer Pro** solves this annoyance with a single click or hotkey. It seamlessly converts mistyped text between Arabic and English without needing to retype a single word.



## Features

- **Instant Conversion**: Fixes text in milliseconds.
- **Floating Button**: Appears automatically when you select text (Mouse or Keyboard).
- **Keyboard Centric**: Full support for Shift + Arrow selection.
- **Stealth Mode**: Turn the floating button off and drive everything from the hotkey — with it off, the app stops touching your clipboard on every selection.
- **Smart Detection**: Automatically detects if the text needs to be Arabic or English.
- **Interactive Feedback**: Subtle sound effects and visual cues.
- **Persistance**: Remembers your settings and window position.
- **Runs at Startup**: Launches with Windows, straight into the system tray.
- **Always in the Tray**: A permanent tray icon with a quick menu — show, enable/disable, toggle startup, exit.
- **Single Instance**: A second launch just points you at the copy already running.
- **Real Installer**: `LanguageFixerPro-Setup.exe` installs per-user (no admin prompt) and registers a proper uninstaller.

## Built with Vibe Coding

This project is a product of **Vibe Coding**.
We leveraged the flow state of AI-assisted development to bring this idea to life rapidly. It represents a modern approach to software engineering where intuition meets AI acceleration to solve real-world micro-frustrations efficiently.

## Installation

### Option 1: Installer (Recommended)
1. Go to the [Releases](../../releases) page.
2. Download `LanguageFixerPro-Setup.exe` and run it.
3. Pick your options and click **Install**.

It installs to `%LOCALAPPDATA%\Programs\LanguageFixerPro` — a per-user install, so
Windows never shows a UAC prompt. Setup can create Desktop and Start Menu shortcuts,
register the app to start with Windows, and launch it when it's done.

Uninstall from **Settings → Apps → Installed apps**, or run `uninstall.exe` from the
install folder.

For scripted deployment:

```bash
LanguageFixerPro-Setup.exe --silent
```

### Option 2: Portable EXE
Download `LanguageFixerPro.exe` from [Releases](../../releases) and run it directly —
nothing is installed, nothing is written to the registry unless you turn on
*Start with Windows* yourself.

### Option 3: Run from Source
If you are a developer or want to vibe with the code:

```bash
git clone https://github.com/s5xx5s/LanguageFixerPro.git
cd LanguageFixerPro
```

Use a virtual environment — on machines with several Python installs, a bare
`pip install` often lands in a *different* interpreter than the one `python` resolves
to, which is what produces `ModuleNotFoundError: No module named 'customtkinter'`
right after a successful install:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Always prefer `python -m pip` over a bare `pip` — it guarantees the packages land in
the interpreter you are about to run.

Start hidden in the tray (this is what the startup entry uses):

```bash
python main.py --minimized
```

## How to Use

### Floating Button Method
1. Select any mistyped text using your Mouse or Keyboard (Shift + Arrows).
2. A floating button "Fix Text" will appear near your cursor.
3. Click it to convert the text instantly.

### Shortcut Method
1. Select the text.
2. Press `Ctrl + Shift + F9` (Customizable in settings).
3. The text will be converted immediately.

> **Note:** Turn **Floating Button** off in settings if you prefer working from the
> hotkey alone. Detecting a selection for the button requires a quick clipboard read,
> so switching it off also stops the app from reading your clipboard on every
> selection — it then only does so when you actually press the hotkey.

## Configuration

Settings are automatically saved in `~/.langfixer_pro.json`. You can modify them via the app interface:

| Setting | Default | Description |
|---------|---------|-------------|
| Enable App | `True` | Toggle the tool on/off globally. |
| Floating Button | `True` | Show the popup button on text selection. Off = hotkey only. |
| Always on Top | `True` | Keep the settings window above others. |
| Sound Feedback | `True` | Play a beep sound on successful fix. |
| Start with Windows | `False` | Register the app in `HKCU\...\Run` to launch minimized at logon. |
| Hotkey | `Ctrl+Shift+F9` | Click to record your own shortcut. |

*Start with Windows* is read back from the registry at every launch, so the switch
always shows the real state even if you removed the entry through Task Manager.

## System Tray

The tray icon stays alive for the whole session. Right-click it for a menu:

| Item | Action |
|------|--------|
| Show | Bring the settings window back |
| Enabled | Pause or resume conversion without quitting |
| Start with Windows | Toggle the startup entry |
| Exit | Quit completely |

Double-clicking the icon shows the window. Closing the window with **X** or
**Hide to Tray** parks the app in the tray rather than quitting it.

## Build from Source

```bash
python -m pip install -r requirements.txt pyinstaller
python build_exe.py
```

This produces both artifacts in `dist/`:

| File | What it is |
|------|-----------|
| `LanguageFixerPro.exe` | Portable app (~19 MB) |
| `LanguageFixerPro-Setup.exe` | Installer with the app bundled inside (~38 MB) |

Useful flags:

```bash
python build_exe.py --app-only
```

If [Inno Setup 6](https://jrsoftware.org/isdl.php) is installed, `build_exe.py` also
compiles `installer.iss` into `LanguageFixerPro-Setup-Inno.exe`. It is optional — the
build skips it silently when Inno Setup is not present.

| Script | Purpose |
|--------|---------|
| `main.py` | The application |
| `installer.py` | GUI installer / uninstaller (also builds to an exe) |
| `installer.iss` | Inno Setup script (optional alternative installer) |
| `make_icon.py` | Generates `app_icon.ico`, with a simplified mark at 16/24px |
| `build_exe.py` | Builds everything |

## Contributing

Contributions are welcome. If you have ideas for improving this tool:

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'Add NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

## License

Distributed under the MIT License. See `LICENSE` for more information.
