import struct

def parse_file(filename):
    with open(filename, 'rb') as f:
        signature = f.read(4)
        if signature != b'DATA':
            raise ValueError("Неверная сигнатура файла")

        version_bytes = f.read(2)
        version = struct.unpack('<H', version_bytes)[0]

        count_bytes = f.read(4)
        count = struct.unpack('<I', count_bytes)[0]

        temperatures = []
        active_flag_count = 0

        record_fmt = '<Q I h B'
        record_size = struct.calcsize(record_fmt)

        for _ in range(count):
            record_bytes = f.read(record_size)
            if len(record_bytes) < record_size:
                raise ValueError("Файл обрезан, не хватает данных записи")
            timestamp, rec_id, temp_raw, flag = struct.unpack(record_fmt, record_bytes)
            temp_celsius = temp_raw / 100.0
            temperatures.append(temp_celsius)
            if flag != 0:
                active_flag_count += 1

    avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0.0

    print(f"Версия файла: {version}")
    print(f"Количество записей: {count}")
    print(f"Средняя температура: {avg_temp:.2f} °C")
    print(f"Количество записей с активным флагом: {active_flag_count}")


if __name__ == '__main__':
    parse_file('resource/abc.bin')
