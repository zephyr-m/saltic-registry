# Эталоны для chacha: судья — OpenSSL (openssl enc -chacha20 и openssl mac
# POLY1305). Шифр с подписью (RFC 8439, 2.8) собирается из примитивов OpenSSL
# по стандарту. Пишет cases.saltic — группу CASES:
# [«stream», ключ, счётчик, номер, текст, ответ], [«poly», ключ, текст, подпись],
# [«seal», ключ, номер, aad, текст, ответ] — всё в hex.
#   python3 workbench/references/chacha.py
import os, random, subprocess, struct

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "chacha", "checks")
rng = random.Random(2026_11_22)

def raw(n):
    return bytes(rng.randrange(256) for _ in range(n))

def chacha(key, counter, nonce, data):
    iv = struct.pack("<I", counter) + nonce
    return subprocess.run(["openssl", "enc", "-chacha20", "-K", key.hex(), "-iv", iv.hex()], input=data, capture_output=True, check=True).stdout

def poly(key, data):
    out = subprocess.run(["openssl", "mac", "-macopt", "hexkey:" + key.hex(), "POLY1305"], input=data, capture_output=True, check=True).stdout
    return bytes.fromhex(out.decode().strip())

def pad(data):
    return data + b"\0" * (-len(data) % 16)

def seal(key, nonce, aad, text):
    one_time = chacha(key, 0, nonce, b"\0" * 64)[:32]
    cipher = chacha(key, 1, nonce, text)
    tag = poly(one_time, pad(aad) + pad(cipher) + struct.pack("<QQ", len(aad), len(cipher)))
    return cipher + tag

rows = []
rfc_key = bytes(range(32))
rfc_nonce = bytes.fromhex("000000000000004a00000000")
rfc_text = b"Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it."
rows.append(["stream", rfc_key, 1, rfc_nonce, rfc_text, chacha(rfc_key, 1, rfc_nonce, rfc_text)])
for size in [0, 1, 63, 64, 65, 127, 128, 200]:
    key, nonce, counter, text = raw(32), raw(12), rng.randrange(1 << 20), raw(size)
    rows.append(["stream", key, counter, nonce, text, chacha(key, counter, nonce, text)])
poly_key = bytes.fromhex("85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b")
rows.append(["poly", poly_key, b"Cryptographic Forum Research Group", poly(poly_key, b"Cryptographic Forum Research Group")])
for size in [0, 1, 15, 16, 17, 31, 32, 33, 100]:
    key, text = raw(32), raw(size)
    rows.append(["poly", key, text, poly(key, text)])
for size in [0, 1, 16, 64, 114]:
    key, nonce, aad, text = raw(32), raw(12), raw(rng.randint(0, 20)), raw(size)
    rows.append(["seal", key, nonce, aad, text, seal(key, nonce, aad, text)])

def word(v):
    return '"' + v.hex() + '"' if isinstance(v, bytes) else str(v)

lines = ["-- cases — эталоны для chacha от OpenSSL (делает workbench/references/chacha.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append('    ["' + row[0] + '", ' + ", ".join(word(v) for v in row[1:]) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев")
