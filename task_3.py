import struct

def process_file_inplace(filename):
    divisor = 73 * 2 + 29  # 175
    with open(filename, 'r+b') as f:
        # Определяем размер числа в байтах
        int_size = 4
        while True:
            pos = f.tell()
            bytes_read = f.read(int_size)
            if len(bytes_read) < int_size:
                break  # конец файла
            # Распаковываем int32 little-endian
            x = struct.unpack('<i', bytes_read)[0]

            if x % 7 == 0:
                # Новое значение
                new_x = int(x * 100 / divisor)
                # Перезаписываем на месте
                f.seek(pos)
                f.write(struct.pack('<i', new_x))
            else:
                # Сдвигаемся дальше, ничего делать не нужно
                # Но сдвиг уже состоялся из-за чтения
                pass

if __name__ == '__main__':
    filename = 'resource/numbers.bin'  # тут укажи свой файл
    process_file_inplace(filename)
    print("Обработка завершена!")