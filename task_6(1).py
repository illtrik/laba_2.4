import socket
import threading
import os
import json
import xml.etree.ElementTree as ET

KEY = 0x5A

STORAGE_DIR = 'storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def rotate_left(val, n):
    return ((val << n) | (val >> (8 - n))) & 0xFF

def rotate_right(val, n):
    return ((val >> n) | (val << (8 - n))) & 0xFF

def encrypt_data(data: bytes) -> bytes:
    result = bytearray()
    for b in data:
        r = rotate_left(b, 2)
        c = r ^ KEY
        result.append(c)
    return bytes(result)

def decrypt_data(data: bytes) -> bytes:
    result = bytearray()
    for b in data:
        r = b ^ KEY
        c = rotate_right(r, 2)
        result.append(c)
    return bytes(result)

def validate_file(filename: str, data: bytes) -> bool:
    try:
        if filename.endswith('.json'):
            json.loads(data.decode('utf-8'))
        elif filename.endswith('.xml'):
            ET.fromstring(data.decode('utf-8'))
        else:
            return False
        return True
    except Exception:
        return False

def handle_client(conn, addr):
    print(f"Connected: {addr}")
    try:
        while True:
            header = b''
            while not header.endswith(b'\n'):
                part = conn.recv(1)
                if not part:
                    print(f"Disconnected: {addr}")
                    return
                header += part
            header_str = header.decode().strip()
            if header_str.upper() == 'QUIT':
                conn.sendall(b'OK\n')
                break
            parts = header_str.split(' ', 1)
            cmd = parts[0].upper()
            if cmd == 'UPLOAD' and len(parts) == 2:
                filename = parts[1]
                length_line = b''
                while not length_line.endswith(b'\n'):
                    length_line += conn.recv(1)
                length = int(length_line.decode().strip())
                received = b''
                while len(received) < length:
                    received += conn.recv(length - len(received))
                data = received

                print(f"Received: {filename} ({length} bytes)")
                if not validate_file(filename, data):
                    conn.sendall(b'ERROR: Invalid file format\n')
                    continue
                encrypted = encrypt_data(data)
                bin_filename = os.path.join(STORAGE_DIR, filename + '.bin')
                with open(bin_filename, 'wb') as f:
                    f.write(encrypted)
                conn.sendall(b'OK\n')

            elif cmd == 'DOWNLOAD' and len(parts) == 2:
                bin_filename = os.path.join(STORAGE_DIR, parts[1])
                if not os.path.exists(bin_filename):
                    conn.sendall(b'ERROR: File not found\n')
                    continue
                with open(bin_filename, 'rb') as f:
                    data = f.read()
                conn.sendall(f"{len(data)}\n".encode())
                conn.sendall(data)
            else:
                conn.sendall(b'ERROR: Unknown command\n')
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection closed: {addr}")

def main():
    HOST = '0.0.0.0'
    PORT = 9000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server started on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main()