import socket
import os

def send_file(sock, filepath):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        data = f.read()
    sock.sendall(f"UPLOAD {filename}\n".encode())
    sock.sendall(f"{len(data)}\n".encode())
    sock.sendall(data)
    resp = sock.recv(1024).decode()
    print(resp.strip())

def download_file(sock, bin_filename, save_as):
    sock.sendall(f"DOWNLOAD {bin_filename}\n".encode())
    length_line = b''
    while not length_line.endswith(b'\n'):
        length_line += sock.recv(1)
    length = int(length_line.decode().strip())
    received = b''
    while len(received) < length:
        received += sock.recv(length - len(received))
    with open(save_as, 'wb') as f:
        f.write(received)
    print(f"File saved: {save_as}")

def main():
    HOST = '127.0.0.1'
    PORT = 9000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    try:
        while True:
            cmd = input("Команда (upload путь_к_файлу / download имя_файла.bin / quit): ").strip()
            if cmd.startswith('upload '):
                filepath = cmd[7:].strip()
                if not os.path.exists(filepath):
                    print("Файл не найден")
                    continue
                send_file(sock, filepath)
            elif cmd.startswith('download '):
                filename = cmd[9:].strip()
                save_as = input("Куда сохранить: ").strip()
                download_file(sock, filename, save_as)
            elif cmd == 'quit':
                sock.sendall(b'QUIT\n')
                resp = sock.recv(1024).decode()
                print(resp.strip())
                break
            else:
                print("Неизвестная команда")
    finally:
        sock.close()

if __name__ == '__main__':
    main()