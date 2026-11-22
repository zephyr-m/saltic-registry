# Эталоны для sha512: Python hashlib. Векторы FIPS 180-4 и сообщения у границ
# блока (111/112/128 байт) и случайные 0…400 байт. Пишет cases.saltic —
# группу CASES [hex сообщения, ответ].
#   python3 workbench/references/sha512.py
import hashlib, random, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "sha512", "checks")
rng = random.Random(2026_11_22)
messages = [b"", b"abc", b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"]
for n in [111, 112, 127, 128, 129, 239, 240, 256]:
    messages.append(bytes(rng.randrange(256) for _ in range(n)))
for _ in range(25):
    messages.append(bytes(rng.randrange(256) for _ in range(rng.randint(0, 400))))
lines = ["-- cases — эталоны для sha512 (делает workbench/references/sha512.py, руками не править).", "", "CASES = ["]
for i, m in enumerate(messages):
    tail = "," if i < len(messages) - 1 else ""
    lines.append('    ["' + m.hex() + '", "' + hashlib.sha512(m).hexdigest() + '"]' + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(messages), "сообщений")
