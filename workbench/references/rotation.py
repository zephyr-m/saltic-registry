# Эталоны для rotation — независимым способом, без кватернионов: формула
# Родрига v·cosθ + (k×v)·sinθ + k·(k·v)·(1 − cosθ) и её матрица. Пишет
# cases.saltic — группу CASES. Зерно закреплено:
#   python3 workbench/references/rotation.py
# turn     — [«turn», ось, угол, вектор, ответ]
# compose  — [«compose», ось1, угол1, ось2, угол2, вектор, ответ] — сначала 1, потом 2
# halfway  — [«halfway», ось, угол, доля t, вектор, ответ] — поворот на t · угол
# matrix   — [«matrix», ось, угол, девять чисел матрицы по строкам]
import math, random, os
from decimal import Decimal

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "rotation", "checks")
rng = random.Random(2026_11_22)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    return text if "." in text else text + ".0"

def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return [c / n for c in v]

def rodrigues(axis, angle, v):
    k = unit(axis)
    c, s = math.cos(angle), math.sin(angle)
    cross = [k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0]]
    dot = sum(a * b for a, b in zip(k, v))
    return [v[i] * c + cross[i] * s + k[i] * dot * (1 - c) for i in range(3)]

def matrix(axis, angle):
    columns = [rodrigues(axis, angle, e) for e in ([1, 0, 0], [0, 1, 0], [0, 0, 1])]
    return [columns[j][i] for i in range(3) for j in range(3)]

def vec():
    return [rng.uniform(-3.0, 3.0) for _ in range(3)]

def ang():
    return rng.uniform(-6.0, 6.0)

rows = []
for _ in range(40):
    axis, angle, v = vec(), ang(), vec()
    rows.append(["turn"] + axis + [angle] + v + rodrigues(axis, angle, v))
for axis, angle, v in [([0, 0, 1], math.pi / 2, [1, 0, 0]), ([1, 0, 0], math.pi, [0, 1, 0]), ([0, 1, 0], 0.0, [1, 2, 3])]:
    rows.append(["turn"] + axis + [angle] + v + rodrigues(axis, angle, v))
for _ in range(25):
    a1, t1, a2, t2, v = vec(), ang(), vec(), ang(), vec()
    rows.append(["compose"] + a1 + [t1] + a2 + [t2] + v + rodrigues(a2, t2, rodrigues(a1, t1, v)))
for _ in range(20):
    axis, angle, t, v = vec(), rng.uniform(-3.0, 3.0), rng.uniform(0.0, 1.0), vec()
    rows.append(["halfway"] + axis + [angle, t] + v + rodrigues(axis, angle * t, v))
for _ in range(10):
    axis, angle = vec(), ang()
    rows.append(["matrix"] + axis + [angle] + matrix(axis, angle))

lines = ["-- cases — эталоны для rotation по формуле Родрига (делает workbench/references/rotation.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append('    ["' + row[0] + '", ' + ", ".join(lit(x) for x in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
