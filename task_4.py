import re

class JsonParser:
    def __init__(self):
        self.text = ''
        self.pos = 0
        self.length = 0
        self.line = 1

    # --- Сериализация ---
    def serialize(self, obj):
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            return 'true' if obj else 'false'
        elif isinstance(obj, (int, float)):
            # В JSON числа не могут быть NaN или Infinity
            if isinstance(obj, float):
                if obj != obj or obj == float('inf') or obj == float('-inf'):
                    raise ValueError("Числа NaN и Infinity не поддерживаются в JSON")
            return str(obj)
        elif isinstance(obj, str):
            return self._serialize_string(obj)
        elif isinstance(obj, list):
            return '[' + ','.join(self.serialize(el) for el in obj) + ']'
        elif isinstance(obj, dict):
            parts = []
            for k, v in obj.items():
                if not isinstance(k, str):
                    raise TypeError('Ключи словаря должны быть строками!')
                parts.append(self.serialize(k) + ':' + self.serialize(v))
            return '{' + ','.join(parts) + '}'
        else:
            raise TypeError(f"Тип {type(obj)} не поддерживается")

    def _serialize_string(self, s):
        replacements = {
            '\\': '\\\\',
            '"': '\\"',
            '\b': '\\b',
            '\f': '\\f',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
        }
        def replace_char(c):
            if c in replacements:
                return replacements[c]
            elif ord(c) < 0x20:
                return '\\u{0:04x}'.format(ord(c))
            else:
                return c
        return '"' + ''.join(replace_char(c) for c in s) + '"'

    # --- Десериализация ---
    def parse(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.line = 1
        value = self._parse_value()
        self._skip_whitespace()
        if self.pos != self.length:
            self._error('Лишние символы после корректного JSON')
        return value

    def _peek(self):
        if self.pos < self.length:
            return self.text[self.pos]
        return ''

    def _next(self):
        ch = self._peek()
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def _skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos] in ' \t\n\r':
            if self.text[self.pos] == '\n':
                self.line += 1
            self.pos += 1

    def _parse_value(self):
        self._skip_whitespace()
        ch = self._peek()
        if ch == '':
            self._error('Ожидалось значение, но достигнут конец')
        elif ch == '{':
            return self._parse_object()
        elif ch == '[':
            return self._parse_array()
        elif ch == '"':
            return self._parse_string()
        elif ch == '-' or ch.isdigit():
            return self._parse_number()
        elif self.text.startswith('true', self.pos):
            self.pos += 4
            return True
        elif self.text.startswith('false', self.pos):
            self.pos += 5
            return False
        elif self.text.startswith('null', self.pos):
            self.pos += 4
            return None
        else:
            self._error(f'Неожиданный символ {ch!r} при попытке распарсить значение')

    def _parse_object(self):
        obj = {}
        self.pos += 1  # пропускаем '{'
        self._skip_whitespace()
        if self._peek() == '}':
            self.pos += 1
            return obj
        while True:
            self._skip_whitespace()
            if self._peek() != '"':
                self._error('Ожидался ключ-строка объекта')
            key = self._parse_string()
            self._skip_whitespace()
            if self._peek() != ':':
                self._error('Ожидался двоеточие после ключа объекта')
            self.pos += 1
            val = self._parse_value()
            obj[key] = val
            self._skip_whitespace()
            ch = self._peek()
            if ch == ',':
                self.pos += 1
                continue
            elif ch == '}':
                self.pos += 1
                break
            else:
                self._error('Ожидалась запятая или закрывающая фигурная скобка в объекте')
        return obj

    def _parse_array(self):
        arr = []
        self.pos += 1  # пропускаем '['
        self._skip_whitespace()
        if self._peek() == ']':
            self.pos += 1
            return arr
        while True:
            val = self._parse_value()
            arr.append(val)
            self._skip_whitespace()
            ch = self._peek()
            if ch == ',':
                self.pos += 1
                continue
            elif ch == ']':
                self.pos += 1
                break
            else:
                self._error('Ожидалась запятая или закрывающая квадратная скобка в массиве')
        return arr

    def _parse_string(self):
        assert self._peek() == '"'
        self.pos += 1  # пропускаем открывающую кавычку
        result = []
        while True:
            if self.pos >= self.length:
                self._error('Неожиданный конец строки внутри строки JSON')
            ch = self._next()
            if ch == '"':
                break
            if ch == '\\':
                if self.pos >= self.length:
                    self._error('Неожиданный конец строки после символа эскейпа')
                esc = self._next()
                if esc == '"':
                    result.append('"')
                elif esc == '\\':
                    result.append('\\')
                elif esc == '/':
                    result.append('/')
                elif esc == 'b':
                    result.append('\b')
                elif esc == 'f':
                    result.append('\f')
                elif esc == 'n':
                    result.append('\n')
                elif esc == 'r':
                    result.append('\r')
                elif esc == 't':
                    result.append('\t')
                elif esc == 'u':
                    hex_digits = self.text[self.pos:self.pos+4]
                    if len(hex_digits) < 4 or not all(c in '0123456789abcdefABCDEF' for c in hex_digits):
                        self._error('Неверная \\u последовательность')
                    unicode_char = chr(int(hex_digits, 16))
                    result.append(unicode_char)
                    self.pos += 4
                else:
                    self._error(f'Неверный escape-символ \\{esc}')
            elif ord(ch) < 0x20:
                self._error('Строка содержит недопустимый управляющий символ')
            else:
                result.append(ch)
        return ''.join(result)

    number_re = re.compile(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?')

    def _parse_number(self):
        m = self.number_re.match(self.text, self.pos)
        if not m:
            self._error('Некорректное число')
        num_str = m.group(0)
        self.pos = m.end()
        if '.' in num_str or 'e' in num_str or 'E' in num_str:
            return float(num_str)
        else:
            return int(num_str)

    def _error(self, message):
        snippet = self.text[self.pos:self.pos+20].split('\n',1)[0]
        raise ValueError(f'Ошибка в JSON на строке {self.line}: {message}. Текущий фрагмент: {snippet!r}')

    # --- Pretty print с отступами ---
    def pretty_print(self, obj, indent=4):
        return self._pretty(obj, indent, 0)

    def _pretty(self, obj, indent, level):
        space = ' ' * (indent * level)
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            return 'true' if obj else 'false'
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, str):
            return self._serialize_string(obj)
        elif isinstance(obj, list):
            if not obj:
                return '[]'
            items = [self._pretty(el, indent, level + 1) for el in obj]
            return '[\n' + ',\n'.join(' ' * (indent * (level + 1)) + item for item in items) + '\n' + space + ']'
        elif isinstance(obj, dict):
            if not obj:
                return '{}'
            items = []
            for k, v in obj.items():
                item = self._serialize_string(k) + ': ' + self._pretty(v, indent, level + 1)
                items.append(' ' * (indent * (level + 1)) + item)
            return '{\n' + ',\n'.join(items) + '\n' + space + '}'
        else:
            raise TypeError(f"Тип {type(obj)} не поддерживается для pretty-print")

    # --- Валидация с указанием строки ошибки ---
    def validate(self, text):
        try:
            self.parse(text)
            return True, None
        except ValueError as e:
            return False, str(e)


if __name__ == '__main__':
    parser = JsonParser()



