import socket
import threading
import os
import json
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

KEY = b'12345678901234567890123456789012'
STORAGE_DIR = 'storage'

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def encrypt_data(data: bytes) -> bytes:
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted

def decrypt_data(encrypted_data: bytes) -> bytes:
    iv = encrypted_data[:16]
    encrypted = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data

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
    print(f"Connection from {addr}")
    try:
        while True:
            header = b''
            while not header.endswith(b'\n'):
                part = conn.recv(1)
                if not part:
                    print(f"Connection closed by {addr}")
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

                print(f"Received file {filename} ({length} bytes)")
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
        print(f"Error: {e}")
    finally:
        conn.close()
        print(f"Connection closed {addr}")

def main():
    HOST = '0.0.0.0'
    PORT = 9000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()

if __name__ == '__main__':
    main()