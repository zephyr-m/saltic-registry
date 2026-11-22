# Эталоны для random: эталонная реализация xoshiro128** на Си (как у авторов,
# Блэкман и Винья), собранная cc на этой машине, и та же засевка (fmix32 над
# счётчиком золотого сечения). Пишет cases.saltic — группу CASES
# [засев, первые 20 слов].
#   python3 workbench/references/random.py
import os, subprocess, tempfile

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "random", "checks")
SOURCE = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static uint32_t s[4];
static inline uint32_t rotl(const uint32_t x, int k) { return (x << k) | (x >> (32 - k)); }
uint32_t next(void) {
    const uint32_t result = rotl(s[1] * 5, 7) * 9;
    const uint32_t t = s[1] << 9;
    s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3];
    s[2] ^= t;
    s[3] = rotl(s[3], 11);
    return result;
}
static uint32_t mix(uint32_t z) {
    z = (z ^ (z >> 16)) * 0x85ebca6bu;
    z = (z ^ (z >> 13)) * 0xc2b2ae35u;
    return z ^ (z >> 16);
}
int main(int argc, char **argv) {
    uint32_t counter = (uint32_t)strtoul(argv[1], 0, 10);
    for (int i = 0; i < 4; i++) { counter += 0x9e3779b9u; s[i] = mix(counter); }
    for (int i = 0; i < 20; i++) printf("%u%s", next(), i < 19 ? " " : "\n");
    return 0;
}
"""
rows = []
with tempfile.TemporaryDirectory() as folder:
    c = os.path.join(folder, "xoshiro.c")
    binary = os.path.join(folder, "xoshiro")
    open(c, "w").write(SOURCE)
    subprocess.run(["cc", "-O2", "-o", binary, c], check=True)
    for seed in [0, 1, 42, 2026, 4294967295, 123456789]:
        words = subprocess.run([binary, str(seed)], capture_output=True, check=True, text=True).stdout.split()
        rows.append([seed] + [int(w) for w in words])

lines = ["-- cases — эталоны для random от xoshiro128** на Си (делает workbench/references/random.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join(str(v) for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "засевов по 20 слов")
