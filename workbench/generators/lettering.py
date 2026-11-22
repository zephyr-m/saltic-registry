import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "registry/libraries/fonts/spleen.saltic"
TARGET = ROOT / "registry/libraries/lettering/glyphs.saltic"
SIZES = [("8X16", 8, 16), ("12X24", 12, 24), ("16X32", 16, 32)]

text = SOURCE.read_text()


def table(name):
    start = text.index(f"GLYPHS_{name} = [")
    depth, index = 0, text.index("[", start)
    begin = index
    while True:
        depth += {"[": 1, "]": -1}.get(text[index], 0)
        index += 1
        if depth == 0:
            break
    body = text[begin + 1:index - 1]
    return [[int(x) for x in re.findall(r"\d+", glyph)] for glyph in re.findall(r"\[([^\[\]]*)\]", body)]


HYPHEN = 13


def em_dash(glyphs, width):
    """Длинное тире: строки дефиса, растянутые на всю ширину буквы."""
    full = (1 << width) - 1
    return [full if row else 0 for row in glyphs[HYPHEN]]


HEADER = [
    "-- glyphs — данные: растровые шрифты Spleen 8×16, 12×24, 16×32 для lettering.",
    "-- Сгенерировано workbench/generators/lettering.py из registry/libraries/fonts/spleen.saltic; руками не править.",
    "-- Глиф — строка hex, 4 цифры на ряд: пиксели в младших битах по ширине",
    "-- глифа, левый пиксель — старший из них.",
    "-- Порядок: ASCII 32–126, затем Ё, А–я, ё, длинное тире (см. lettering.glyph_index).",
    "--",
    "-- GLYPHS_8X16 / GLYPHS_12X24 / GLYPHS_16X32 -> [строки глифов]",
    "",
]
lines = list(HEADER)
for name, width, height in SIZES:
    glyphs = table(name)
    glyphs.append(em_dash(glyphs, width))
    print(f"glyphs: {name} — {len(glyphs)} букв", flush=True)
    lines.append(f"GLYPHS_{name} = [")
    rows = []
    for glyph in glyphs:
        assert len(glyph) == height, (name, len(glyph))
        rows.append('    "' + "".join(f"{row:04x}" for row in glyph) + '"')
    lines.append(",\n".join(rows))
    lines.append("]")
    lines.append("")
TARGET.write_text("\n".join(lines))
print(f"glyphs: записано {TARGET.relative_to(ROOT)}, {TARGET.stat().st_size} байт", flush=True)
