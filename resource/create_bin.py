import struct
import time

def create_test_file(filename):
    signature = b'DATA'
    version = 1
    records = [
        {
            'timestamp': int(time.time()),
            'id': 1234,
            'temp': int(23.45 * 100),  # 23.45 C
            'flag': 0b00000011
        },
        {
            'timestamp': int(time.time()) + 60,
            'id': 5678,
            'temp': int(-5.67 * 100),  # -5.67 C
            'flag': 0b00000000
        }
    ]
    count = len(records)

    with open(filename, 'wb') as f:
        f.write(signature)
        f.write(struct.pack('<H', version))
        f.write(struct.pack('<I', count))
        for r in records:
            packed = struct.pack(
                '<Q I h B',
                r['timestamp'],
                r['id'],
                r['temp'],
                r['flag']
            )
            f.write(packed)

if __name__ == '__main__':
    create_test_file('abc.bin')
    print("Файл abc.bin создан!")