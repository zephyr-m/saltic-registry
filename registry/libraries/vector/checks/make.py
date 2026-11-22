# Эталоны для vector: Python считает те же действия на double, зерно
# закреплено. Пишет cases.saltic — группу CASES [[действие, a…, b…, ответ…]].
#   python3 registry/libraries/vector/checks/make.py
import math, random, os
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(2026_11_22)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    return text if "." in text else text + ".0"

def vec():
    return [rng.uniform(-50.0, 50.0) for _ in range(3)]

rows = []
for _ in range(30):
    a, b = vec(), vec()
    rows.append(["plus"] + a + b + [a[i] + b[i] for i in range(3)])
    rows.append(["minus"] + a + b + [a[i] - b[i] for i in range(3)])
    rows.append(["dot"] + a + b + [sum(a[i] * b[i] for i in range(3))])
    rows.append(["cross"] + a + b + [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]])
    n = math.sqrt(sum(c * c for c in a))
    rows.append(["unit"] + a + [0.0, 0.0, 0.0] + [c / n for c in a])
    t = rng.uniform(-10.0, 10.0)
    rows.append(["along"] + a + b + [t] + [a[i] + b[i] * t for i in range(3)])

lines = ["-- cases — эталоны для vector (делает make.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append('    ["' + row[0] + '", ' + ", ".join(lit(x) for x in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
