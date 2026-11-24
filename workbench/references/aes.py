# Эталоны для aes: свой AES по FIPS 197 (в стандартной библиотеке Python AES
# нет), CTR по NIST SP 800-38A и GCM по NIST SP 800-38D. Прежде чем писать
# случаи, эталон сверяется с опубликованными векторами: FIPS 197 (приложения
# B, C.1, C.3), SP 800-38A F.5.1 и F.5.5 (CTR-AES128 и CTR-AES256), тест-кейсы
# GCM 1–6 и 13–18 McGrew–Viega; не сошлось — падает, cases.saltic не пишется.
# Пишет registry/libraries/aes/checks/cases.saltic — группу CASES (всё в hex):
# [«block», ключ, текст, шифр], [«ctr», ключ, счётчик, текст, ответ],
# [«gcm», ключ, номер, aad, текст, шифр с тегом].
#   python3 -I workbench/references/aes.py
import os
import random

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "aes", "checks")
rng = random.Random(2026_11_24)


def times(a, b):
    made = 0
    while b:
        if b & 1:
            made ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        b >>= 1
    return made


def inverse(a):
    if a == 0:
        return 0
    for b in range(1, 256):
        if times(a, b) == 1:
            return b


def affine(b):
    made = 0x63
    for i in range(8):
        bit = (b >> i ^ b >> (i + 4) % 8 ^ b >> (i + 5) % 8 ^ b >> (i + 6) % 8 ^ b >> (i + 7) % 8) & 1
        made ^= bit << i
    return made


SBOX = [affine(inverse(x)) for x in range(256)]
UNBOX = [SBOX.index(x) for x in range(256)]


def schedule(key):
    nk = len(key) // 4
    rounds = nk + 6
    words = [list(key[4 * i:4 * i + 4]) for i in range(nk)]
    rcon = 1
    for i in range(nk, 4 * (rounds + 1)):
        temp = list(words[i - 1])
        if i % nk == 0:
            temp = [SBOX[b] for b in temp[1:] + temp[:1]]
            temp[0] ^= rcon
            rcon = times(rcon, 2)
        elif nk > 6 and i % nk == 4:
            temp = [SBOX[b] for b in temp]
        words.append([a ^ b for a, b in zip(words[i - nk], temp)])
    return [sum(words[4 * r:4 * r + 4], []) for r in range(rounds + 1)]


def mix(state, row):
    made = []
    for c in range(4):
        col = state[4 * c:4 * c + 4]
        for r in range(4):
            made.append(times(row[0], col[r]) ^ times(row[1], col[(r + 1) % 4]) ^ times(row[2], col[(r + 2) % 4]) ^ times(row[3], col[(r + 3) % 4]))
    return made


def shift(state, step):
    return [state[r + 4 * ((c + step * r) % 4)] for c in range(4) for r in range(4)]


def encrypt(key, block):
    keys = schedule(key)
    state = [a ^ b for a, b in zip(block, keys[0])]
    for r in range(1, len(keys)):
        state = shift([SBOX[b] for b in state], 1)
        if r < len(keys) - 1:
            state = mix(state, [2, 3, 1, 1])
        state = [a ^ b for a, b in zip(state, keys[r])]
    return bytes(state)


def decrypt(key, block):
    keys = schedule(key)
    state = [a ^ b for a, b in zip(block, keys[-1])]
    for r in range(len(keys) - 2, -1, -1):
        state = [UNBOX[b] for b in shift(state, 3)]
        state = [a ^ b for a, b in zip(state, keys[r])]
        if r > 0:
            state = mix(state, [14, 11, 13, 9])
    return bytes(state)


def ctr(key, counter, data, width=16):
    made = b""
    value = int.from_bytes(counter, "big")
    for at in range(0, len(data), 16):
        pad = encrypt(key, value.to_bytes(16, "big"))
        made += bytes(a ^ b for a, b in zip(data[at:at + 16], pad))
        low = (value + 1) % (1 << (8 * width))
        value = (value >> (8 * width) << (8 * width)) | low
    return made


def gf(x, y):
    z, v = 0, y
    for i in range(127, -1, -1):
        if x >> i & 1:
            z ^= v
        v = (v >> 1) ^ (0xE1 << 120) if v & 1 else v >> 1
    return z


def ghash(h, aad, cipher):
    y, hn = 0, int.from_bytes(h, "big")
    pad = lambda d: d + b"\0" * (-len(d) % 16)
    data = pad(aad) + pad(cipher) + (8 * len(aad)).to_bytes(8, "big") + (8 * len(cipher)).to_bytes(8, "big")
    for at in range(0, len(data), 16):
        y = gf(y ^ int.from_bytes(data[at:at + 16], "big"), hn)
    return y.to_bytes(16, "big")


def gcm(key, nonce, aad, text):
    h = encrypt(key, bytes(16))
    j0 = nonce + b"\0\0\0\1" if len(nonce) == 12 else ghash(h, b"", nonce)
    first = (int.from_bytes(j0, "big") & ~0xFFFFFFFF) | ((int.from_bytes(j0[12:], "big") + 1) & 0xFFFFFFFF)
    cipher = ctr(key, first.to_bytes(16, "big"), text, 4)
    tag = bytes(a ^ b for a, b in zip(encrypt(key, j0), ghash(h, aad, cipher)))
    return cipher + tag


def check(name, got, want):
    if got.hex() != want:
        raise SystemExit("эталон не сошёлся с опубликованным вектором: " + name + "\n  есть  " + got.hex() + "\n  нужно " + want)


x = bytes.fromhex
check("FIPS 197 B", encrypt(x("2b7e151628aed2a6abf7158809cf4f3c"), x("3243f6a8885a308d313198a2e0370734")), "3925841d02dc09fbdc118597196a0b32")
check("FIPS 197 C.1", encrypt(bytes(range(16)), x("00112233445566778899aabbccddeeff")), "69c4e0d86a7b0430d8cdb78070b4c55a")
check("FIPS 197 C.3", encrypt(bytes(range(32)), x("00112233445566778899aabbccddeeff")), "8ea2b7ca516745bfeafc49904b496089")
check("FIPS 197 C.1 обратно", decrypt(bytes(range(16)), x("69c4e0d86a7b0430d8cdb78070b4c55a")), "00112233445566778899aabbccddeeff")
check("FIPS 197 C.3 обратно", decrypt(bytes(range(32)), x("8ea2b7ca516745bfeafc49904b496089")), "00112233445566778899aabbccddeeff")
SP_TEXT = x("6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710")
SP_COUNTER = x("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
SP_KEY128 = x("2b7e151628aed2a6abf7158809cf4f3c")
SP_KEY256 = x("603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4")
check("SP 800-38A F.5.1", ctr(SP_KEY128, SP_COUNTER, SP_TEXT), "874d6191b620e3261bef6864990db6ce9806f66b7970fdff8617187bb9fffdff5ae4df3edbd5d35e5b4f09020db03eab1e031dda2fbe03d1792170a0f3009cee")
check("SP 800-38A F.5.5", ctr(SP_KEY256, SP_COUNTER, SP_TEXT), "601ec313775789a5b7a7f504bbf3d228f443e3ca4d62b59aca84e990cacaf5c52b0930daa23de94ce87017ba2d84988ddfc9c58db67aada613c2dd08457941a6")
GK = x("feffe9928665731c6d6a8f9467308308")
GP = x("d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a721c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b391aafd255")
GA = x("feedfacedeadbeeffeedfacedeadbeefabaddad2")
GIV = x("cafebabefacedbaddecaf888")
GIV8 = x("cafebabefacedbad")
GIV60 = x("9313225df88406e555909c5aff5269aa6a7a9538534f7da1e4c303d2a318a728c3c0c95156809539fcf0e2429a6b525416aedbf5a0de6a57a637b39b")
GCM_VECTORS = [
    ["GCM 1", bytes(16), bytes(12), b"", b"", "58e2fccefa7e3061367f1d57a4e7455a"],
    ["GCM 2", bytes(16), bytes(12), b"", bytes(16), "0388dace60b6a392f328c2b971b2fe78ab6e47d42cec13bdf53a67b21257bddf"],
    ["GCM 3", GK, GIV, b"", GP, "42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e091473f59854d5c2af327cd64a62cf35abd2ba6fab4"],
    ["GCM 4", GK, GIV, GA, GP[:60], "42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e0915bc94fbc3221a5db94fae95ae7121a47"],
    ["GCM 5", GK, GIV8, GA, GP[:60], "61353b4c2806934a777ff51fa22a4755699b2a714fcdc6f83766e5f97b6c742373806900e49f24b22b097544d4896b424989b5e1ebac0f07c23f45983612d2e79e3b0785561be14aaca2fccb"],
    ["GCM 6", GK, GIV60, GA, GP[:60], "8ce24998625615b603a033aca13fb894be9112a5c3a211a8ba262a3cca7e2ca701e4a9a4fba43c90ccdcb281d48c7c6fd62875d2aca417034c34aee5619cc5aefffe0bfa462af43c1699d050"],
    ["GCM 13", bytes(32), bytes(12), b"", b"", "530f8afbc74536b9a963b4f1c4cb738b"],
    ["GCM 14", bytes(32), bytes(12), b"", bytes(16), "cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919"],
    ["GCM 15", GK + GK, GIV, b"", GP, "522dc1f099567d07f47f37a32a84427d643a8cdcbfe5c0c97598a2bd2555d1aa8cb08e48590dbb3da7b08b1056828838c5f61e6393ba7a0abcc9f662898015adb094dac5d93471bdec1a502270e3cc6c"],
    ["GCM 16", GK + GK, GIV, GA, GP[:60], "522dc1f099567d07f47f37a32a84427d643a8cdcbfe5c0c97598a2bd2555d1aa8cb08e48590dbb3da7b08b1056828838c5f61e6393ba7a0abcc9f66276fc6ece0f4e1768cddf8853bb2d551b"],
    ["GCM 17", GK + GK, GIV8, GA, GP[:60], "c3762df1ca787d32ae47c13bf19844cbaf1ae14d0b976afac52ff7d79bba9de0feb582d33934a4f0954cc2363bc73f7862ac430e64abe499f47c9b1f3a337dbf46a792c45e454913fe2ea8f2"],
    ["GCM 18", GK + GK, GIV60, GA, GP[:60], "5a8def2f0c9e53f1f75d7853659e2a20eeb2b22aafde6419a058ab4f6f746bf40fc0c3b780f244452da3ebf1c5d82cdea2418997200ef82e44ae7e3fa44a8266ee1c8eb0c8b5d4cf5ae9f19a"],
]
for name, key, nonce, aad, text, want in GCM_VECTORS:
    check(name, gcm(key, nonce, aad, text), want)

rows = []
rows.append(["block", x("2b7e151628aed2a6abf7158809cf4f3c"), x("3243f6a8885a308d313198a2e0370734"), x("3925841d02dc09fbdc118597196a0b32")])
rows.append(["block", bytes(range(16)), x("00112233445566778899aabbccddeeff"), x("69c4e0d86a7b0430d8cdb78070b4c55a")])
rows.append(["block", bytes(range(32)), x("00112233445566778899aabbccddeeff"), x("8ea2b7ca516745bfeafc49904b496089")])
for size in [16, 32, 16, 32, 16, 32]:
    key, text = rng.randbytes(size), rng.randbytes(16)
    rows.append(["block", key, text, encrypt(key, text)])
rows.append(["ctr", SP_KEY128, SP_COUNTER, SP_TEXT, ctr(SP_KEY128, SP_COUNTER, SP_TEXT)])
rows.append(["ctr", SP_KEY256, SP_COUNTER, SP_TEXT, ctr(SP_KEY256, SP_COUNTER, SP_TEXT)])
wrap = x("ffffffffffffffffffffffffffffffff")
rows.append(["ctr", SP_KEY128, wrap, SP_TEXT[:40], ctr(SP_KEY128, wrap, SP_TEXT[:40])])
for size in [0, 1, 15, 16, 17, 33, 100]:
    key, counter, text = rng.randbytes(rng.choice([16, 32])), rng.randbytes(16), rng.randbytes(size)
    rows.append(["ctr", key, counter, text, ctr(key, counter, text)])
for name, key, nonce, aad, text, want in GCM_VECTORS:
    rows.append(["gcm", key, nonce, aad, text, x(want)])
for size in [0, 1, 15, 16, 17, 31, 64, 77]:
    key = rng.randbytes(rng.choice([16, 32]))
    nonce = rng.randbytes(rng.choice([12, 12, 12, 1, 16, 20]))
    aad, text = rng.randbytes(rng.randint(0, 40)), rng.randbytes(size)
    rows.append(["gcm", key, nonce, aad, text, gcm(key, nonce, aad, text)])


def word(v):
    return '"' + v.hex() + '"'


lines = ["-- cases — эталоны для aes от своего AES на Python, сверенного с FIPS 197, SP 800-38A и векторами GCM (делает workbench/references/aes.py, руками не править).", "", "CASES = ["]
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append('    ["' + row[0] + '", ' + ", ".join(word(v) for v in row[1:]) + "]" + tail)
lines.append("]")
os.makedirs(HERE, exist_ok=True)
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print("эталон сошёлся с опубликованными векторами: FIPS 197 — 5, SP 800-38A — 2, GCM — " + str(len(GCM_VECTORS)))
print(len(rows), "случаев")
