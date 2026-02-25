# Language Fixer Pro ع⇄A

> Fix text typed in the wrong keyboard layout — instantly.

Ever typed `hgsghl` when you meant **السلام**? Or `اثممخ` when you meant **hello**?

Language Fixer Pro fixes this with one click.

![Screenshot](screenshot.png)

## Features

- **Floating Button** — appears automatically when you select text
- **Keyboard Shortcut** — customizable (default: `Ctrl+Shift+F9`)
- **Auto Detection** — detects whether text should be Arabic or English
- **System Tray** — runs quietly in the background
- **Always on Top** — optional floating window
- **Sound Feedback** — optional beep on conversion
- **Settings Persistence** — remembers your preferences
- **Update Checker** — notifies you of new versions

## Installation

### Option 1: Download EXE (Recommended)
1. Go to [Releases](../../releases)
2. Download `LanguageFixerPro.exe`
3. Run it — no installation needed!

### Option 2: Run from Source
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/LanguageFixerPro.git
cd LanguageFixerPro

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## How to Use

1. **Select** any mistyped text (mouse drag, double-click, or Shift+arrows)
2. **Click** the floating blue button that appears, or press `Ctrl+Shift+F9`
3. Text is **converted** to the correct language!

## Build EXE

```bash
pip install pyinstaller
python build_exe.py
# Output: dist/LanguageFixerPro.exe
```

## Requirements

- Windows 10/11
- Python 3.8+ (for running from source)

### Dependencies
```
customtkinter
pynput
pyperclip
pystray
Pillow
```

## Configuration

Settings are saved in `~/.langfixer_pro.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| `hotkey` | `ctrl+shift+f9` | Keyboard shortcut |
| `direction` | `auto` | `auto`, `ar_to_en`, or `en_to_ar` |
| `always_on_top` | `true` | Keep window on top |
| `sound_enabled` | `true` | Beep on conversion |

## Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## Roadmap

- [ ] Context-aware conversion using dictionary
- [ ] Conversion history with undo
- [ ] Auto-start with Windows
- [ ] Toast notifications
- [ ] Support for more languages (Persian, Urdu, French AZERTY)
- [ ] Spell check after conversion

## License

[MIT License](LICENSE) — free to use, modify, and distribute.

## Acknowledgments

Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI.