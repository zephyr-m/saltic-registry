# Эталоны для pcg: PCG32 (XSH RR, состояние 64 бита) по pcg-random.org и
# эталонной pcg-c (О'Нил): шаг s' = s·6364136223846793005 + inc mod 2^64,
# выход из старого s: xorshifted = ((s >> 18) ^ s) >> 27 (32 бита), поворот
# вправо на s >> 59; засев pcg32_srandom(зерно, поток 54). Опубликованная
# проверка — pcg-c test-high/expected/check-pcg32.out, раунд 1 для
# pcg32_srandom(42, 54). Пишет cases.saltic — CASES [зерно, первые 20 слов] и
# BELOW [зерно, n, первые 10 below(n)].
#   python3 -I workbench/references/pcg.py
import os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "pcg", "checks")
MASK = 0xFFFFFFFF
FULL = (1 << 64) - 1
MULT = 6364136223846793005
STREAM = 54
PUBLISHED = [0xa15c02b7, 0x7b47f409, 0xba1d3330, 0x83d2f293, 0xbfa4784b, 0xcbed606e]


class Pcg32:
    def __init__(self, seed, stream):
        self.inc = ((stream << 1) | 1) & FULL
        self.state = 0
        self.next()
        self.state = (self.state + seed) & FULL
        self.next()

    def next(self):
        old = self.state
        self.state = (old * MULT + self.inc) & FULL
        xorshifted = (((old >> 18) ^ old) >> 27) & MASK
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & MASK


def words(seed, count):
    g = Pcg32(seed, STREAM)
    return [g.next() for _ in range(count)]


def below(seed, n, count):
    g, made = Pcg32(seed, STREAM), []
    threshold = (MASK + 1 - n) % n
    while len(made) < count:
        x = g.next()
        if x >= threshold:
            made.append(x % n)
    return made


assert words(42, 6) == PUBLISHED, "не сходится с опубликованным выводом pcg-c"
SEEDS = [42, 0, 1, 2026, 4294967295, 123456789]
ROWS = [[s] + words(s, 20) for s in SEEDS]
LIMITS = [[1, 1], [42, 6], [2026, 1000], [7, 3000000000], [123456789, 4294967296]]
BELOW = [[s, n] + below(s, n, 10) for s, n in LIMITS]
lines = ["-- cases — эталоны для pcg (делает workbench/references/pcg.py реестра, руками не править):",
         "-- CASES [зерно, первые 20 слов]; BELOW [зерно, n, первые 10 below(n)]; PUBLISHED — pcg-c,",
         "-- check-pcg32.out, раунд 1 для pcg32_srandom(42, 54)", "", "CASES = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(ROWS) - 1 else "") for i, r in enumerate(ROWS)]
lines += ["]", "", "BELOW = ["]
lines += ["    [" + ", ".join(map(str, r)) + "]" + ("," if i < len(BELOW) - 1 else "") for i, r in enumerate(BELOW)]
lines += ["]", "", "PUBLISHED = [" + ", ".join(map(str, PUBLISHED)) + "]"]
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print("pcg:", len(ROWS), "зёрен по 20 слов,", len(BELOW), "строк below; опубликованные 6 слов сошлись")
