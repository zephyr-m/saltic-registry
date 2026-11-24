# Эталоны для cordic: Python math (sin, cos, atan2, hypot) на целых с масштабом
# ONE = 2^24 и допуски, выведенные из числа шагов, а не подобранные по прогону.
# Пишет registry/libraries/cordic/checks/cases.saltic:
#   TURNS = [[угол · ONE, round(cos · ONE), round(sin · ONE)], …]
#   POINTS = [[y, x, round(atan2 · ONE), round(hypot)], …]
#   TABLE — round(atan(2^−i) · ONE), CONSTANTS — [ONE, PI, HALF_PI, TWO_PI, GAIN]
#   SINE_TOLERANCE, ANGLE_TOLERANCE — в единицах 2^−24; LENGTH_TOLERANCE — доля 2^−24
#   python3 -I workbench/references/cordic.py
#
# Вывод допусков (N шагов, α_i = atan(2^−i), A_i — α_i · ONE, округлённые;
# K = ∏ √(1 + 2^−2i) — растяжение, ε = √2 / 2 — сдвиг с округлением даёт ≤ ½ на
# каждую из двух координат):
#   sin/cos: остаток угла ≤ A_{N−1}; таблица ошибается на Σ|A_i − α_i·ONE|;
#     приведение к −π…π — до 3 вычитаний TWO_PI и одно PI; 1/K записан с
#     ошибкой ½ и растянут в K; округления N − 1 шагов — (N − 1)·ε·K.
#   atan2: тот же остаток и таблица, PI; округление каждого шага поворачивает
#     вектор длины ≥ 2^24 не больше чем на ε / 2^24 рад — (N − 1)·ε; ввод в
#     2^24…2^25 сдвигом с округлением — ещё ε.
#   hypot: доля (N − 1)·ε (растяжение K у ошибки и у длины общее); ввод ε;
#     1/K в GAIN — ½·ONE / GAIN; деление на K сдвигами — по ½ на каждый бит GAIN.
#   Сверка с округлённым эталоном добавляет ещё ½ (у hypot — ½ на итоговое
#   округление и ½ на эталон, проверка берёт их как 1).
import math
import os
import random

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "cordic", "checks")
N = 24
ONE = 1 << 24
MAXIMUM = 268435455
LIMIT = (1 << 27) - 1
PI = round(math.pi * ONE)
HALF_PI = round(math.pi / 2 * ONE)
TWO_PI = round(2 * math.pi * ONE)
TABLE = [round(math.atan(2.0 ** -i) * ONE) for i in range(N)]
K = math.prod(math.sqrt(1 + 2.0 ** (-2 * i)) for i in range(N))
GAIN = round(ONE / K)
EPS = math.sqrt(2) / 2
table_error = sum(abs(TABLE[i] - math.atan(2.0 ** -i) * ONE) for i in range(N))
sine = TABLE[-1] + table_error + 3 * abs(TWO_PI - 2 * math.pi * ONE) + abs(PI - math.pi * ONE) + 0.5 * K + (N - 1) * EPS * K + 0.5
angle = TABLE[-1] + table_error + abs(PI - math.pi * ONE) + (N - 1) * EPS + EPS + 0.5
length = (N - 1) * EPS + EPS + 0.5 * ONE / GAIN + 0.5 * bin(GAIN).count("1")
SINE_TOLERANCE = math.ceil(sine)
ANGLE_TOLERANCE = math.ceil(angle)
LENGTH_TOLERANCE = math.ceil(length)

rng = random.Random(2026_11_24)
angles = [0, 1, -1, 2, -2, 7, -7, 100, -100, HALF_PI, -HALF_PI, HALF_PI + 1, HALF_PI - 1, -HALF_PI - 1, -HALF_PI + 1,
          PI, -PI, PI + 1, PI - 1, -PI + 1, -PI - 1, TWO_PI, -TWO_PI, TWO_PI + HALF_PI, 3 * PI, -3 * PI, 5 * HALF_PI,
          -5 * HALF_PI, MAXIMUM, -MAXIMUM, MAXIMUM - 1, ONE, -ONE]
for quarter in range(-8, 8):
    angles.append(quarter * HALF_PI + rng.randint(1, HALF_PI - 1))
for _ in range(40):
    angles.append(rng.randint(-MAXIMUM, MAXIMUM))
turns = [[a, round(math.cos(a / ONE) * ONE), round(math.sin(a / ONE) * ONE)] for a in angles]

points = [[0, 1], [0, -1], [1, 0], [-1, 0], [0, 5], [0, -5], [7, 0], [-7, 0], [1, 1], [-1, 1], [1, -1], [-1, -1],
          [4, 3], [-4, 3], [4, -3], [-4, -3], [12, 5], [1, 1000000], [-1, -1000000], [1, -1000000], [-1, -1000000],
          [LIMIT, LIMIT], [-LIMIT, LIMIT], [LIMIT, -LIMIT], [-LIMIT, -LIMIT], [LIMIT, 0], [0, -LIMIT], [LIMIT, 1],
          [1, LIMIT], [ONE, ONE], [ONE - 1, -ONE], [(1 << 25), 3], [(1 << 25) - 1, -(1 << 24)]]
for size in (3, 50, 1000, 100000, ONE, LIMIT):
    for _ in range(8):
        y, x = rng.randint(-size, size), rng.randint(-size, size)
        if (x, y) == (0, 0):
            x = 1
        points.append([y, x])
rows = [[y, x, round(math.atan2(y, x) * ONE), round(math.hypot(x, y))] for y, x in points]


def group(values):
    return "[" + ", ".join(str(v) for v in values) + "]"


with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("-- cases — эталоны для cordic от Python math (workbench/references/cordic.py\n")
    out.write("-- реестра), руками не править. Допуски выведены в шапке эталона из числа шагов.\n\n")
    out.write(f"SINE_TOLERANCE = {SINE_TOLERANCE}\nANGLE_TOLERANCE = {ANGLE_TOLERANCE}\nLENGTH_TOLERANCE = {LENGTH_TOLERANCE}\n")
    out.write(f"CONSTANTS = {group([ONE, PI, HALF_PI, TWO_PI, GAIN])}\n")
    out.write(f"TABLE = {group(TABLE)}\n\nTURNS = [\n")
    out.write(",\n".join("    " + group(row) for row in turns))
    out.write("\n]\n\nPOINTS = [\n")
    out.write(",\n".join("    " + group(row) for row in rows))
    out.write("\n]\n")
print(f"cordic: углов {len(turns)}, точек {len(rows)}; допуски: sin/cos {sine:.2f} → {SINE_TOLERANCE}, "
      f"atan2 {angle:.2f} → {ANGLE_TOLERANCE}, hypot {length:.2f} → {LENGTH_TOLERANCE} (в 2^−24)")
