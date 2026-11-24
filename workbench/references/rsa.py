# Эталоны для rsa (RFC 8017, SHA-256): своё RSA на Python — pow, кодирование
# EMSA-PKCS1-v1_5 и EMSA-PSS с MGF1 по тексту RFC, ключи из своих простых
# (Миллер — Рабин на random.Random с зерном) — 2048, 1025 (emLen на байт
# короче n), 1024, 256 бит (для ошибок длины). И тест-векторы Wycheproof —
# по ним же проверяется сам эталон: valid → он принимает, invalid → отвергает.
# Пишет в registry/libraries/rsa/checks/:
#   cases.saltic   — KEYS [имя, n, e, d, p, q, dP, dQ, qInv] (hex),
#                    SIGNS [ключ, «pkcs1»|«pss», сообщение, соль, подпись],
#                    VERIFIES [ключ, «pkcs1»|«pss», сообщение, подпись, длина соли, ответ]
#                    ответ — «yes» или имя ошибки Saltic; SIGN_ERRORS [ключ, вид, соль, ошибка]
#   vectors.saltic — Wycheproof: KEYS [n, e], ROWS [ключ, «pkcs1»|«pss»,
#                    сообщение, подпись, длина соли, ответ, tcId]
# Wycheproof (C2SP) скачать в папку и отдать её первым словом:
#   curl -# -fL -o <папка>/rsa_signature_2048_sha256_test.json \
#     https://raw.githubusercontent.com/C2SP/wycheproof/main/testvectors_v1/rsa_signature_2048_sha256_test.json
#   curl -# -fL -o <папка>/rsa_pss_2048_sha256_mgf1_32_test.json \
#     https://raw.githubusercontent.com/C2SP/wycheproof/main/testvectors_v1/rsa_pss_2048_sha256_mgf1_32_test.json
#   python3 -I workbench/references/rsa.py <папка>
import hashlib, json, os, random, sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "rsa", "checks")
PREFIX = bytes([48, 49, 48, 13, 6, 9, 96, 134, 72, 1, 101, 3, 4, 2, 1, 5, 0, 4, 32])
H = 32
rng = random.Random(2026_11_24)


def sha(data):
    return hashlib.sha256(data).digest()


def i2osp(x, size):
    if x >= 256 ** size:
        raise ValueError("integer too large")
    return x.to_bytes(size, "big")


def mgf1(seed, size):
    out = b""
    for counter in range((size + H - 1) // H):
        out += sha(seed + counter.to_bytes(4, "big"))
    return out[:size]


def pkcs1_encode(message, size):
    t = PREFIX + sha(message)
    if size < len(t) + 11:
        raise KeyError("ModulusTooShort")
    return b"\x00\x01" + b"\xff" * (size - len(t) - 3) + b"\x00" + t


def pss_encode(message, salt, bits):
    size = (bits + 7) // 8
    if size < H + len(salt) + 2:
        raise KeyError("SaltTooLong")
    sealed = sha(b"\x00" * 8 + sha(message) + salt)
    db = b"\x00" * (size - len(salt) - H - 2) + b"\x01" + salt
    masked = bytearray(a ^ b for a, b in zip(db, mgf1(sealed, size - H - 1)))
    masked[0] &= 0xFF >> (8 * size - bits)
    return bytes(masked) + sealed + b"\xbc"


def pss_check(message, em, bits, salt_size):
    size = (bits + 7) // 8
    if size < H + salt_size + 2 or em[-1] != 0xBC:
        return False
    masked, sealed = em[:size - H - 1], em[size - H - 1:-1]
    if masked[0] & (0xFF ^ (0xFF >> (8 * size - bits))):
        return False
    db = bytearray(a ^ b for a, b in zip(masked, mgf1(sealed, size - H - 1)))
    db[0] &= 0xFF >> (8 * size - bits)
    border = size - H - salt_size - 2
    if any(db[:border]) or db[border] != 1:
        return False
    salt = bytes(db[len(db) - salt_size:]) if salt_size else b""
    return sha(b"\x00" * 8 + sha(message) + salt) == sealed


def verify(n, e, kind, message, signature, salt_size):
    """RFC 8017, 8.1.2 и 8.2.2 по шагам: «yes» или имя ошибки, как у Saltic."""
    bits = n.bit_length()
    size = (bits + 7) // 8
    if len(signature) != size:
        return "WrongSignatureLength"
    s = int.from_bytes(signature, "big")
    if s >= n:
        return "SignatureOutOfRange"
    m = pow(s, e, n)
    if kind == "pkcs1":
        return "yes" if i2osp(m, size) == pkcs1_encode(message, size) else "SignatureMismatch"
    if m.bit_length() > bits - 1:
        return "SignatureMismatch"
    return "yes" if pss_check(message, i2osp(m, (bits + 6) // 8), bits - 1, salt_size) else "SignatureMismatch"


def sign(key, kind, message, salt):
    n, d = key["n"], key["d"]
    size = (n.bit_length() + 7) // 8
    em = pkcs1_encode(message, size) if kind == "pkcs1" else pss_encode(message, salt, n.bit_length() - 1)
    return i2osp(pow(int.from_bytes(em, "big"), d, n), size)


def prime(bits):
    while True:
        x = rng.getrandbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if x % 65537 == 1:
            continue
        if all(x % p for p in range(3, 2000, 2)) and probable(x):
            return x


def probable(x):
    d, r = x - 1, 0
    while d % 2 == 0:
        d, r = d // 2, r + 1
    for _ in range(40):
        a = pow(rng.randrange(2, x - 1), d, x)
        if a in (1, x - 1):
            continue
        for _ in range(r - 1):
            a = a * a % x
            if a == x - 1:
                break
        else:
            return False
    return True


def key(name, p_bits, q_bits):
    while True:
        p, q = prime(p_bits), prime(q_bits)
        n = p * q
        if p != q and n.bit_length() == p_bits + q_bits:
            break
    e = 65537
    d = pow(e, -1, (p - 1) * (q - 1))
    return {"name": name, "n": n, "e": e, "d": d, "p": p, "q": q, "dp": d % (p - 1), "dq": d % (q - 1), "qinv": pow(q, -1, p)}


def hexed(x):
    text = "%x" % x
    return text if len(text) % 2 == 0 else "0" + text


def write(name, header, blocks):
    lines = ["-- " + name.split(".")[0] + " — " + header + " (делает workbench/references/rsa.py, руками не править).", ""]
    for title, rows in blocks:
        lines.append(title + " = [")
        for i, row in enumerate(rows):
            cells = ['"' + v + '"' if isinstance(v, str) else str(v) for v in row]
            lines.append("    [" + ", ".join(cells) + "]" + ("," if i < len(rows) - 1 else ""))
        lines.append("]")
        lines.append("")
    with open(os.path.join(HERE, name), "w") as out:
        out.write("\n".join(lines))


def own():
    keys = [key("2048", 1024, 1024), key("1025", 513, 512), key("1024", 512, 512), key("256", 128, 128)]
    signs, verifies, errors = [], [], []
    plan = [
        (0, "pkcs1", b"", b""), (0, "pkcs1", "привет, RSA".encode(), b""),
        (0, "pss", b"abc", bytes(rng.randrange(256) for _ in range(32))), (0, "pss", b"", b""),
        (1, "pkcs1", b"edge", b""), (1, "pss", b"edge", bytes(rng.randrange(256) for _ in range(32))),
        (1, "pss", bytes(range(200)), bytes(rng.randrange(256) for _ in range(20))),
        (2, "pkcs1", b"abc", b""), (2, "pss", b"abc", bytes(rng.randrange(256) for _ in range(32))),
        (2, "pss", bytes(rng.randrange(256) for _ in range(300)), bytes(rng.randrange(256) for _ in range(62))),
    ]
    for at, kind, message, salt in plan:
        k = keys[at]
        signature = sign(k, kind, message, salt)
        assert verify(k["n"], k["e"], kind, message, signature, len(salt)) == "yes"
        signs.append([at, kind, message.hex(), salt.hex(), signature.hex()])
        verifies.append([at, kind, message.hex(), signature.hex(), len(salt), "yes"])
        broken = bytearray(signature)
        broken[len(broken) // 2] ^= 1
        verifies.append([at, kind, message.hex(), bytes(broken).hex(), len(salt), verify(k["n"], k["e"], kind, message, bytes(broken), len(salt))])
        verifies.append([at, kind, (message + b"!").hex(), signature.hex(), len(salt), verify(k["n"], k["e"], kind, message + b"!", signature, len(salt))])
        verifies.append([at, kind, message.hex(), signature[1:].hex(), len(salt), "WrongSignatureLength"])
        verifies.append([at, kind, message.hex(), (b"\x00" + signature).hex(), len(salt), "WrongSignatureLength"])
        size = len(signature)
        verifies.append([at, kind, message.hex(), i2osp(k["n"], size).hex(), len(salt), "SignatureOutOfRange"])
        if kind == "pss":
            verifies.append([at, kind, message.hex(), signature.hex(), len(salt) + 1, verify(k["n"], k["e"], kind, message, signature, len(salt) + 1)])
            other = sign(k, "pkcs1", message, b"")
            verifies.append([at, kind, message.hex(), other.hex(), len(salt), verify(k["n"], k["e"], kind, message, other, len(salt))])
    errors.append([3, "pkcs1", "", "ModulusTooShort"])
    errors.append([2, "pss", "00" * 95, "SaltTooLong"])
    errors.append([3, "pss", "", "SaltTooLong"])
    for at, kind, salt, name in errors:
        try:
            sign(keys[at], kind, b"x", bytes.fromhex(salt))
            raise SystemExit("эталон: ждала " + name)
        except KeyError as err:
            assert err.args[0] == name
    rows = [[k["name"]] + [hexed(k[f]) for f in ("n", "e", "d", "p", "q", "dp", "dq", "qinv")] for k in keys]
    write("cases.saltic", "эталоны для rsa: свои ключи и подписи Python", [("KEYS", rows), ("SIGNS", signs), ("VERIFIES", verifies), ("SIGN_ERRORS", errors)])
    return len(signs), len(verifies), len(errors)


def wycheproof(folder):
    files = [("pkcs1", "rsa_signature_2048_sha256_test.json"), ("pss", "rsa_pss_2048_sha256_mgf1_32_test.json")]
    keys, rows = [], []
    for kind, name in files:
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            raise SystemExit("эталон: нет " + path + " — команды curl в шапке")
        data = json.load(open(path))
        for group in data["testGroups"]:
            n = int(group["publicKey"]["modulus"], 16)
            e = int(group["publicKey"]["publicExponent"], 16)
            salt_size = group.get("sLen", 0)
            keys.append([hexed(n), hexed(e)])
            for test in group["tests"]:
                message, signature = bytes.fromhex(test["msg"]), bytes.fromhex(test["sig"])
                answer = verify(n, e, kind, message, signature, salt_size)
                if (answer == "yes") != (test["result"] == "valid"):
                    raise SystemExit("эталон расходится с Wycheproof: %s tcId %d" % (kind, test["tcId"]))
                rows.append([len(keys) - 1, kind, test["msg"], test["sig"], salt_size, answer, test["tcId"]])
    write("vectors.saltic", "тест-векторы Wycheproof (C2SP) rsa_signature_2048_sha256 и rsa_pss_2048_sha256_mgf1_32", [("KEYS", keys), ("ROWS", rows)])
    return len(rows)


if len(sys.argv) < 2:
    raise SystemExit("эталон: нужна папка с JSON Wycheproof — команды curl в шапке")
print("rsa: Wycheproof — %d случаев (эталон с ними согласен)" % wycheproof(sys.argv[1]))
print("rsa: свои ключи — подписей %d, проверок %d, ошибок подписи %d" % own())
