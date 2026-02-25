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
- **Stealth Mode**: Option to hide the floating button and rely solely on shortcuts.
- **Smart Detection**: Automatically detects if the text needs to be Arabic or English.
- **Interactive Feedback**: Subtle sound effects and visual cues.
- **Persistance**: Remembers your settings and window position.
- **Tray Icon**: Minimize to the system tray to keep your taskbar clean.

## Built with Vibe Coding

This project is a product of **Vibe Coding**.
We leveraged the flow state of AI-assisted development to bring this idea to life rapidly. It represents a modern approach to software engineering where intuition meets AI acceleration to solve real-world micro-frustrations efficiently.

## Installation

### Option 1: Portable EXE (Recommended)
1. Go to the [Releases](../../releases) page.
2. Download `LanguageFixerPro.exe`.
3. Run it directly — no installation required.

### Option 2: Run from Source
If you are a developer or want to vibe with the code:

```bash
# Clone the repo
git clone https://github.com/s5xx5s/LanguageFixerPro.git
cd LanguageFixerPro

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
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

> **Note:** You can disable the floating button in settings if you prefer using shortcuts only.

## Configuration

Settings are automatically saved in `~/.langfixer_pro.json`. You can modify them via the app interface:

| Setting | Default | Description |
|---------|---------|-------------|
| Enable App | `True` | Toggle the tool on/off globally. |
| Show Floating Button | `True` | Show the popup button on text selection. |
| Always on Top | `True` | Keep the settings window above others. |
| Sound Feedback | `True` | Play a beep sound on successful fix. |
| Hotkey | `Ctrl+Shift+F9` | Click to record your own shortcut. |

## Build EXE

To build your own executable:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "LanguageFixerPro" --icon "icon.ico" main.py
```

## Contributing

Contributions are welcome. If you have ideas for improving this tool:

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'Add NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

## License

Distributed under the MIT License. See `LICENSE` for more information.
