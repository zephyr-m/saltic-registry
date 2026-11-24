# Эталоны для деления bignum (magnitude.split — столбиком по цифрам 2^14):
# частное и остаток считает сам Python — его целые произвольной длины точные.
# Пишет registry/libraries/bignum/checks/split_cases.saltic — группу CASES:
# [имя случая, делимое, делитель, частное, остаток], всё десятичным текстом.
# Случаи: делитель в одну цифру и в две; делимое меньше делителя; степени
# BASE и BASE^k − 1; цифры, прижатые к краям (0, 1, BASE/2, BASE − 1), —
# там угадывание цифры частного ошибается; редкие ветки, найденные моделью
# того же алгоритма: угаданная цифра ≥ BASE, две поправки угадывания и
# «вернуть назад» (вычли лишний делитель); случайные разной длины.
#   python3 -I workbench/references/bignum_split.py
import os
import random
import sys

sys.set_int_max_str_digits(0)

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "bignum", "checks")
rng = random.Random(2026_11_25)
BASE = 1 << 14
EDGES = [0, 1, BASE // 2, BASE - 1]

rows = []


def case(name, a, b):
    rows.append([name, str(a), str(b), str(a // b), str(a % b)])


def number(digits, edgy):
    value = 0
    for place in range(digits):
        digit = rng.choice(EDGES) if edgy and rng.random() < 0.7 else rng.randrange(BASE)
        if place == digits - 1 and digit == 0:
            digit = 1 + rng.randrange(BASE - 1)
        value = value * BASE + digit
    return value


def digits_of(value):
    found = []
    while value:
        found.append(value % BASE)
        value //= BASE
    return found


def branches(a, b):
    """Модель magnitude.split: какие редкие ветки прошло деление a на b."""
    seen = set()
    v_top = digits_of(b)
    if len(v_top) < 2 or a < b:
        return seen
    lift = 14 - v_top[-1].bit_length()
    v = digits_of(b << lift)
    u = digits_of(a << lift) + [0]
    size = len(v)
    steps = len(u) - size
    rest = u[steps:]
    for beat in range(steps):
        rest = [u[steps - 1 - beat]] + rest
        head = rest[size] * BASE + rest[size - 1]
        guess = head // v[-1]
        if guess >= BASE:
            seen.add("clamp")
            guess = BASE - 1
        left = head - guess * v[-1]
        fixes = 0
        while left < BASE and guess * v[-2] > left * BASE + rest[size - 2]:
            guess -= 1
            left += v[-1]
            fixes += 1
        if fixes == 2:
            seen.add("two_fixes")
        value = sum(d * BASE ** i for i, d in enumerate(rest)) - guess * sum(d * BASE ** i for i, d in enumerate(v))
        if value < 0:
            seen.add("add_back")
            value += sum(d * BASE ** i for i, d in enumerate(v))
        rest = digits_of(value) + [0] * size
        rest = rest[:size]
    return seen


case("делимое — ноль", 0, 12345)
case("делимое меньше делителя", 5, 7)
case("делимое меньше длинного делителя", BASE ** 3, BASE ** 5 + 3)
case("равные", BASE ** 4 + 17, BASE ** 4 + 17)
case("делитель — единица", 3 ** 200, 1)
case("делитель в одну цифру", 3 ** 200, BASE - 1)
case("делитель в две цифры", 3 ** 200, BASE + 1)
case("BASE^k − 1 на BASE − 1", BASE ** 30 - 1, BASE - 1)
case("BASE^k − 1 на BASE^j − 1", BASE ** 30 - 1, BASE ** 7 - 1)
case("BASE^k на BASE^j", BASE ** 30, BASE ** 7)
case("2^4096 на 2^2048 − 1", 2 ** 4096, 2 ** 2048 - 1)
case("остаток — делитель без единицы", (BASE ** 9 + 5) * (BASE ** 6 + 1) + BASE ** 6, BASE ** 6 + 1)
case("старшая цифра делителя уже нормальна", BASE ** 20 - 1, (BASE - 1) * BASE ** 4 + 1)
case("старшая цифра делителя — единица", BASE ** 20 - 1, BASE ** 4 + BASE - 1)

wanted = {"clamp": 4, "two_fixes": 4, "add_back": 6}
found = {key: 0 for key in wanted}
tries = 0
while any(found[key] < wanted[key] for key in wanted):
    tries += 1
    b = number(rng.randrange(2, 9), True)
    a = number(rng.randrange(2, 12), True) * b + rng.randrange(b) if rng.random() < 0.5 else number(rng.randrange(3, 18), True)
    for key in branches(a, b):
        if found[key] < wanted[key]:
            found[key] += 1
            case(f"ветка {key} ({found[key]})", a, b)
            break

for beat in range(60):
    b = number(rng.randrange(1, 40), beat % 2 == 0)
    a = number(rng.randrange(1, 80), beat % 3 == 0)
    case(f"случайные {beat + 1}", a, b)

for beat in range(4):
    b = number(rng.randrange(140, 150), beat % 2 == 0)
    a = number(rng.randrange(280, 295), beat % 2 == 1)
    case(f"длинные как RSA-2048 {beat + 1}", a, b)

lines = [
    "-- split_cases — эталоны деления bignum (делает workbench/references/bignum_split.py,",
    "-- руками не править): [имя, делимое, делитель, частное, остаток].",
    "",
    "CASES = [",
]
for index, row in enumerate(rows):
    tail = "," if index < len(rows) - 1 else ""
    lines.append("    [" + ", ".join(f'"{item}"' for item in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "split_cases.saltic"), "w", encoding="utf-8") as out:
    out.write("\n".join(lines) + "\n")
print(f"bignum_split: случаев {len(rows)}, поиск редких веток — {tries} попыток")
