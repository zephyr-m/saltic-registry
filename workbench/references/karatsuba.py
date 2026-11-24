# Эталоны для karatsuba (умножение больших целых): произведения считает сам
# Python — его целые произвольной длины точные. Числа — десятичным текстом.
# Пишет registry/libraries/karatsuba/checks/cases.saltic — группу CASES:
# [имя случая, множитель a, множитель b, произведение a · b].
# Случаи: 0, 1 и знаки; края цифры bignum (2^14) и порога (20 цифр по 14 бит,
# и вдвое, и вчетверо); нули внутри и одни девятки (переносы при сложении
# половинок); случайные разной длины и знака; тысячи десятичных цифр.
#   python3 -I workbench/references/karatsuba.py
import os
import random
import sys

sys.set_int_max_str_digits(0)

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "karatsuba", "checks")
rng = random.Random(2026_11_24)
BASE = 1 << 14

rows = []


def case(name, a, b):
    rows.append([name, str(a), str(b), str(a * b)])


def decimal(length):
    return rng.randrange(10 ** (length - 1), 10 ** length)


def signed(value):
    return value if rng.randrange(2) else -value


case("0 · 0", 0, 0)
case("0 · 1", 0, 1)
case("1 · 0", 1, 0)
case("1 · 1", 1, 1)
case("-1 · 1", -1, 1)
case("-1 · -1", -1, -1)
case("0 · -5", 0, -5)
case("2 · 3", 2, 3)
case("-7 · 6", -7, 6)
case("большое · 0", decimal(900), 0)
case("большое · 1", decimal(900), 1)
case("большое · -1", decimal(900), -1)
case("край цифры: (2^14 - 1)²", BASE - 1, BASE - 1)
case("край цифры: 2^14 · 2^14", BASE, BASE)
case("край цифры: (2^14 + 1) · -(2^14 - 1)", BASE + 1, -(BASE - 1))
for digits in (3, 4, 5, 19, 20, 21, 39, 40, 41, 79, 80, 81, 160, 161):
    case(f"{digits} цифр: все старшие (BASE^n - 1)²", BASE ** digits - 1, BASE ** digits - 1)
    case(f"{digits} цифр: наименьшее BASE^(n-1) · случайное", BASE ** (digits - 1), -rng.randrange(BASE ** (digits - 1), BASE ** digits))
    case(f"{digits} цифр: случайные", rng.randrange(BASE ** (digits - 1), BASE ** digits), rng.randrange(BASE ** (digits - 1), BASE ** digits))
for digits in (40, 64, 97):
    half = digits // 2
    high = rng.randrange(BASE ** (digits - half - 1), BASE ** (digits - half))
    low = rng.randrange(1, BASE ** 3)
    case(f"{digits} цифр: нули в младшей половине", high * BASE ** half, high * BASE ** half + low)
    case(f"{digits} цифр: нули в середине", high * BASE ** half + low, -(BASE ** (digits - 1) + 1))
    case(f"{digits} цифр: нули в старшей половине · длинное", low, rng.randrange(BASE ** (digits - 1), BASE ** digits))
for length in (50, 100, 500, 1000):
    case(f"{length} девяток в квадрате", 10 ** length - 1, 10 ** length - 1)
    case(f"10^{length} · -10^{length // 2}", 10 ** length, -(10 ** (length // 2)))
for _ in range(40):
    left = rng.randint(1, 700)
    right = rng.randint(1, 700)
    case(f"случайные {left} × {right} знаков", signed(decimal(left)), signed(decimal(right)))
for left, right in ((1000, 1000), (2000, 2000), (3000, 3000), (4000, 50), (30, 3500), (2500, 700), (1, 3000), (2048, 2047)):
    case(f"длинные {left} × {right} знаков", signed(decimal(left)), signed(decimal(right)))

with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("-- cases — произведения больших целых от Python (workbench/references/karatsuba.py\n")
    out.write("-- реестра), не править руками: [имя случая, a, b, a · b] — числа десятичным текстом\n\n")
    out.write("CASES = [\n")
    out.write(",\n".join("    [" + ", ".join('"%s"' % item for item in row) + "]" for row in rows))
    out.write("\n]\n")
print(f"karatsuba: {len(rows)} случаев → {os.path.normpath(os.path.join(HERE, 'cases.saltic'))}")
