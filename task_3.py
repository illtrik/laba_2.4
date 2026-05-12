import struct

def process_file_inplace(filename):
    divisor = 73 * 2 + 29  # 175
    with open(filename, 'r+b') as f:
        int_size = 4
        while True:
            pos = f.tell()
            bytes_read = f.read(int_size)
            if len(bytes_read) < int_size:
                break
            x = struct.unpack('<i', bytes_read)[0]

            if x % 7 == 0:
                new_x = int(x * 100 / divisor)
                f.seek(pos)
                f.write(struct.pack('<i', new_x))
            else:
                pass

if __name__ == '__main__':
    filename = 'resource/numbers.bin'
    process_file_inplace(filename)
    print("Обработка завершена!")