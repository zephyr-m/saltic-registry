# Эталон для blake3: BLAKE3 по спецификации (github.com/BLAKE3-team/BLAKE3-specs),
# написан здесь же — в стандартной библиотеке Python BLAKE3 нет. Сначала сверяет
# себя с официальным test_vectors.json (все 35 длин от 0 до 102400, три режима, вывод 131 байт),
# потом пишет registry/libraries/blake3/checks/cases.saltic:
#   OFFICIAL — [длина входа, hash, keyed_hash, derive_key] из официального файла
#     (вход — байты i % 251, ключ KEY, контекст CONTEXT);
#   CASES — [режим, hex входа, hex ключа / контекст / «», hex ответа] от этого
#     эталона: границы блока 64 и чанка 1024, вывод через границу 64, случайные.
#   python3 -I workbench/references/blake3.py <путь к test_vectors.json>
# Файл — из репозитория BLAKE3: github.com/BLAKE3-team/BLAKE3, test_vectors/
# test_vectors.json (sha256 у взятого 24.11.2026: dcb91ea8…db32f624).
import json, os, random, sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "blake3", "checks")
MASK = 0xFFFFFFFF
IV = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8]
CHUNK_START, CHUNK_END, PARENT, ROOT = 1, 2, 4, 8
KEYED_HASH, DERIVE_KEY_CONTEXT, DERIVE_KEY_MATERIAL = 16, 32, 64


def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def g(v, a, b, c, d, x, y):
    v[a] = (v[a] + v[b] + x) & MASK
    v[d] = rotr(v[d] ^ v[a], 16)
    v[c] = (v[c] + v[d]) & MASK
    v[b] = rotr(v[b] ^ v[c], 12)
    v[a] = (v[a] + v[b] + y) & MASK
    v[d] = rotr(v[d] ^ v[a], 8)
    v[c] = (v[c] + v[d]) & MASK
    v[b] = rotr(v[b] ^ v[c], 7)


def compress(cv, block, counter, length, flags):
    m = [int.from_bytes(block[i * 4:i * 4 + 4], "little") for i in range(16)]
    v = list(cv) + IV[:4] + [counter & MASK, counter >> 32, length, flags]
    for r in range(7):
        g(v, 0, 4, 8, 12, m[0], m[1])
        g(v, 1, 5, 9, 13, m[2], m[3])
        g(v, 2, 6, 10, 14, m[4], m[5])
        g(v, 3, 7, 11, 15, m[6], m[7])
        g(v, 0, 5, 10, 15, m[8], m[9])
        g(v, 1, 6, 11, 12, m[10], m[11])
        g(v, 2, 7, 8, 13, m[12], m[13])
        g(v, 3, 4, 9, 14, m[14], m[15])
        if r < 6:
            m = [m[p] for p in PERMUTATION]
    return [v[i] ^ v[i + 8] for i in range(8)] + [v[i + 8] ^ cv[i] for i in range(8)]


def chunk_output(key, chunk, counter, flags):
    """Вершина для чанка: (cv входа, последний блок, счётчик, длина блока, флаги)."""
    cv = key
    blocks = [chunk[i:i + 64] for i in range(0, len(chunk), 64)] or [b""]
    for i, block in enumerate(blocks):
        f = flags | (CHUNK_START if i == 0 else 0)
        if i == len(blocks) - 1:
            return (cv, block.ljust(64, b"\0"), counter, len(block), f | CHUNK_END)
        cv = compress(cv, block, counter, 64, f)[:8]


def chaining(node):
    cv, block, counter, length, flags = node
    return compress(cv, block, counter, length, flags)[:8]


def words_bytes(words):
    return b"".join(w.to_bytes(4, "little") for w in words)


def blake3(data, length=32, key=IV, flags=0):
    chunks = [data[i:i + 1024] for i in range(0, len(data), 1024)] or [b""]
    nodes = [chunk_output(key, c, i, flags) for i, c in enumerate(chunks)]
    # дерево: левое поддерево — наибольшая степень двойки чанков, меньшая всего
    def tree(lo, hi):
        if hi - lo == 1:
            return nodes[lo]
        left = 1
        while left * 2 < hi - lo:
            left *= 2
        block = words_bytes(chaining(tree(lo, lo + left)) + chaining(tree(lo + left, hi)))
        return (key, block, 0, 64, flags | PARENT)
    cv, block, _, size, f = tree(0, len(nodes))
    out = b""
    counter = 0
    while len(out) < length:
        out += words_bytes(compress(cv, block, counter, size, f | ROOT))
        counter += 1
    return out[:length]


def keyed_hash(key, data, length=32):
    return blake3(data, length, [int.from_bytes(key[i * 4:i * 4 + 4], "little") for i in range(8)], KEYED_HASH)


def derive_key(context, material, length=32):
    context_key = blake3(context.encode(), 32, IV, DERIVE_KEY_CONTEXT)
    return blake3(material, length, [int.from_bytes(context_key[i * 4:i * 4 + 4], "little") for i in range(8)], DERIVE_KEY_MATERIAL)


def pattern(n):
    return bytes(i % 251 for i in range(n))


official = json.load(open(sys.argv[1]))
KEY = official["key"].encode()
CONTEXT = official["context_string"]
for case in official["cases"]:
    data = pattern(case["input_len"])
    size = len(case["hash"]) // 2
    mine = [blake3(data, size).hex(), keyed_hash(KEY, data, size).hex(), derive_key(CONTEXT, data, size).hex()]
    if mine != [case["hash"], case["keyed_hash"], case["derive_key"]]:
        sys.exit("эталон расходится с официальным вектором, длина " + str(case["input_len"]))
print(len(official["cases"]), "официальных длин сошлись (по три режима)")

rng = random.Random(2026_11_24)
rows = []
def some(n):
    return bytes(rng.randrange(256) for _ in range(n))
for n in [0, 1, 63, 64, 65, 127, 128, 1023, 1024, 1025, 2047, 2048, 2049, 3072, 4097]:
    data = some(n)
    rows.append(["hash", data.hex(), "", blake3(data).hex()])
for size in [1, 31, 33, 63, 64, 65, 128, 200]:
    data = some(rng.randint(0, 2100))
    rows.append(["hash", data.hex(), "", blake3(data, size).hex()])
for _ in range(6):
    data, key = some(rng.randint(0, 2100)), some(32)
    rows.append(["keyed", data.hex(), key.hex(), keyed_hash(key, data, rng.choice([32, 32, 7, 100])).hex()])
for context in ["", "Saltic 2026-11-24 blake3 checks", "Зэф: ключ сессии"]:
    data = some(rng.randint(0, 2100))
    rows.append(["derive", data.hex(), context, derive_key(context, data, rng.choice([32, 64, 90])).hex()])

lines = ["-- cases — эталоны для blake3 (делает workbench/references/blake3.py, руками не править).", ""]
lines.append('KEY = "' + KEY.decode() + '"')
lines.append('CONTEXT = "' + CONTEXT + '"')
lines.append("OFFICIAL = [")
for i, case in enumerate(official["cases"]):
    tail = "," if i < len(official["cases"]) - 1 else ""
    lines.append('    [{}, "{}", "{}", "{}"]{}'.format(case["input_len"], case["hash"], case["keyed_hash"], case["derive_key"], tail))
lines.append("]")
lines.append("CASES = [")
for i, row in enumerate(rows):
    tail = "," if i < len(rows) - 1 else ""
    lines.append("    [" + ", ".join('"' + v + '"' for v in row) + "]" + tail)
lines.append("]")
with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("\n".join(lines) + "\n")
print(len(rows), "своих случаев")
