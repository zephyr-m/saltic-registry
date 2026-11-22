# Эталоны для ed25519: судья — OpenSSL (openssl pkey и pkeyutl -sign -rawin).
# Сырое 32-байтное зерно заворачивается в DER (префикс RFC 8410). Первый
# случай — тест 2 из RFC 8032 (один байт 72; пустое сообщение OpenSSL
# pkeyutl -rawin подписывать не умеет), дальше случайные. Пишет
# cases.saltic — группу CASES [зерно, открытый ключ, сообщение, подпись] в hex.
#   python3 workbench/references/ed25519.py
import os, random, subprocess, tempfile

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "ed25519", "checks")
rng = random.Random(2026_11_22)
PRIVATE = bytes.fromhex("302e020100300506032b657004220420")

def run(args):
    return subprocess.run(["openssl"] + args, capture_output=True, check=True).stdout

cases = [(bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb"), bytes.fromhex("72"))]
for size in [1, 2, 32, 64, 100, 255]:
    cases.append((bytes(rng.randrange(256) for _ in range(32)), bytes(rng.randrange(256) for _ in range(size))))

# константы кривой в ed25519.saltic — сверить с определением
p = 2 ** 255 - 19
le = lambda v: v.to_bytes(32, "little").hex()
d = (-121665 * pow(121666, p - 2, p)) % p
source = open(os.path.join(HERE, "..", "ed25519.saltic"), encoding="utf-8").read()
for name, value in [("CURVE_D", d), ("TWICE_D", 2 * d % p), ("ROOT_MINUS_ONE", pow(2, (p - 1) // 4, p)), ("ORDER", 2 ** 252 + 27742317777372353535851937790883648493), ("BASE_Y", 4 * pow(5, p - 2, p) % p)]:
    assert f'{name} = "{le(value)}"' in source, name
print("константы кривой сверены с определением")

rows = []
with tempfile.TemporaryDirectory() as folder:
    key = os.path.join(folder, "key.der")
    message = os.path.join(folder, "message.bin")
    for seed, text in cases:
        open(key, "wb").write(PRIVATE + seed)
        open(message, "wb").write(text)
        public = run(["pkey", "-inform", "DER", "-in", key, "-pubout", "-outform", "DER"])[-32:]
        signature = run(["pkeyutl", "-sign", "-rawin", "-keyform", "DER", "-inkey", key, "-in", message])
        rows.append([seed, public, text, signature])

lines = ["-- cases — эталоны для ed25519 от OpenSSL (делает workbench/references/ed25519.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join('"' + v.hex() + '"' for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "случаев; RFC 8032 тест 2:", rows[0][3].hex()[:32], "…")
