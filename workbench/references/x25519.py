# Эталоны для x25519: судья — OpenSSL (openssl pkey и pkeyutl -derive). Сырой
# 32-байтный ключ заворачивается в DER (префиксы RFC 8410). Пары: Алиса и Боб
# из RFC 7748 (6.1) и случайные. Пишет cases.saltic — группу CASES
# [секрет a, открытый a, секрет b, открытый b, общий] в hex.
#   python3 workbench/references/x25519.py
import os, random, subprocess, tempfile

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "x25519", "checks")
rng = random.Random(2026_11_22)
PRIVATE = bytes.fromhex("302e020100300506032b656e04220420")
PUBLIC = bytes.fromhex("302a300506032b656e032100")

def run(args, data=b""):
    return subprocess.run(["openssl"] + args, input=data, capture_output=True, check=True).stdout

def public(secret, folder):
    path = os.path.join(folder, "secret.der")
    open(path, "wb").write(PRIVATE + secret)
    return run(["pkey", "-inform", "DER", "-in", path, "-pubout", "-outform", "DER"])[-32:]

def shared(secret, peer, folder):
    mine = os.path.join(folder, "mine.der")
    theirs = os.path.join(folder, "theirs.der")
    open(mine, "wb").write(PRIVATE + secret)
    open(theirs, "wb").write(PUBLIC + peer)
    return run(["pkeyutl", "-derive", "-keyform", "DER", "-inkey", mine, "-peerform", "DER", "-peerkey", theirs])

pairs = [(bytes.fromhex("77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a"), bytes.fromhex("5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb"))]
for _ in range(6):
    pairs.append((bytes(rng.randrange(256) for _ in range(32)), bytes(rng.randrange(256) for _ in range(32))))

rows = []
with tempfile.TemporaryDirectory() as folder:
    for a, b in pairs:
        pa, pb = public(a, folder), public(b, folder)
        s = shared(a, pb, folder)
        assert s == shared(b, pa, folder)
        rows.append([a, pa, b, pb, s])

lines = ["-- cases — эталоны для x25519 от OpenSSL (делает workbench/references/x25519.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join('"' + v.hex() + '"' for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "пар; Алиса и Боб:", rows[0][4].hex())
