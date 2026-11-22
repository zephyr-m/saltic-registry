# Эталоны для sha256: Python hashlib и hmac. Векторы FIPS 180-4 и RFC 4231 и
# случайные сообщения 0…300 байт (вокруг границ блока 55/56/64 — обязательно).
# Пишет cases.saltic — группу CASES:
# [«digest», hex сообщения, ответ] и [«hmac», hex ключа, hex сообщения, ответ].
#   python3 workbench/references/sha256.py
import hashlib, hmac, random, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "sha256", "checks")
rng = random.Random(2026_11_22)

rows = []
def digest(data):
    rows.append(["digest", data.hex(), hashlib.sha256(data).hexdigest()])
def mac(key, data):
    rows.append(["hmac", key.hex(), data.hex(), hmac.new(key, data, hashlib.sha256).hexdigest()])

digest(b"")
digest(b"abc")
digest(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")
digest(b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu")
for n in [55, 56, 63, 64, 65, 119, 120, 128]:
    digest(bytes(rng.randrange(256) for _ in range(n)))
for _ in range(40):
    digest(bytes(rng.randrange(256) for _ in range(rng.randint(0, 300))))
mac(b"\x0b" * 20, b"Hi There")
mac(b"Jefe", b"what do ya want for nothing?")
mac(b"\xaa" * 20, b"\xdd" * 50)
mac(bytes(range(1, 26)), b"\xcd" * 50)
mac(b"\xaa" * 131, b"Test Using Larger Than Block-Size Key - Hash Key First")
mac(b"\xaa" * 131, b"This is a test using a larger than block-size key and a larger than block-size data. The key needs to be hashed before being used by the HMAC algorithm.")
for _ in range(10):
    mac(bytes(rng.randrange(256) for _ in range(rng.randint(0, 100))), bytes(rng.randrange(256) for _ in range(rng.randint(0, 200))))

lines = ["-- cases — эталоны для sha256 (делает workbench/references/sha256.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join('"' + v + '"' for v in row) + "]" + tail)
lines.append("]")
lines.append("")
lines.append('MILLION_A = "' + hashlib.sha256(b"a" * 1000000).hexdigest() + '"')
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
