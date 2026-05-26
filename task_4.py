class JsonParserError(Exception):
    def __init__(self, message, line_no):
        super().__init__(f"Line {line_no}: {message}")
        self.line_no = line_no


def serialize(obj):
    if obj is None:
        return "null"
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif isinstance(obj, (int, float)):
        return str(obj)
    elif isinstance(obj, str):
        esc = obj.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t',
                                                                                                              '\\t')
        return '"' + esc + '"'
    elif isinstance(obj, list):
        return "[" + ",".join(serialize(item) for item in obj) + "]"
    elif isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError("JSON object keys must be strings")
            items.append(serialize(k) + ":" + serialize(v))
        return "{" + ",".join(items) + "}"
    else:
        raise TypeError("Type not serializable: " + str(type(obj)))


def deserialize(s):

    pos = 0
    line = 1

    def skip_whitespace():
        nonlocal pos, line
        while pos < len(s) and s[pos] in " \t\n\r":
            if s[pos] == '\n':
                line += 1
            pos += 1

    def parse_value():
        nonlocal pos, line
        skip_whitespace()
        if pos >= len(s):
            raise JsonParserError("Unexpected end of data", line)

        if s[pos] == '"':
            return parse_string()
        elif s[pos] == '{':
            return parse_object()
        elif s[pos] == '[':
            return parse_array()
        elif s[pos] in "-0123456789":
            return parse_number()
        elif s.startswith("true", pos):
            pos_inc(4)
            return True
        elif s.startswith("false", pos):
            pos_inc(5)
            return False
        elif s.startswith("null", pos):
            pos_inc(4)
            return None
        else:
            raise JsonParserError(f"Invalid value starting with '{s[pos]}'", line)

    def pos_inc(n):
        nonlocal pos
        pos += n

    def parse_string():
        nonlocal pos, line
        if s[pos] != '"':
            raise JsonParserError('Expected \'"\' for string start', line)
        pos += 1
        res = ''
        while pos < len(s):
            ch = s[pos]
            if ch == '"':
                pos += 1
                return res
            elif ch == '\\':
                pos += 1
                if pos >= len(s):
                    raise JsonParserError("Invalid escape at end of string", line)
                esc_ch = s[pos]
                if esc_ch == '"':
                    res += '"'
                elif esc_ch == '\\':
                    res += '\\'
                elif esc_ch == '/':
                    res += '/'
                elif esc_ch == 'b':
                    res += '\b'
                elif esc_ch == 'f':
                    res += '\f'
                elif esc_ch == 'n':
                    res += '\n'
                elif esc_ch == 'r':
                    res += '\r'
                elif esc_ch == 't':
                    res += '\t'
                elif esc_ch == 'u':
                    raise JsonParserError("Unicode escape not supported", line)
                else:
                    raise JsonParserError(f"Invalid escape character \\{esc_ch}", line)
                pos += 1
            else:
                if ch == '\n' or ch == '\r':
                    raise JsonParserError("String not closed before newline", line)
                res += ch
                pos += 1
        raise JsonParserError("Unterminated string literal", line)

    def parse_number():
        nonlocal pos
        start = pos
        if s[pos] == '-':
            pos += 1
        if pos < len(s) and s[pos] == '0':
            pos += 1
        else:
            while pos < len(s) and s[pos].isdigit():
                pos += 1
        if pos < len(s) and s[pos] == '.':
            pos += 1
            if pos >= len(s) or not s[pos].isdigit():
                raise JsonParserError("Invalid number format", line)
            while pos < len(s) and s[pos].isdigit():
                pos += 1
        if pos < len(s) and s[pos] in 'eE':
            pos += 1
            if pos < len(s) and s[pos] in '+-':
                pos += 1
            if pos >= len(s) or not s[pos].isdigit():
                raise JsonParserError("Invalid number format", line)
            while pos < len(s) and s[pos].isdigit():
                pos += 1

        num_str = s[start:pos]
        try:
            if '.' in num_str or 'e' in num_str or 'E' in num_str:
                return float(num_str)
            else:
                return int(num_str)
        except ValueError:
            raise JsonParserError("Invalid number: " + num_str, line)

    def parse_array():
        nonlocal pos
        if s[pos] != '[':
            raise JsonParserError("Expected '['", line)
        pos += 1
        skip_whitespace()
        arr = []
        if pos < len(s) and s[pos] == ']':
            pos += 1
            return arr
        while True:
            val = parse_value()
            arr.append(val)
            skip_whitespace()
            if pos >= len(s):
                raise JsonParserError("Unterminated array", line)
            if s[pos] == ',':
                pos += 1
                skip_whitespace()
            elif s[pos] == ']':
                pos += 1
                return arr
            else:
                raise JsonParserError("Expected ',' or ']' in array", line)

    def parse_object():
        nonlocal pos
        if s[pos] != '{':
            raise JsonParserError("Expected '{'", line)
        pos += 1
        skip_whitespace()
        obj = {}
        if pos < len(s) and s[pos] == '}':
            pos += 1
            return obj
        while True:
            skip_whitespace()
            if pos >= len(s) or s[pos] != '"':
                raise JsonParserError("Expected string key", line)
            key = parse_string()
            skip_whitespace()
            if pos >= len(s) or s[pos] != ':':
                raise JsonParserError("Expected ':' after key", line)
            pos += 1
            val = parse_value()
            obj[key] = val
            skip_whitespace()
            if pos >= len(s):
                raise JsonParserError("Unterminated object", line)
            if s[pos] == ',':
                pos += 1
                skip_whitespace()
            elif s[pos] == '}':
                pos += 1
                return obj
            else:
                raise JsonParserError("Expected ',' or '}' in object", line)

    result = parse_value()
    skip_whitespace()
    if pos != len(s):
        raise JsonParserError("Extra characters after valid JSON", line)
    return result


def pretty_print(obj, indent=2):
    def _pp(o, level):
        sp = ' ' * (level * indent)
        if o is None:
            return "null"
        elif isinstance(o, bool):
            return "true" if o else "false"
        elif isinstance(o, (int, float)):
            return str(o)
        elif isinstance(o, str):
            esc = o.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t',
                                                                                                                '\\t')
            return '"' + esc + '"'
        elif isinstance(o, list):
            if not o:
                return "[]"
            inner = ",\n".join(sp + ' ' * indent + _pp(i, level + 1) for i in o)
            return "[\n" + inner + "\n" + sp + "]"
        elif isinstance(o, dict):
            if not o:
                return "{}"
            inner = ",\n".join(sp + ' ' * indent + serialize(k) + ": " + _pp(v, level + 1) for k, v in o.items())
            return "{\n" + inner + "\n" + sp + "}"
        else:
            raise TypeError("Type not serializable: " + str(type(o)))

    return _pp(obj, 0)


def validate_json(s):
    try:
        deserialize(s)
        return True, None
    except JsonParserError as e:
        return False, str(e)

def read_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
    return data


def main():
    filepath = "resource/test_1.json"
    json_str = read_json_file(filepath)

    print("Оригинальный JSON из файла:")
    print(json_str)

    valid, err = validate_json(json_str)
    if not valid:
        print(f"Ошибка валидации: {err}")
        return

    obj = deserialize(json_str)
    print("\nДесериализованный объект:")
    print(obj)

    serialized = serialize(obj)
    print("\nСериализация обратно в JSON:")
    print(serialized)

    print("\nВывод с отступами (indent=2):")
    print(pretty_print(obj, indent=2))


if __name__ == "__main__":
    main()

