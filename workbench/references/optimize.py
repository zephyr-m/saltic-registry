# Эталоны для optimize: своя реализация на Python по формулам — спуск с
# моментом и Adam (Кингма и Ба, алгоритм 1). Одна и та же случайная
# последовательность градиентов, 40 шагов, 3 параметра. Пишет cases.saltic —
# START, GRADS (40 групп по 3), DESCENT_END и ADAM_END (параметры в конце).
#   python3 workbench/references/optimize.py
import math, random, os
from decimal import Decimal

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "optimize", "checks")
rng = random.Random(2026_11_22)
BITS = 50

def held(x):
    if x == 0.0:
        return 0.0
    m, e = math.frexp(x)
    return math.ldexp(round(m * 2 ** BITS), e - BITS)

def lit(x):
    text = format(Decimal(repr(float(x))), "f")
    return text if "." in text else text + ".0"

start = [held(rng.uniform(-5, 5)) for _ in range(3)]
grads = [[held(rng.uniform(-3, 3)) for _ in range(3)] for _ in range(40)]

theta, velocity = start[:], [0.0] * 3
for g in grads:
    velocity = [0.9 * v - 0.1 * gi for v, gi in zip(velocity, g)]
    theta = [t + v for t, v in zip(theta, velocity)]
descent_end = theta

theta, m, s = start[:], [0.0] * 3, [0.0] * 3
b1, b2, eps, rate, p1, p2 = 0.9, 0.999, 1e-8, 0.05, 1.0, 1.0
for g in grads:
    p1 *= b1
    p2 *= b2
    m = [b1 * mi + (1 - b1) * gi for mi, gi in zip(m, g)]
    s = [b2 * si + (1 - b2) * gi * gi for si, gi in zip(s, g)]
    theta = [t - rate * (mi / (1 - p1)) / (math.sqrt(si / (1 - p2)) + eps) for t, mi, si in zip(theta, m, s)]
adam_end = theta

def group(values):
    return "[" + ", ".join(lit(v) for v in values) + "]"

lines = ["-- cases — эталоны для optimize (делает workbench/references/optimize.py, руками не править).", "",
         "START = " + group(start), "DESCENT_END = " + group(descent_end), "ADAM_END = " + group(adam_end), "GRADS = ["]
for i, g in enumerate(grads):
    lines.append("    " + group(g) + ("," if i < len(grads) - 1 else ""))
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print("40 шагов, конец Adam:", [round(v, 6) for v in adam_end])
