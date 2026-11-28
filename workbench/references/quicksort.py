# Эталоны для quicksort: Python sorted (и reverse=True). Пустая, один
# элемент, повторы, уже отсортированная, обратная (и по 3000 — проверка
# опорного медианой трёх), все равные, случайные
# целые со знаком (тысячи). Дробных нет: core.group.slice / add теряют метку
# дробного (ошибка языка, см. паспорт пакета). Пишет cases.saltic — группу CASES
# [rising, n, данные…, ожидаемое…].
#   python3 -I workbench/references/quicksort.py
import os, random

NAME = "quicksort"
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", NAME, "checks")
rng = random.Random(2026_11_24)

def lit(x):
    if isinstance(x, bool):
        return "yes" if x else "no"
    return str(x)

sets = [
    [], [5], [3, 1, 3, 2, 1, 3, 2, 2],
    list(range(60)), list(range(60, 0, -1)), [4] * 40,
    list(range(3000)), list(range(3000, 0, -1)),
    [rng.randint(-1000, 1000) for _ in range(300)],
    [rng.randint(0, 50) for _ in range(1500)],
    [rng.randint(-10 ** 9, 10 ** 9) for _ in range(2000)],
]
rows = []
for data in sets:
    for rising in (True, False):
        rows.append([rising, len(data)] + data + sorted(data, reverse=not rising))

lines = ["-- cases — эталоны для " + NAME + " от Python sorted (делает workbench/references/" + NAME + ".py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join(lit(v) for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
