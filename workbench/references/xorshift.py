# Эталоны для xorshift: xorshift32 Марсальи («Xorshift RNGs», Journal of
# Statistical Software 8(14), 2003) — тройка сдвигов (13, 17, 5): x ^= x << 13;
# x ^= x >> 17; x ^= x << 5 по модулю 2^32, отдаётся новое состояние. Пишет
# cases.saltic — группу CASES [зерно, первые 20 слов] и BELOW [зерно, n,
# первые 10 below(n)].
#   python3 -I workbench/references/xorshift.py
import os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "xorshift", "checks")
MASK = 0xFFFFFFFF


def step(x):
    x ^= (x << 13) & MASK
    x ^= x >> 17
    x ^= (x << 5) & MASK
    return x


def words(seed, count):
    x, made = seed, []
    for _ in range(count):
        x = step(x)
        made.append(x)
    return made


def below(seed, n, count):
    x, made = seed, []
    threshold = (MASK + 1 - n) % n
    while len(made) < count:
        x = step(x)
        if x >= threshold:
            made.append(x % n)
    return made


SEEDS = [1, 42, 2026, 2463534242, 4294967295, 123456789]
ROWS = [[s] + words(s, 20) for s in SEEDS]
LIMITS = [[1, 1], [42, 6], [2026, 1000], [7, 3000000000], [123456789, 4294967296]]
BELOW = [[s, n] + below(s, n, 10) for s, n in LIMITS]
lines = ["-- cases — эталоны для xorshift (делает workbench/references/xorshift.py реестра, руками не править):",
         "-- CASES [зерно, первые 20 слов]; BELOW [зерно, n, первые 10 below(n)]", "", "CASES = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(ROWS) - 1 else "") for i, r in enumerate(ROWS)]
lines += ["]", "", "BELOW = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(BELOW) - 1 else "") for i, r in enumerate(BELOW)]
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print("xorshift:", len(ROWS), "зёрен по 20 слов,", len(BELOW), "строк below")
