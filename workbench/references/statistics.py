# Эталоны для statistics: модуль Python statistics. Случайные выборки разной
# длины и масштаба (и сдвинутые на 1e9 — проверка устойчивости дисперсии).
# Пишет cases.saltic — группу CASES [n, данные x…, данные y…, mean, variance,
# pvariance, median, q1, q2, q3, least, most, covariance, correlation, наклон,
# сдвиг, допуск]. Входы округлены до 50 значимых бит, как их держит
# core.fraction. Допуск — предел 50 бит с учётом обусловленности: у выборок,
# сдвинутых на 1e9, сдвиг регрессии продлевает прямую на миллиард от облака
# точек — ошибка наклона множится на 1e9, допуск 1e−5; у остальных — 1e−11.
#   python3 workbench/references/statistics.py
import math, random, os, statistics
from decimal import Decimal

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "statistics", "checks")
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
    return text if "." in text else text + ".0"

rows = []
for n in [3, 4, 5, 10, 17, 50, 100, 8, 9, 30]:
    base = rng.choice([0.0, 1e9, -100.0])
    x = [held(base + rng.uniform(-50, 50)) for _ in range(n)]
    y = [held(3.0 * v + rng.gauss(0, 5)) for v in x]
    close = 1e-5 if base == 1e9 else 1e-11
    q = statistics.quantiles(x, n=4)
    slope, intercept = statistics.linear_regression(x, y)
    rows.append([n] + x + y + [statistics.fmean(x), statistics.variance(x), statistics.pvariance(x), statistics.median(x)] + q + [min(x), max(x), statistics.covariance(x, y), statistics.correlation(x, y), slope, intercept, close])

lines = ["-- cases — эталоны для statistics от Python statistics (делает workbench/references/statistics.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + str(row[0]) + ", " + ", ".join(lit(v) for v in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "выборок")
