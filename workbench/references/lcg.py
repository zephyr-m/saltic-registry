# Эталоны для lcg: линейный конгруэнтный генератор «quick and dirty» из
# Numerical Recipes in C, 2-е изд., §7.1 (Press и др., 1992): x' = (1664525·x +
# 1013904223) mod 2^32, отдаётся новое состояние. Опубликованная проверка —
# 11 слов от x = 0 из текста книги (3C6EF35F, 47502932, … CBF633B1). Пишет cases.saltic —
# группу CASES [зерно, первые 20 слов] и BELOW [зерно, n, первые 10 below(n)].
#   python3 -I workbench/references/lcg.py
import os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "lcg", "checks")
MASK = 0xFFFFFFFF


def words(seed, count):
    x, made = seed, []
    for _ in range(count):
        x = (1664525 * x + 1013904223) & MASK
        made.append(x)
    return made


def below(seed, n, count):
    x, made = seed, []
    threshold = (MASK + 1 - n) % n
    while len(made) < count:
        x = (1664525 * x + 1013904223) & MASK
        if x >= threshold:
            made.append(x % n)
    return made


PUBLISHED = [0x3C6EF35F, 0x47502932, 0xD1CCF6E9, 0xAAF95334, 0x6252E503, 0x9F2EC686, 0x57FE6C2D,
             0xA3D95FA8, 0x81FDBEE7, 0x94F0AF1A, 0xCBF633B1]
assert words(0, 11) == PUBLISHED, "не сходится с Numerical Recipes"
SEEDS = [0, 1, 42, 2026, 4294967295, 123456789]
ROWS = [[s] + words(s, 20) for s in SEEDS]
LIMITS = [[1, 1], [42, 6], [2026, 1000], [7, 3000000000], [123456789, 4294967296]]
BELOW = [[s, n] + below(s, n, 10) for s, n in LIMITS]
lines = ["-- cases — эталоны для lcg (делает workbench/references/lcg.py реестра, руками не править):",
         "-- CASES [зерно, первые 20 слов]; BELOW [зерно, n, первые 10 below(n)]", "", "CASES = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(ROWS) - 1 else "") for i, r in enumerate(ROWS)]
lines += ["]", "", "BELOW = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(BELOW) - 1 else "") for i, r in enumerate(BELOW)]
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print("lcg:", len(ROWS), "зёрен по 20 слов,", len(BELOW), "строк below")
