# Эталоны для linear: точные дроби Python (fractions) — определитель и решение
# A·x = b на целых матрицах считаются без единой ошибки округления. Пишет
# cases.saltic — группу CASES [[n, a00 … a(n−1)(n−1), b0 … b(n−1), det, x0 …]].
#   python3 registry/libraries/linear/checks/make.py
import random, os
from fractions import Fraction
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(2026_11_22)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    return text if "." in text else text + ".0"

def det(m):
    n = len(m)
    m = [row[:] for row in m]
    result = Fraction(1)
    for k in range(n):
        p = next((i for i in range(k, n) if m[i][k] != 0), None)
        if p is None:
            return Fraction(0)
        if p != k:
            m[k], m[p] = m[p], m[k]
            result = -result
        result *= m[k][k]
        for i in range(k + 1, n):
            f = m[i][k] / m[k][k]
            for j in range(k, n):
                m[i][j] -= f * m[k][j]
    return result

def solve(m, b):
    n = len(m)
    a = [row[:] + [b[i]] for i, row in enumerate(m)]
    for k in range(n):
        p = next(i for i in range(k, n) if a[i][k] != 0)
        a[k], a[p] = a[p], a[k]
        for i in range(n):
            if i != k:
                f = a[i][k] / a[k][k]
                for j in range(k, n + 1):
                    a[i][j] -= f * a[k][j]
    return [a[i][n] / a[i][i] for i in range(n)]

rows = []
while len(rows) < 30:
    n = rng.randint(2, 6)
    m = [[Fraction(rng.randint(-9, 9)) for _ in range(n)] for _ in range(n)]
    d = det(m)
    if d == 0:
        continue
    b = [Fraction(rng.randint(-20, 20)) for _ in range(n)]
    x = solve(m, b)
    rows.append([n] + [c for row in m for c in row] + b + [d] + x)

lines = ["-- cases — эталоны для linear, точные дроби Python (делает make.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + str(row[0]) + ", " + ", ".join(lit(float(v)) for v in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "систем")
