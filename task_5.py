class XmlParserError(Exception):
    def __init__(self, message, line_no):
        super().__init__(f"Line {line_no}: {message}")
        self.line_no = line_no


def escape_xml(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def unescape_xml(text):
    return (text.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&apos;", "'")
                .replace("&amp;", "&"))


def serialize_xml(node):

    tag = node["tag"]
    attrs = node.get("attributes", {})
    children = node.get("children", [])
    text = node.get("text", None)

    attr_str = ""
    for k, v in attrs.items():
        attr_str += f' {k}="{escape_xml(str(v))}"'

    res = f"<{tag}{attr_str}>"

    if text:
        res += escape_xml(text)
    for c in children:
        if isinstance(c, str):
            res += escape_xml(c)
        else:
            res += serialize_xml(c)

    res += f"</{tag}>"
    return res


def pretty_print_xml(node, indent=2, level=0):
    sp = " " * (indent * level)
    tag = node["tag"]
    attrs = node.get("attributes", {})
    children = node.get("children", [])
    text = node.get("text", None)

    attr_str = ""
    for k, v in attrs.items():
        attr_str += f' {k}="{escape_xml(str(v))}"'

    if not children and not text:
        return f"{sp}<{tag}{attr_str}/>"
    res = f"{sp}<{tag}{attr_str}>"

    if text:
        res += escape_xml(text)
    else:
        res += "\n"
        for c in children:
            if isinstance(c, str):
                res += sp + " " * indent + escape_xml(c) + "\n"
            else:
                res += pretty_print_xml(c, indent, level + 1) + "\n"
        res += sp
    res += f"</{tag}>"
    return res


def deserialize_xml(s):
    pos = 0
    line = 1

    def skip_whitespace():
        nonlocal pos, line
        while pos < len(s) and s[pos] in " \t\r\n":
            if s[pos] == '\n':
                line += 1
            pos += 1

    def parse_tag_name():
        nonlocal pos, line
        start = pos
        while pos < len(s) and (s[pos].isalnum() or s[pos] in "-_:"):
            pos += 1
        if start == pos:
            raise XmlParserError("Expected tag name", line)
        return s[start:pos]

    def parse_attributes():
        nonlocal pos, line
        attrs = {}
        while True:
            skip_whitespace()
            if pos >= len(s) or s[pos] in ['>', '/', '?']:
                break
            start = pos
            while pos < len(s) and (s[pos].isalnum() or s[pos] in ['-', '_', ':']):
                pos += 1
            attr_name = s[start:pos]
            if not attr_name:
                break
            skip_whitespace()
            if pos >= len(s) or s[pos] != '=':
                raise XmlParserError("Expected '=' after attribute name", line)
            pos += 1
            skip_whitespace()
            if pos >= len(s) or s[pos] not in ['"', "'"]:
                raise XmlParserError("Expected quote to start attribute value", line)
            quote_char = s[pos]
            pos += 1
            start_val = pos
            while pos < len(s) and s[pos] != quote_char:
                if s[pos] == '\n':
                    line += 1
                pos += 1
            if pos >= len(s):
                raise XmlParserError("Unterminated attribute value", line)
            attr_value = s[start_val:pos]
            pos += 1
            attrs[attr_name] = unescape_xml(attr_value)
        return attrs

    def parse_node():
        nonlocal pos, line
        skip_whitespace()
        if pos >= len(s) or s[pos] != '<':
            raise XmlParserError("Expected '<'", line)
        pos += 1

        if pos < len(s) and s[pos] == '/':
            raise XmlParserError("Unexpected closing tag", line)
        if pos < len(s) and s[pos] == '?':
            pos += 1
            while pos < len(s) and not (s[pos - 1] == '?' and s[pos] == '>'):
                if s[pos] == '\n':
                    line += 1
                pos += 1
            pos += 1
            return parse_node()

        tag = parse_tag_name()
        attrs = parse_attributes()
        skip_whitespace()

        if pos < len(s) and s[pos] == '/':
            pos += 1
            if pos >= len(s) or s[pos] != '>':
                raise XmlParserError("Expected '>' after '/' in self-closing tag", line)
            pos += 1
            return {
                "tag": tag,
                "attributes": attrs,
                "children": [],
                "text": None,
            }

        if pos >= len(s) or s[pos] != '>':
            raise XmlParserError("Expected '>'", line)
        pos += 1

        children = []
        text_content = ""

        while True:
            skip_whitespace()
            if pos >= len(s):
                raise XmlParserError(f"Unclosed tag <{tag}>", line)
            if s[pos] == '<':
                if pos + 1 < len(s) and s[pos + 1] == '/':
                    pos += 2
                    close_tag = parse_tag_name()
                    if close_tag != tag:
                        raise XmlParserError(f"Mismatched closing tag, expected </{tag}> but got </{close_tag}>", line)
                    skip_whitespace()
                    if pos >= len(s) or s[pos] != '>':
                        raise XmlParserError("Expected '>' for closing tag", line)
                    pos += 1
                    break
                else:
                    if text_content.strip():
                        children.append(unescape_xml(text_content))
                        text_content = ""
                    child_node = parse_node()
                    children.append(child_node)
            else:
                text_content += s[pos]
                if s[pos] == '\n':
                    line += 1
                pos += 1

        if text_content.strip():
            text = unescape_xml(text_content.strip())
        else:
            text = None

        if children and text is not None:
            children.insert(0, text)
            text = None

        return {
            "tag": tag,
            "attributes": attrs,
            "children": children,
            "text": text,
        }

    skip_whitespace()
    res = parse_node()
    skip_whitespace()
    if pos != len(s):
        raise XmlParserError("Extra data after closing root tag", line)
    return res


def validate_xml(s):
    try:
        deserialize_xml(s)
        return True, None
    except XmlParserError as e:
        return False, str(e)


def read_xml_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    filepath = "resource/test_1.xml"
    xml_str = read_xml_file(filepath)

    print("Оригинальный XML из файла:")
    print(xml_str)

    valid, err = validate_xml(xml_str)
    if not valid:
        print(f"Ошибка валидации: {err}")
        return

    obj = deserialize_xml(xml_str)
    print("\nДесериализованный объект:")
    print(obj)

    serialized = serialize_xml(obj)
    print("\nСериализация обратно в XML:")
    print(serialized)

    print("\nВывод с отступами (indent=2):")
    print(pretty_print_xml(obj, indent=2))


if __name__ == "__main__":
    main()

