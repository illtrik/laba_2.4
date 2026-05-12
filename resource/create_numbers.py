import struct

numbers = [7, 20, 21, 35, 42, 50]

with open('numbers.bin', 'wb') as f:
    for num in numbers:
        f.write(struct.pack('<i', num))

print("Файл numbers.bin создан с тестовыми данными!")