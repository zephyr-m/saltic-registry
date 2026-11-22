# Эталоны для exponent: Python math (double) считает функции в случайных
# точках, зерно закреплено. Пишет cases.saltic — группу CASES
# [[функция, x, y, ответ], …]; y есть только у raised. Числа — десятичной
# записью без «e», в пределах 1e−40 … 1e40, чтобы литералы были короткими.
# Входы сначала округляются до 50 значимых бит — ровно как их держит
# core.fraction, — и Python считает от того же x, что и Saltic.
#   python3 workbench/references/exponent.py
import math, random, os
from decimal import Decimal

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "exponent", "checks")
rng = random.Random(2026_11_22)

BITS = 50

def held(x):
    # как держит core.fraction: 50 значимых бит, к ближайшему
    if x == 0.0:
        return 0.0
    m, e = math.frexp(x)
    return math.ldexp(round(m * 2 ** BITS), e - BITS)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    if "." not in text:
        text += ".0"
    return text

cases = []
for _ in range(60):
    x = rng.uniform(-90.0, 90.0)
    cases.append(("exp", x, 0.0, math.exp(x)))
for x in [0.0, 1.0, -1.0, 0.5, 1e-10, -1e-10, 0.6931471805599453, 2.0]:
    cases.append(("exp", x, 0.0, math.exp(x)))
for _ in range(50):
    x = 10 ** rng.uniform(-35.0, 35.0)
    cases.append(("log", x, 0.0, math.log(x)))
for x in [1.0, 2.0, 0.5, 1.0000001, 0.9999999, 10.0, 2.718281828459045]:
    cases.append(("log", x, 0.0, math.log(x)))
for _ in range(30):
    x = 10 ** rng.uniform(-30.0, 30.0)
    cases.append(("log2", x, 0.0, math.log2(x)))
for x in [1.0, 2.0, 1024.0, 0.125, 3.0]:
    cases.append(("log2", x, 0.0, math.log2(x)))
for _ in range(30):
    x = 10 ** rng.uniform(-30.0, 30.0)
    cases.append(("log10", x, 0.0, math.log10(x)))
for x in [1.0, 10.0, 1000.0, 0.001, 2.0]:
    cases.append(("log10", x, 0.0, math.log10(x)))
for _ in range(25):
    x = rng.uniform(0.01, 30.0)
    y = rng.uniform(-8.0, 8.0)
    cases.append(("raised", x, y, x ** y))
for x, y in [(2.0, 10.0), (2.0, -3.0), (-2.0, 3.0), (-2.0, 4.0), (9.0, 0.5), (10.0, 20.0), (1.0001, 10000.0), (5.0, 0.0), (0.0, 3.0), (1.5, -2.0)]:
    cases.append(("raised", x, y, x ** y))

lines = ["-- cases — эталоны Python math для exponent (делает workbench/references/exponent.py, руками не править).", "", "CASES = ["]
cases = [(name, held(x), held(y), None) for name, x, y, _ in cases]
def answer(name, x, y):
    if name == "exp": return math.exp(x)
    if name == "log": return math.log(x)
    if name == "log2": return math.log2(x)
    if name == "log10": return math.log10(x)
    return x ** y
cases = [(name, x, y, answer(name, x, y)) for name, x, y, _ in cases]
for i, (name, x, y, want) in enumerate(cases):
    tail = "," if i < len(cases) - 1 else ""
    lines.append(f'    ["{name}", {lit(x)}, {lit(y)}, {lit(want)}]{tail}')
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(cases), "случаев")
