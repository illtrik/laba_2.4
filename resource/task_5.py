import re

class XmlParser:
    def __init__(self):
        self.text = ''
        self.pos = 0
        self.length = 0
        self.line = 1

    def serialize(self, obj, root_tag='root'):
        xml_content = self._serialize_value(obj)
        return f'<{root_tag}>{xml_content}</{root_tag}>'

    def _serialize_value(self, obj):
        if obj is None:
            return ''
        elif isinstance(obj, bool):
            return 'true' if obj else 'false'
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, str):
            return self._escape_text(obj)
        elif isinstance(obj, list):
            return ''.join(f'<item>{self._serialize_value(el)}</item>' for el in obj)
        elif isinstance(obj, dict):
            parts = []
            for k, v in obj.items():
                if not isinstance(k, str):
                    raise TypeError('Ключи словаря должны быть строками!')
                parts.append(f'<{k}>{self._serialize_value(v)}</{k}>')
            return ''.join(parts)
        else:
            raise TypeError(f"Тип {type(obj)} не поддерживается для сериализации в XML")

    def _escape_text(self, text):
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&apos;'))

    def parse(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.line = 1
        self._skip_whitespace()
        if self._peek() != '<':
            self._error('Ожидался элемент')
        node = self._parse_element()
        self._skip_whitespace()
        if self.pos != self.length:
            self._error('Лишние символы после корневого элемента')
        return node

    def _parse_element(self):
        assert self._peek() == '<'
        self.pos += 1
        self._skip_whitespace()
        tag = self._parse_tag_name()
        attributes = self._parse_attributes()
        self._skip_whitespace()

        if self.text.startswith('/>', self.pos):
            self.pos += 2
            return {tag: None} if not attributes else {tag: {'@attributes': attributes}}

        if self._peek() != '>':
            self._error('Ожидался > в открывающем теге')
        self.pos += 1

        children = []
        text_content = []

        while True:
            self._skip_whitespace()
            if self.text.startswith(f'</{tag}>', self.pos):
                self.pos += len(f'</{tag}>')
                break

            if self._peek() == '<':
                if self.text.startswith('</', self.pos):
                    continue
                child = self._parse_element()
                children.append(child)
            else:
                text = self._parse_text()
                text_content.append(text)

            self._skip_whitespace()

            if self.pos >= self.length:
                self._error(f'Ожидался закрывающий тег </{tag}>')

        if children:
            res = {}
            for child in children:
                for k, v in child.items():
                    if k in res:
                        if not isinstance(res[k], list):
                            res[k] = [res[k]]
                        res[k].append(v)
                    else:
                        res[k] = v
            if attributes:
                res['@attributes'] = attributes
            if text_content and ''.join(text_content).strip():
                res['#text'] = ''.join(text_content).strip()
            return {tag: res}
        else:
            val = ''.join(text_content).strip() if text_content else None
            if attributes:
                return {tag: {'@attributes': attributes, '#text': val} if val else {'@attributes': attributes}}
            else:
                return {tag: val}

    def _parse_tag_name(self):
        m = re.match(r'[a-zA-Z_:][a-zA-Z0-9_\-.:]*', self.text[self.pos:])
        if not m:
            self._error('Некорректное имя тега')
        tag = m.group(0)
        self.pos += len(tag)
        return tag

    def _parse_attributes(self):
        attrs = {}
        while True:
            self._skip_whitespace()
            if self._peek() in ['>', '/', '']:
                break
            name = self._parse_tag_name()
            self._skip_whitespace()
            if self._peek() != '=':
                self._error('Ожидался = после имени атрибута')
            self.pos += 1
            self._skip_whitespace()
            quote = self._peek()
            if quote not in ['"', "'"]:
                self._error('Атрибут должен быть в кавычках')
            self.pos += 1
            value_start = self.pos
            while self.pos < self.length and self._peek() != quote:
                self.pos += 1
            if self.pos >= self.length:
                self._error('Незакрытая кавычка в атрибуте')
            value = self.text[value_start:self.pos]
            value = self._unescape_text(value)
            self.pos += 1
            attrs[name] = value
        return attrs

    def _parse_text(self):
        start = self.pos
        while self.pos < self.length and self._peek() != '<':
            ch = self._peek()
            if ch == '\n':
                self.line += 1
            self.pos += 1
        text = self.text[start:self.pos]
        return self._unescape_text(text.strip())

    def _peek(self):
        if self.pos < self.length:
            return self.text[self.pos]
        return ''

    def _skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos] in ' \t\r\n':
            if self.text[self.pos] == '\n':
                self.line += 1
            self.pos += 1

    def _unescape_text(self, text):
        text = (text.replace('&lt;', '<')
                    .replace('&gt;', '>')
                    .replace('&amp;', '&')
                    .replace('&quot;', '"')
                    .replace('&apos;', "'"))
        return text

    def _error(self, message):
        snippet = self.text[self.pos:self.pos+20].split('\n',1)[0]
        raise ValueError(f'Ошибка в XML на строке {self.line}: {message}. Текущий фрагмент: {snippet!r}')


    def pretty_print(self, obj, indent=4):
        if not isinstance(obj, dict) or len(obj) != 1:
            raise TypeError('Для pretty_print ожидается dict с одним корневым элементом')
        root_tag = list(obj.keys())[0]
        return self._pretty_element(root_tag, obj[root_tag], indent, 0)

    def _pretty_element(self, tag, content, indent, level):
        space = ' ' * (indent * level)

        attrs = ''
        children = ''
        text = ''

        if isinstance(content, dict):
            attrs_dict = content.get('@attributes', {})
            text = content.get('#text', '')
            other_keys = [k for k in content.keys() if k not in ('@attributes', '#text')]
            attrs = ''.join(f' {k}="{self._escape_text(str(v))}"' for k, v in attrs_dict.items())

            if other_keys:
                children_parts = []
                for k in other_keys:
                    v = content[k]
                    if isinstance(v, list):
                        for el in v:
                            children_parts.append(self._pretty_element(k, el, indent, level + 1))
                    else:
                        children_parts.append(self._pretty_element(k, v, indent, level + 1))
                children = '\n'.join(children_parts)
                if text:
                    children = self._escape_text(text) + '\n' + children
                return f'{space}<{tag}{attrs}>\n{children}\n{space}</{tag}>'
            else:
                if text:
                    return f'{space}<{tag}{attrs}>{self._escape_text(text)}</{tag}>'
                else:
                    return f'{space}<{tag}{attrs} />'
        elif isinstance(content, list):
            parts = []
            for el in content:
                parts.append(self._pretty_element(tag, el, indent, level))
            return '\n'.join(parts)
        elif content is None:
            return f'{space}<{tag} />'
        else:
            return f'{space}<{tag}>{self._escape_text(str(content))}</{tag}>'

    def validate(self, text):
        try:
            self.parse(text)
            return True, None
        except ValueError as e:
            return False, str(e)

if __name__ == '__main__':
    parser = XmlParser()

