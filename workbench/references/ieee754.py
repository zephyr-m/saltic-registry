# Случаи для сверки ieee754 с железом: Python (x86-64, IEEE 754 без сброса
# субнормальных) считает a op b. Зерно закреплено — файлы воспроизводятся:
#   python3 workbench/references/ieee754.py
# Строка: «операция a b ответ», числа — биты в hex старшим вперёд; NaN — слово
# NAN (биты NaN у разных машин разные, сверяется только «это NaN»).
# float32: считаем в double и округляем в float32 — для + − × ÷ это точно
# (53 ≥ 2·24 + 2, двойное округление не мешает).
import math, random, struct, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "ieee754", "checks", "cases")
COUNT = 1000

def pick_bits(rng, width):
    roll = rng.random()
    total = width * 8
    if roll < 0.45:
        return rng.getrandbits(total)
    if roll < 0.75:
        value = rng.uniform(-4.0, 4.0) * 10 ** rng.randint(-3, 3)
    elif roll < 0.85:
        value = rng.choice([0.0, -0.0, 1.0, -1.0, math.inf, -math.inf, math.nan, 2.0, 0.5, 3.0])
    else:
        exponent_bits = 8 if width == 4 else 11
        fraction_bits = total - 1 - exponent_bits
        field = rng.choice([0, 1, 2, (1 << exponent_bits) - 2])
        return (rng.getrandbits(1) << (total - 1)) | (field << fraction_bits) | rng.getrandbits(fraction_bits)
    fmt = ">f" if width == 4 else ">d"
    return int.from_bytes(struct.pack(fmt, value), "big")

def value_of(bits, width):
    fmt = ">f" if width == 4 else ">d"
    return struct.unpack(fmt, bits.to_bytes(width, "big"))[0]

def text_of(value, width):
    if math.isnan(value):
        return "NAN"
    fmt = ">f" if width == 4 else ">d"
    return struct.pack(fmt, value).hex().upper()

def apply(op, a, b):
    try:
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if b == 0.0:
            if a == 0.0 or math.isnan(a): return math.nan
            sign = math.copysign(1.0, a) * math.copysign(1.0, b)
            return math.copysign(math.inf, sign)
        return a / b
    except OverflowError:
        return math.copysign(math.inf, a)

def build(width, name, seed):
    rng = random.Random(seed)
    lines = []
    for _ in range(COUNT):
        op = rng.choice("+-*/")
        a_bits, b_bits = pick_bits(rng, width), pick_bits(rng, width)
        a, b = value_of(a_bits, width), value_of(b_bits, width)
        result = apply(op, a, b)
        if width == 4 and not math.isnan(result):
            try:
                result = struct.unpack(">f", struct.pack(">f", result))[0]
            except OverflowError:
                result = math.copysign(math.inf, result)
        digits = width * 2
        lines.append(f"{op} {a_bits:0{digits}X} {b_bits:0{digits}X} {text_of(result, width)}")
    with open(os.path.join(HERE, name), "w") as out:
        out.write("\n".join(lines) + "\n")

build(4, "f32.txt", 2026_11_22)
build(8, "f64.txt", 2026_11_23)
