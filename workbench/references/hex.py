# Эталоны для hex: Python bytes.hex и bytes.fromhex на случайных буферах
# 0…64 байта (все 256 значений байта встречаются). Пишет
# registry/libraries/hex/checks/cases.saltic — группу CASES: [hex строчными, hex ЗАГЛАВНЫМИ].
#   python3 -I workbench/references/hex.py
import os
import random

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "hex", "checks")
rng = random.Random(2026_11_24)
rows = [[bytes(range(256)).hex(), bytes(range(256)).hex().upper()], ["", ""]]
for _ in range(40):
    data = bytes(rng.randrange(256) for _ in range(rng.randint(1, 64)))
    rows.append([data.hex(), data.hex().upper()])
for low, high in rows:
    assert bytes.fromhex(high).hex() == low
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("-- cases — буферы от Python (workbench/references/hex.py реестра), не править руками:\n")
    out.write("-- [hex строчными, hex ЗАГЛАВНЫМИ]\n\nCASES = [\n")
    out.write(",\n".join('    ["%s", "%s"]' % (low, high) for low, high in rows))
    out.write("\n]\n")
print(f"hex: {len(rows)} буферов")
