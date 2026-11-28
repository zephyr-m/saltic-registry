# Эталоны для binary_search: Python bisect_left / bisect_right и list.index.
# Пустая группа, один элемент, повторы, все равные, случайные целые со знаком
# (тысячи); дробных нет: core.group.slice / add теряют метку дробного (ошибка
# языка, см. паспорт пакета); запросы — каждый элемент, промахи между ними и за
# краями.
# Пишет cases.saltic — группу CASES [n, группа…, m, запросы…, insertion…,
# insertion_after…, index_of… (−1 — ждём Absent)].
#   python3 -I workbench/references/binary_search.py
import bisect, os, random

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "binary_search", "checks")
rng = random.Random(2026_11_24)

def lit(x):
    return str(x)

def queries(items, misses):
    found = list(items) + misses
    rng.shuffle(found)
    return found[:400]

rows = []
def case(items, misses):
    items = sorted(items)
    asked = queries(items, misses)
    left = [bisect.bisect_left(items, q) for q in asked]
    right = [bisect.bisect_right(items, q) for q in asked]
    index = [items.index(q) if q in items else -1 for q in asked]
    rows.append([len(items)] + items + [len(asked)] + asked + left + right + index)

case([], [0, -5, 7])
case([4], [3, 4, 5])
case([1, 2, 2, 2, 3, 5, 5, 8], [0, 4, 6, 9, -1])
case([7] * 50, [6, 8])
ints = [rng.randrange(-100000, 100000, 2) for _ in range(3000)]
case(ints, [v + 1 for v in ints[:200]] + [-100001, 100001])
small = [rng.randint(0, 30) for _ in range(1000)]
case(small, [-1, 31, 100])

lines = ["-- cases — эталоны для binary_search от Python bisect (делает workbench/references/binary_search.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join(lit(v) for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
