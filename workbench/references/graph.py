# Эталоны для graph: расстояния — Беллман — Форд (другой алгоритм, без кучи),
# уровни — обход в ширину. Случайные графы 5…40 вершин, ориентированные и
# нет, веса 0…20. Пишет cases.saltic — группу CASES
# [n, ориентирован (1/0), m, рёбра a b w…, начало, расстояния…, уровни…].
#   python3 workbench/references/graph.py
import random, os
from collections import deque

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "graph", "checks")
rng = random.Random(2026_11_22)
FAR = 1000000000000

rows = []
for _ in range(15):
    n = rng.randint(5, 40)
    directed = rng.random() < 0.5
    edges = [(rng.randrange(n), rng.randrange(n), rng.randint(0, 20)) for _ in range(rng.randint(n, 4 * n))]
    full = edges + ([] if directed else [(b, a, w) for a, b, w in edges])
    start = rng.randrange(n)
    dist = [FAR] * n
    dist[start] = 0
    for _ in range(n):
        for a, b, w in full:
            if dist[a] + w < dist[b]:
                dist[b] = dist[a] + w
    level = [-1] * n
    level[start] = 0
    queue = deque([start])
    while queue:
        v = queue.popleft()
        for a, b, w in full:
            if a == v and level[b] < 0:
                level[b] = level[v] + 1
                queue.append(b)
    rows.append([n, 1 if directed else 0, len(edges)] + [x for e in edges for x in e] + [start] + dist + level)

lines = ["-- cases — эталоны для graph (делает workbench/references/graph.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join(str(v) for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "графов")
