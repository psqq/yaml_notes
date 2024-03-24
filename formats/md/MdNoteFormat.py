import yaml

from formats.common.CommonNoteFormat import CommonNoteFormat
import formats.common.NoteAst as NoteAst
from formats.common.CommonParser import CommonParser
import re


class MdNoteFormatParser(CommonParser):
    def __init__(self, text_for_parse):
        super().__init__(text_for_parse)

    def try_parse_code(self):
        l = self.next_line()
        if not l.startswith('```'):
            self.back_line()
            return False
        code_node = self.create_node(NoteAst.CodeNode)
        code_node.header = l
        code_node.lang = l[3:].strip()
        code_node.footer = ''
        code_node.code = ''
        self.noteNode.childs.append(code_node)
        while True:
            l = self.next_line()
            if l.startswith('```'):
                code_node.footer = l
                return True
            code_node.code += l

    def try_parse_task_sub_element(self, parent: NoteAst.TaskNode):
        l = self.next_line()
        m = re.match(r'^(\s+)([\-*]) (.*)', l)
        if not m:
            self.back_line()
            return False
        if len(m.group(1)) <= len(parent.left_padding):
            self.back_line()
            return False
        mt = re.match(r'\[(.)] (.*)', m.group(3))
        if mt:
            self.back_line()
            return self.try_parse_task(parent)
        else:
            list_item_node = self.create_node(NoteAst.ListItemNode)
            list_item_node.left_padding = m.group(1)
            list_item_node.level = parent.level + 1
            list_item_node.mark = m.group(2)
            list_item_node.text = m.group(3)
            mm = re.match(r'^`(.*)`$', m.group(3))
            if mm:
                task_words = mm.group(1).split()
                i = 0
                while i < len(task_words):
                    w = task_words[i]
                    if w == '-':
                        parent.isInProgress = True
                    elif w == '_':
                        parent.isCanceled = True
                    elif w == '=':
                        parent.isOnHold = True
                    if i + 1 < len(task_words):
                        w2 = task_words[i + 1]
                        if w == 'P' and w2.isdigit():
                            parent.priority = int(w2)
                            i += 1
                        elif w == 'U' and w2.isdigit():
                            parent.urgency = int(w2)
                            i += 1
                    i += 1
            parent.childs.append(list_item_node)
            list_item_node.parent = parent
        return True

    def try_parse_task(self, parent: NoteAst.Node):
        l = self.next_line()
        m = re.match(r'^(\s*)- \[(.)] (.*)', l)
        if not m:
            self.back_line()
            return False
        task_tag_content = m.group(2)
        task_node = self.create_node(NoteAst.TaskNode)
        task_node.isDone = task_tag_content == 'x'
        task_node.text = m.group(3)
        task_node.left_padding = m.group(1)
        task_node.prefix = f"- [{task_tag_content}] "
        task_node.parent = parent
        parent.childs.append(task_node)
        while self.try_parse_task_sub_element(task_node):
            pass
        return True

    def try_parse_text(self):
        text_node = self.get_or_create_last_node(NoteAst.TextNode)
        text_node.value += self.next_line()
        text_node.parent = self.noteNode


class MdNoteFormat(CommonNoteFormat):
    def __init__(self):
        super().__init__()

    def parse(self, s: str):
        from Note import NoteLoadException
        self.fullText = s
        parser = MdNoteFormatParser(self.fullText)
        parser.parse()
        self.noteNode = parser.noteNode

        first_child = self.noteNode.childs[0]
        if not isinstance(first_child, NoteAst.CodeNode):
            raise NoteLoadException("No params in Note (no code)")
        if first_child.lang != 'yaml':
            raise NoteLoadException("No params in Note (first code block is not in yaml)")
        self.params = yaml.safe_load(first_child.code)

        self.text = ""
        for child in self.noteNode.childs[1:]:
            self.text += child.to_text()

    def get_default_file_extension(self):
        return 'md'

    def from_text(self, s: str):
        from Note import NoteLoadException
        self.parse(s)
        ls = s.splitlines()
        q = "text"
        params_s = ""
        text = ""
        for i, l in enumerate(ls):
            if i == 0 and l == "```yaml":
                q = "params"
            elif q == "params" and l == "```":
                q = "text"
            elif q == "params":
                params_s += l + "\n"
            elif q == "text":
                text += l + "\n"
        if not params_s:
            raise NoteLoadException("No params in Note")
        else:
            params = yaml.safe_load(params_s)
        return [text, params]

    def to_text(self, params: dict, text: str):
        s = "```yaml\n"
        s += yaml.safe_dump(params, allow_unicode=True)
        s += "```\n\n"
        s += text.strip() + "\n"
        return s
