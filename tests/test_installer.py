import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

installer = pytest.importorskip("installer")


@pytest.mark.parametrize("typed, expected", [
    (r"D:\\", r"D:\LanguageFixerPro"),
    (r"C:\Users\me\Documents", r"C:\Users\me\Documents\LanguageFixerPro"),
    (r"C:\Apps\LanguageFixerPro", r"C:\Apps\LanguageFixerPro"),
    (r"C:\Apps\languagefixerpro\\", r"C:\Apps\languagefixerpro"),
    (r"  C:\Apps  ", r"C:\Apps\LanguageFixerPro"),
])
def test_install_always_gets_its_own_folder(typed, expected):
    assert installer.normalize_install_dir(typed) == expected


def test_uninstall_only_owns_its_binaries():
    assert set(installer.OWNED_FILES) == {"LanguageFixerPro.exe", "uninstall.exe"}


def test_remove_installation_leaves_other_files(tmp_path, monkeypatch):
    # neutralise everything that touches the real system
    for name in ("stop_running_app", "set_startup", "unregister_uninstall"):
        monkeypatch.setattr(installer, name, lambda *a, **k: None)
    monkeypatch.setattr(installer, "start_menu_dir", lambda: str(tmp_path / "menu"))
    monkeypatch.setattr(installer, "desktop_dir", lambda: str(tmp_path / "desk"))
    launched = []
    monkeypatch.setattr(installer.subprocess, "Popen",
                        lambda cmd, **k: launched.append(cmd))

    folder = tmp_path / "Documents"
    folder.mkdir()
    (folder / "LanguageFixerPro.exe").write_bytes(b"x")
    (folder / "uninstall.exe").write_bytes(b"x")
    (folder / "thesis.docx").write_bytes(b"precious")
    (folder / "photos").mkdir()
    (folder / "photos" / "a.jpg").write_bytes(b"precious")

    installer.remove_installation(str(folder))

    assert not (folder / "LanguageFixerPro.exe").exists()
    assert not (folder / "uninstall.exe").exists()
    assert (folder / "thesis.docx").read_bytes() == b"precious"
    assert (folder / "photos" / "a.jpg").read_bytes() == b"precious"
    assert "/s" not in launched[0]
