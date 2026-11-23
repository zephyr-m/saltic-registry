# Эталоны для tcp (свой TCP): сегменты по RFC 9293, 3.1, собранные
# независимо — struct и своя контрольная сумма над псевдозаголовком IPv4.
# Пишет registry/libraries/tcp/checks/cases.saltic — группу CASES:
# [hex сегмента, IP отправителя, IP получателя, порт отправителя, порт получателя,
#  номер, подтверждение, флаги, окно, MSS (0 — нет опции), hex данных].
#   python3 workbench/references/tcp.py
import os
import random
import struct

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "registry", "libraries", "tcp", "checks")
rng = random.Random(2026_11_24)
FIN, SYN, RST, PSH, ACK = 1, 2, 4, 8, 16


def checksum(data):
    if len(data) % 2:
        data += b"\0"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return 0xFFFF - total


def segment(src_ip, dst_ip, sport, dport, seq, ack, flags, window, mss, payload):
    options = struct.pack("!BBH", 2, 4, mss) if mss else b""
    offset = (20 + len(options)) // 4
    head = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, offset << 4, flags, window, 0, 0) + options
    pseudo = bytes(src_ip) + bytes(dst_ip) + struct.pack("!BBH", 0, 6, len(head) + len(payload))
    total = checksum(pseudo + head + payload)
    head = head[:16] + struct.pack("!H", total) + head[18:]
    return head + payload


rows = []


def case(src_ip, dst_ip, sport, dport, seq, ack, flags, window, mss, payload):
    packet = segment(src_ip, dst_ip, sport, dport, seq, ack, flags, window, mss, payload)
    rows.append([packet.hex(), src_ip, dst_ip, sport, dport, seq, ack, flags, window, mss, payload.hex()])


A, B = [10, 0, 0, 1], [10, 0, 0, 2]
case(A, B, 40000, 80, 1000, 0, SYN, 65535, 1460, b"")
case(B, A, 80, 40000, 5000, 1001, SYN | ACK, 65535, 1460, b"")
case(A, B, 40000, 80, 1001, 5001, ACK, 65535, 0, b"")
case(A, B, 40000, 80, 1001, 5001, PSH | ACK, 65535, 0, "привет, сеть".encode())
case(A, B, 40000, 80, 1024, 5001, PSH | ACK, 65535, 0, b"odd")
case(B, A, 80, 40000, 5001, 1027, FIN | ACK, 65535, 0, b"")
case(A, B, 40000, 80, 0, 1001, RST | ACK, 0, 0, b"")
case(A, B, 65535, 1, 4294967295, 4294967294, ACK, 1, 0, b"\xff")
case([192, 168, 1, 77], [93, 184, 216, 34], 51234, 443, 123456789, 987654321, PSH | ACK, 29200, 0, bytes(range(256)))
for _ in range(30):
    src = [rng.randrange(256) for _ in range(4)]
    dst = [rng.randrange(256) for _ in range(4)]
    flags = rng.choice([SYN, SYN | ACK, ACK, PSH | ACK, FIN | ACK, RST])
    mss = rng.randrange(1, 65536) if flags & SYN else 0
    body = b"" if flags & (SYN | RST) else bytes(rng.randrange(256) for _ in range(rng.randint(0, 200)))
    case(src, dst, rng.randrange(1, 65536), rng.randrange(1, 65536), rng.randrange(1 << 32), rng.randrange(1 << 32),
         flags, rng.randrange(65536), mss, body)


def saltic(value):
    if isinstance(value, str):
        return '"%s"' % value
    if isinstance(value, list):
        return "[" + ", ".join(saltic(item) for item in value) + "]"
    return str(value)


with open(os.path.join(HERE, "cases.saltic"), "w") as out:
    out.write("-- cases — сегменты TCP от Python (workbench/references/tcp.py реестра), не править руками:\n")
    out.write("-- [hex сегмента, IP отправителя, IP получателя, порт отправителя, порт получателя,\n")
    out.write("--  номер, подтверждение, флаги, окно, MSS, hex данных]\n\n")
    out.write("CASES = [\n")
    out.write(",\n".join("    " + saltic(row) for row in rows))
    out.write("\n]\n")
print(f"tcp: {len(rows)} сегментов → {os.path.normpath(os.path.join(HERE, 'cases.saltic'))}")
