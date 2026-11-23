# Эталоны для wire: контрольная сумма интернета (RFC 1071) — пример из самого
# RFC 1071 (раздел 3) и случайные буферы 0…300 байт (чётные и нечётные), плюс
# числа 16 и 32 бита struct «!H» / «!I». Пишет registry/libraries/wire/checks/cases.saltic:
# SUMS — [hex буфера, контрольная сумма]; NUMBERS — [hex 4 байтов, слово с 0, длинное].
#   python3 -I workbench/references/wire.py
import os
import random
import struct

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "wire", "checks")
rng = random.Random(2026_11_24)


def checksum(data):
    if len(data) % 2:
        data += b"\0"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return 0xFFFF - total


sums = [bytes.fromhex("0001f203f4f5f6f7"), b"", b"\xff", b"\xff\xff" * 1000]
for _ in range(40):
    sums.append(bytes(rng.randrange(256) for _ in range(rng.randint(0, 300))))
assert checksum(bytes.fromhex("0001f203f4f5f6f7")) == 0xFFFF - 0xDDF2   # RFC 1071, 3: сумма ddf2
numbers = [bytes.fromhex("00000000"), bytes.fromhex("ffffffff"), bytes.fromhex("12345678")]
numbers += [bytes(rng.randrange(256) for _ in range(4)) for _ in range(20)]
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("-- cases — эталоны от Python (workbench/references/wire.py реестра), не править руками:\n")
    out.write("-- SUMS — [hex буфера, контрольная сумма]; NUMBERS — [hex 4 байтов, слово, длинное]\n\n")
    out.write("SUMS = [\n" + ",\n".join('    ["%s", %d]' % (data.hex(), checksum(data)) for data in sums) + "\n]\n\n")
    out.write("NUMBERS = [\n" + ",\n".join('    ["%s", %d, %d]' % (data.hex(), struct.unpack("!H", data[:2])[0], struct.unpack("!I", data)[0]) for data in numbers) + "\n]\n")
print(f"wire: сумм {len(sums)}, чисел {len(numbers)}")
