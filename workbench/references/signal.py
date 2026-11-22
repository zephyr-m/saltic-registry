# Эталоны для signal: Python считает ДПФ прямо по определению (без FFT),
# свёртку и КИХ-фильтр — прямо по сумме. Пишет cases.saltic — группу CASES:
# [«dft», n, re…, im…, re'…, im'…], [«convolve», na, nb, a…, b…, ответ…],
# [«fir», n, taps, x…, h…, ответ…]. Зерно закреплено:
#   python3 workbench/references/signal.py
import math, random, os
from decimal import Decimal

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "signal", "checks")
rng = random.Random(2026_11_22)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    return text if "." in text else text + ".0"

def dft(re, im):
    n = len(re)
    out_re, out_im = [], []
    for k in range(n):
        sr = si = 0.0
        for t in range(n):
            a = -2 * math.pi * k * t / n
            sr += re[t] * math.cos(a) - im[t] * math.sin(a)
            si += re[t] * math.sin(a) + im[t] * math.cos(a)
        out_re.append(sr)
        out_im.append(si)
    return out_re, out_im

def convolve(a, b):
    return [sum(a[j] * b[i - j] for j in range(len(a)) if 0 <= i - j < len(b)) for i in range(len(a) + len(b) - 1)]

rows = []
for n in [1, 2, 4, 8, 16, 32, 64, 3, 6, 12]:
    re = [rng.uniform(-5, 5) for _ in range(n)]
    im = [rng.uniform(-5, 5) for _ in range(n)]
    fr, fi = dft(re, im)
    rows.append(["dft", n] + re + im + fr + fi)
for _ in range(12):
    a = [rng.uniform(-3, 3) for _ in range(rng.randint(1, 20))]
    b = [rng.uniform(-3, 3) for _ in range(rng.randint(1, 12))]
    rows.append(["convolve", len(a), len(b)] + a + b + convolve(a, b))
for _ in range(6):
    x = [rng.uniform(-1, 1) for _ in range(rng.randint(5, 40))]
    h = [rng.uniform(-1, 1) for _ in range(rng.randint(1, 8))]
    rows.append(["fir", len(x), len(h)] + x + h + convolve(x, h)[:len(x)])

def word(v):
    return str(v) if isinstance(v, int) else lit(v)

lines = ["-- cases — эталоны для signal (делает workbench/references/signal.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append('    ["' + row[0] + '", ' + ", ".join(word(v) for v in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
