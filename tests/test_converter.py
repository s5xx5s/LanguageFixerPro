import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter import EN_TO_AR_MAP, convert_text  # noqa: E402


def typed_in_arabic(english):
    """What the keyboard produces when English is typed on the Arabic layout."""
    return convert_text(english, "en_to_ar")


@pytest.mark.parametrize("word", [
    # gh words — لا must come back as "gh"
    "light", "right", "night", "might", "straight", "tonight", "lightning",
    "high", "thigh", "sigh", "higher", "highest", "highly", "highway", "highlight",
    "eight", "weight", "height", "neighbor", "weigh",
    "though", "through", "thought", "bought", "brought", "enough", "rough",
    "cough", "dough", "doughnut",
    "caught", "taught", "daughter", "laugh",
    "ghost", "spaghetti",
    # b words — لا must stay "b"
    "bob", "about", "number", "possible", "possibly", "visible", "terribly",
    "public", "subject", "rabbit", "obtain", "doubt", "double", "trouble",
    "habit", "tribe", "crib", "rib", "exhibit", "inhibit", "hibernate", "ribbon",
    "club", "pub", "debt", "orbit",
])
def test_round_trip_words(word):
    assert convert_text(typed_in_arabic(word), "ar_to_en") == word


def test_round_trip_sentence_auto():
    sentence = "the light at night was bright enough, (about 8 o'clock)."
    assert convert_text(typed_in_arabic(sentence)) == sentence


def test_capital_g_is_not_ambiguous():
    # Shift+G types لأ, a different sequence from لا
    assert convert_text(typed_in_arabic("Ghost"), "ar_to_en") == "Ghost"


def test_english_to_arabic():
    assert convert_text("hgsghl ugd;l") == "السلام عليكم"


def test_arabic_to_english():
    assert convert_text("اثممخ") == "hello"


@pytest.mark.parametrize("key, char", [
    ("C", "}"), ("V", "{"), ("U", "‘"), ("M", "’"), ("(", ")"), (")", "("),
])
def test_shift_row_matches_windows_arabic_101(key, char):
    assert EN_TO_AR_MAP[key] == char


def test_parentheses_come_back_the_right_way_round():
    assert convert_text(typed_in_arabic("(hi)"), "ar_to_en") == "(hi)"


def test_text_without_mapped_characters_is_unchanged():
    assert convert_text("123 456") == "123 456"
    assert convert_text("") == ""
