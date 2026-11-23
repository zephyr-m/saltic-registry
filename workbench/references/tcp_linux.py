# Эталон для tcp_linux (мост к TCP Linux): эхо-сервер на сокетах Python. Слушает 127.0.0.1 на
# свободном порту, первой строкой печатает порт. Каждое соединение — эхо:
# что пришло, то и отправил назад; пришло «BYE» — отвечает «пока» и закрывает.
# Живёт, пока открыт ввод: проверка закрывает ввод — сервер выходит.
#   python3 workbench/references/tcp_linux.py
import socket
import sys
import threading


def serve(conn):
    with conn:
        while True:
            data = conn.recv(65536)
            if not data:
                return
            if data == b"BYE":
                conn.sendall("пока".encode())
                return
            conn.sendall(data)


def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    print(listener.getsockname()[1], flush=True)

    def accept():
        while True:
            conn, _ = listener.accept()
            threading.Thread(target=serve, args=(conn,), daemon=True).start()

    threading.Thread(target=accept, daemon=True).start()
    sys.stdin.read()


if __name__ == "__main__":
    main()
