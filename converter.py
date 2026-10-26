"""
Arabic <-> English keyboard layout conversion.

Kept free of GUI and Windows imports so it can be tested on its own.
The maps follow Windows' "Arabic (101)" layout key for key.
"""

EN_TO_AR_MAP = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ',
    'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'د',
    'a': 'ش', 's': 'س', 'd': 'ي', 'f': 'ب', 'g': 'ل', 'h': 'ا',
    'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ك', "'": 'ط',
    'z': 'ئ', 'x': 'ء', 'c': 'ؤ', 'v': 'ر', 'b': 'لا', 'n': 'ى',
    'm': 'ة', ',': 'و', '.': 'ز', '/': 'ظ',
    '`': 'ذ', '~': 'ّ',
    'Q': 'َ', 'W': 'ً', 'E': 'ُ', 'R': 'ٌ', 'T': 'لإ', 'Y': 'إ',
    'U': '‘', 'I': '÷', 'O': '×', 'P': '؛', '{': '<', '}': '>',
    'A': 'ِ', 'S': 'ٍ', 'D': ']', 'F': '[', 'G': 'لأ', 'H': 'أ',
    'J': 'ـ', 'K': '،', 'L': '/', ':': ':', '"': '"',
    'Z': '~', 'X': 'ْ', 'C': '}', 'V': '{', 'B': 'لآ', 'N': 'آ',
    'M': '’', '<': ',', '>': '.', '?': '؟',
    # the layout swaps the parentheses so they look right in right-to-left text
    '(': ')', ')': '(',
}

AR_TO_EN_MAP = {}
for k, v in EN_TO_AR_MAP.items():
    if len(v) == 1:
        AR_TO_EN_MAP[v] = k

COMPOUND_AR = [('لآ', 'B'), ('لأ', 'G'), ('لإ', 'T')]

# The B key types لا as two ordinary letters, ل then ا — exactly what G then H
# type. So لا can mean "b" or "gh" and only the surrounding word can tell.
LAM_ALEF = 'لا'
_PENDING = '\x00'

# words where gh starts the word or follows letters the rules below can't trust
GH_WORDS = {
    "ghost", "ghosts", "ghostly", "ghetto", "ghettos", "ghoul", "ghouls",
    "aghast", "spaghetti", "yoghurt", "dinghy", "afghan", "ugh", "hugh",
}


def _gh_or_b(before, after):
    """Pick "gh" or "b" from the lowercase letters of the same word on each side."""
    if before + "gh" + after in GH_WORDS:
        return "gh"
    if before.endswith(("ei", "au")):                 # eight, weigh, caught, laugh
        return "gh"
    if before.endswith("ou"):                         # though, enough, thought
        if after.startswith("l"):                     # double, trouble
            return "b"
        if before.endswith("dou") and after.startswith("t"):   # doubt
            return "b"
        return "gh"
    if before.endswith("i"):
        if after.startswith("t"):                     # light, night, straight
            return "gh"
        if not after and before.endswith(("hi", "si")):         # high, thigh, sigh
            return "gh"
        if before.endswith("hi") and (after in ("er", "est", "ly", "ness", "s")
                                      or after.startswith(("way", "land", "light"))):
            return "gh"                               # higher, highway, highlight
    return "b"


def _is_letter(piece):
    return piece.isascii() and piece.isalpha()


def _resolve_lam_alef(pieces):
    """Replace each pending لا marker with "b" or "gh", left to right."""
    for i, piece in enumerate(pieces):
        if piece != _PENDING:
            continue
        j = i
        while j > 0 and _is_letter(pieces[j - 1]):
            j -= 1
        k = i + 1
        while k < len(pieces) and (pieces[k] == _PENDING or _is_letter(pieces[k])):
            k += 1
        before = "".join(pieces[j:i]).lower()
        after = "".join("gh" if p == _PENDING else p for p in pieces[i + 1:k]).lower()
        pieces[i] = _gh_or_b(before, after)
    return pieces


def convert_text(text, direction="auto"):
    ar_count = sum(1 for c in text if '؀' <= c <= 'ۿ')
    en_count = sum(1 for c in text if c.isascii() and c.isalpha())

    if direction == "auto":
        is_arabic = ar_count >= en_count
    elif direction == "ar_to_en":
        is_arabic = True
    else:
        is_arabic = False

    if not is_arabic:
        return "".join(EN_TO_AR_MAP.get(ch, ch) for ch in text)

    temp = text
    for ar, en in COMPOUND_AR:
        temp = temp.replace(ar, en)
    temp = temp.replace(LAM_ALEF, _PENDING)
    pieces = [AR_TO_EN_MAP.get(ch, ch) for ch in temp]
    return "".join(_resolve_lam_alef(pieces))
