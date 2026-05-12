def rotate_left(byte, n):
    return ((byte << n) & 0xFF) | (byte >> (8 - n))

def rotate_right(byte, n):
    return ((byte >> n) | (byte << (8 - n))) & 0xFF

def encrypt_byte(byte, key):
    shifted = rotate_left(byte, 2)
    return shifted ^ key

def decrypt_byte(byte, key):
    xored = byte ^ key
    return rotate_right(xored, 2)

def process_file(in_filename, out_filename, key, mode='encrypt'):
    if mode not in ('encrypt', 'decrypt'):
        raise ValueError("mode должен быть 'encrypt' или 'decrypt'")

    with open(in_filename, 'rb') as f_in, open(out_filename, 'wb') as f_out:
        data = f_in.read()
        result = bytearray(len(data))

        for i, b in enumerate(data):
            if mode == 'encrypt':
                result[i] = encrypt_byte(b, key)
            else:
                result[i] = decrypt_byte(b, key)

        f_out.write(result)
    print(f"{mode.title()}ion complete: {in_filename} -> {out_filename}")

if __name__ == '__main__':
    import sys

    print("=== Шифрование файла abc.bin ===")
    mode = input("Режим (encrypt/decrypt): ").strip().lower()
    if mode not in ('encrypt', 'decrypt'):
        print("Неверный режим! Используйте 'encrypt' или 'decrypt'")
        sys.exit(1)

    in_file = 'resource/abc.bin'
    out_file = input("Имя выходного файла: ").strip()

    try:
        key = int(input("Ключ (0–255): "))
        if not (0 <= key <= 255):
            print("Ключ должен быть в диапазоне 0–255")
            sys.exit(1)
    except ValueError:
        print("Ключ должен быть целым числом")
        sys.exit(1)

    process_file(in_file, out_file, key, mode)

