# Эталоны для ecdsa: ECDSA на P-256 (FIPS 186-5, SEC 1) с SHA-256 и
# детерминированным nonce RFC 6979 — арифметика кривой на целых Python по
# стандарту. Своя реализация сначала сверяется с RFC 6979 A.2.5 (точные k, r, s
# для «sample» и «test») и со всеми векторами Wycheproof
# ecdsa_secp256r1_sha256_p1363_test.json (подпись r ‖ s по 32 байта), потом
# пишет cases.saltic:
#   SIGNED — [секрет, открытый ключ 04‖X‖Y, сообщение, k, подпись r‖s] в hex
#   VERIFIED — Wycheproof: [номер, ключ, сообщение, подпись, «yes»/«no»/«BadSignature»]
#   POINTS — точки, которые не точки: [hex, почему] → BadPoint
#   SECRETS — негодные секреты → BadSecret
# Файл Wycheproof (C2SP/wycheproof, testvectors_v1) — первым аргументом:
#   curl -# -fLO https://raw.githubusercontent.com/C2SP/wycheproof/main/testvectors_v1/ecdsa_secp256r1_sha256_p1363_test.json
#   python3 -I workbench/references/ecdsa.py ecdsa_secp256r1_sha256_p1363_test.json
import hashlib, hmac, json, os, random, sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "ecdsa", "checks")
rng = random.Random(2026_11_24)

P = 2 ** 256 - 2 ** 224 + 2 ** 192 + 2 ** 96 - 1
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
G = (0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
     0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5)

def on_curve(point):
    x, y = point
    return (y * y - (x * x * x + A * x + B)) % P == 0

def add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    if p[0] == q[0] and (p[1] + q[1]) % P == 0:
        return None
    if p == q:
        slope = (3 * p[0] * p[0] + A) * pow(2 * p[1], P - 2, P) % P
    else:
        slope = (q[1] - p[1]) * pow(q[0] - p[0], P - 2, P) % P
    x = (slope * slope - p[0] - q[0]) % P
    return (x, (slope * (p[0] - x) - p[1]) % P)

def times(k, point):
    result = None
    for bit in bin(k)[2:]:
        result = add(result, result)
        if bit == "1":
            result = add(result, point)
    return result

def be(value, size=32):
    return value.to_bytes(size, "big")

def encode(point):
    return b"\x04" + be(point[0]) + be(point[1])

def decode(raw):
    if len(raw) != 65 or raw[0] != 4:
        raise ValueError("BadPoint")
    point = (int.from_bytes(raw[1:33], "big"), int.from_bytes(raw[33:], "big"))
    if point[0] >= P or point[1] >= P or on_curve(point) == False:
        raise ValueError("BadPoint")
    return point

def nonce(secret, digest):
    # RFC 6979 3.2: qlen = hlen = 256, bits2octets — z mod q
    k_key, v = b"\x00" * 32, b"\x01" * 32
    material = be(secret) + be(int.from_bytes(digest, "big") % N)
    k_key = hmac.new(k_key, v + b"\x00" + material, hashlib.sha256).digest()
    v = hmac.new(k_key, v, hashlib.sha256).digest()
    k_key = hmac.new(k_key, v + b"\x01" + material, hashlib.sha256).digest()
    v = hmac.new(k_key, v, hashlib.sha256).digest()
    while True:
        v = hmac.new(k_key, v, hashlib.sha256).digest()
        k = int.from_bytes(v, "big")
        if 1 <= k < N:
            yield k
        k_key = hmac.new(k_key, v + b"\x00", hashlib.sha256).digest()
        v = hmac.new(k_key, v, hashlib.sha256).digest()

def sign(secret, message):
    digest = hashlib.sha256(message).digest()
    e = int.from_bytes(digest, "big")
    for k in nonce(secret, digest):
        r = times(k, G)[0] % N
        s = pow(k, N - 2, N) * (e + r * secret) % N
        if r > 0 and s > 0:
            return k, be(r) + be(s)

def parts(signature):
    if len(signature) != 64:
        raise ValueError("BadSignature")
    r, s = int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")
    if r == 0 or s == 0 or r >= N or s >= N:
        raise ValueError("BadSignature")
    return r, s

def verify(public, message, signature):
    point = decode(public)
    r, s = parts(signature)
    e = int.from_bytes(hashlib.sha256(message).digest(), "big")
    w = pow(s, N - 2, N)
    total = add(times(e * w % N, G), times(r * w % N, point))
    return total is not None and total[0] % N == r

# RFC 6979 A.2.5 — точные k, r, s
SECRET = 0xC9AFA9D845BA75166B5C215767B1D6934E50C3DB36E89B127B8A622B120F6721
assert times(SECRET, G) == (0x60FED4BA255A9D31C961EB74C6356D68C049B8923B61FA6CE669622E60F29FB6,
                            0x7903FE1008B8BC99A41AE9E95628BC64F2F1B20C2D7E9F5177A3C294D4462299)
RFC = [(b"sample", 0xA6E3C57DD01ABE90086538398355DD4C3B17AA873382B0F24D6129493D8AAD60,
        "efd48b2aacb6a8fd1140dd9cd45e81d69d2c877b56aaf991c34d0ea84eaf3716f7cb1c942d657c41d436c7a1b6e29f65f3e900dbb9aff4064dc4ab2f843acda8"),
       (b"test", 0xD16B6AE827F17175E040871A1C7EC3500192C4C92677336EC2537ACAEE0008E0,
        "f1abb023518351cd71d881567b1ea663ed3efcf6c5132b354f28d3b0b7d38367019f4113742a2b14bd25926b49c649155f267e60d3814b4c0cc84250e46f0083")]
signed = []
for message, k, signature in RFC:
    assert sign(SECRET, message) == (k, bytes.fromhex(signature)), message
    signed.append((SECRET, message))
print("RFC 6979 A.2.5: k, r, s сошлись")
for size in [0, 1, 3, 32, 64, 100]:
    signed.append((rng.randrange(1, N), bytes(rng.randrange(256) for _ in range(size))))
signed.append((1, b"one"))
signed.append((N - 1, b"last"))

verified = []
for group in json.load(open(sys.argv[1]))["testGroups"]:
    public = bytes.fromhex(group["publicKey"]["uncompressed"])
    for test in group["tests"]:
        message, signature = bytes.fromhex(test["msg"]), bytes.fromhex(test["sig"])
        try:
            parts(signature)
            verdict = "yes" if verify(public, message, signature) else "no"
        except ValueError as fault:
            verdict = str(fault)
        assert (verdict == "yes") == (test["result"] == "valid"), test["tcId"]
        verified.append([str(test["tcId"]), public.hex(), message.hex(), signature.hex(), verdict])
print(f"Wycheproof: {len(verified)} векторов сошлись со своей проверкой")

good = encode(times(SECRET, G))
flipped = bytearray(good)
flipped[64] ^= 1
points = [(bytes(flipped).hex(), "y испорчен — не на кривой"),
          ("04" + be(P).hex() + good[33:].hex(), "x = p"),
          ("04" + good[1:33].hex() + be(P).hex(), "y = p"),
          ("04" + be(0).hex() + be(0).hex(), "бесконечность (0, 0) — не точка"),
          ("02" + good[1:].hex(), "не 04 впереди"),
          (good[:64].hex(), "64 байта, не 65"),
          (good.hex() + "00", "66 байт")]
for raw, why in points:
    try:
        decode(bytes.fromhex(raw))
        raise SystemExit("точка прошла: " + why)
    except ValueError:
        pass
secrets = [be(0).hex(), be(N).hex(), be(2 ** 256 - 1).hex(), be(1, 31).hex()]

def text(row):
    return "[" + ", ".join(f'"{cell}"' for cell in row) + "]"

lines = ["-- cases — эталоны для ecdsa: RFC 6979 A.2.5, Wycheproof и Python по стандарту",
         "-- (делает workbench/references/ecdsa.py, руками не править).", "", "SIGNED = ["]
rows = []
for secret, message in signed:
    k, signature = sign(secret, message)
    rows.append("    " + text([be(secret).hex(), encode(times(secret, G)).hex(), message.hex(), be(k).hex(), signature.hex()]))
lines += [",\n".join(rows), "]", "", "VERIFIED = ["]
lines += [",\n".join("    " + text(row) for row in verified), "]", "", "POINTS = ["]
lines += [",\n".join("    " + text(row) for row in points), "]", "", "SECRETS = ["]
lines += [",\n".join("    " + text([row]) for row in secrets), "]"]
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(f"записано: {len(signed)} подписей, {len(verified)} проверок, {len(points)} точек, {len(secrets)} секретов")
