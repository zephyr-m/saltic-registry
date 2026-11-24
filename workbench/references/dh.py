# Эталоны для dh (Диффи–Хеллман на группах ffdhe из RFC 7919): всё считает сам
# Python — его целые произвольной длины точные, pow(g, x, p) — степень по модулю.
# Модуль p каждой группы Python строит не из шестнадцатеричной записи RFC, а по
# формуле RFC 7919 (приложение A): p = 2^b − 2^(b−64) + {[2^(b−130)·e] + X}·2^64 − 1,
# число e — из decimal с запасом точности. Так пакет (у него p из hex RFC)
# сверяется с независимым путём. Числа — десятичным текстом.
# Пишет registry/libraries/dh/checks/cases.saltic:
#   PRIMES — [ширина, p];
#   PAIRS — [ширина, имя, закрытый a, закрытый b, открытый A, открытый B, секрет];
#   BAD_PEERS — [ширина, имя, чужой открытый y] — по RFC 7919 §5.1 нужна ошибка;
#   BAD_PRIVATE — [ширина, имя, закрытый x] — вне 1 < x < p − 1, нужна ошибка.
#   python3 -I workbench/references/dh.py
import os
import random
import sys
from decimal import Decimal, getcontext

sys.set_int_max_str_digits(0)

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "dh", "checks")
rng = random.Random(2026_11_24)
G = 2
GROUPS = {2048: 560316, 3072: 2625351, 4096: 5736041}

getcontext().prec = 1400
E = Decimal(1).exp()


def prime(bits):
    whole = int((Decimal(2) ** (bits - 130)) * E)
    return 2 ** bits - 2 ** (bits - 64) + (whole + GROUPS[bits]) * 2 ** 64 - 1


PRIMES = {bits: prime(bits) for bits in GROUPS}
for bits, p in PRIMES.items():
    assert p.bit_length() == bits
    q = (p - 1) // 2
    assert pow(3, p - 1, p) == 1 and pow(3, q - 1, q) == 1 and pow(G, q, p) == 1, bits

pairs = []


def pair(bits, name, a, b):
    p = PRIMES[bits]
    assert 1 < a < p - 1 and 1 < b < p - 1
    big_a, big_b = pow(G, a, p), pow(G, b, p)
    secret = pow(big_b, a, p)
    assert secret == pow(big_a, b, p)
    pairs.append([bits, name, str(a), str(b), str(big_a), str(big_b), str(secret)])


def short(bits):
    return rng.randrange(2 ** (bits - 1), 2 ** bits)


p2048 = PRIMES[2048]
pair(2048, "ffdhe2048, полные ключи из [2, p − 2]", rng.randrange(2, p2048 - 1), rng.randrange(2, p2048 - 1))
pair(2048, "ffdhe2048, короткие ключи по 256 бит", short(256), short(256))
pair(2048, "ffdhe2048, короткие ключи по 225 бит (наименьшие по RFC)", short(225), short(225))
pair(2048, "ffdhe2048, края: 2 и 3", 2, 3)
pair(3072, "ffdhe3072, короткие ключи по 275 бит", short(275), short(275))
pair(4096, "ffdhe4096, короткие ключи по 325 бит", short(325), short(325))

bad_peers = []
for bits, p in PRIMES.items():
    bad_peers.append([bits, "p − 1", str(p - 1)])
    bad_peers.append([bits, "p", str(p)])
bad_peers += [
    [2048, "0", "0"],
    [2048, "1", "1"],
    [2048, "p + 1", str(p2048 + 1)],
    [2048, "2^2048", str(2 ** 2048)],
    [2048, "p · 3", str(p2048 * 3)],
    [2048, "−2", "-2"],
]

bad_private = [
    [2048, "0", "0"],
    [2048, "1", "1"],
    [2048, "p − 1", str(p2048 - 1)],
    [2048, "p", str(p2048)],
    [2048, "−7", "-7"],
]


def text(row):
    return "[" + ", ".join(str(x) if isinstance(x, int) else '"' + x + '"' for x in row) + "]"


def block(name, rows):
    return name + " = [\n" + ",\n".join("    " + text(r) for r in rows) + "\n]\n"


with open(os.path.join(HERE, "cases.saltic"), "w", encoding="utf-8") as out:
    out.write("-- cases — эталоны Python для dh (workbench/references/dh.py реестра), не править руками:\n")
    out.write("-- PRIMES [ширина, p по формуле RFC 7919]; PAIRS [ширина, имя, a, b, 2^a, 2^b, секрет];\n")
    out.write("-- BAD_PEERS [ширина, имя, чужой открытый]; BAD_PRIVATE [ширина, имя, закрытый]\n\n")
    out.write(block("PRIMES", [[bits, str(p)] for bits, p in PRIMES.items()]))
    out.write("\n" + block("PAIRS", pairs))
    out.write("\n" + block("BAD_PEERS", bad_peers))
    out.write("\n" + block("BAD_PRIVATE", bad_private))
print("dh.py: групп", len(PRIMES), "пар", len(pairs), "плохих открытых", len(bad_peers), "плохих закрытых", len(bad_private))
