from typing import Optional
import yaml

from formats.common.CommonNoteFormat import CommonNoteFormat
import formats.common.NoteAst as NoteAst
from formats.common.CommonParser import CommonParser
import re


class NorgNoteFormatParser(CommonParser):
    def __init__(self, text_for_parse):
        super().__init__(text_for_parse)

    def try_parse_code(self):
        l = self.next_line()
        if l != '@code' and not l.startswith('@code '):
            self.back_line()
            return False
        code_node = self.create_node(NoteAst.CodeNode)
        code_node.header = l
        code_node.lang = l[5:].strip()
        code_node.footer = ''
        code_node.code = ''
        self.noteNode.childs.append(code_node)
        while True:
            l = self.next_line()
            if l.startswith('@end'):
                code_node.footer = l
                return True
            code_node.code += l

    def try_parse_task_sub_element(self, parent: NoteAst.TaskNode):
        l = self.next_line()
        m = re.match(r'^(-+) (.*)', l)
        if not m:
            self.back_line()
            return False
        level = len(m.group(1))
        if level <= parent.level:
            self.back_line()
            return False
        mt = re.match(r'\([^)]+\) (.*)', m.group(2))
        if mt:
            self.back_line()
            return self.try_parse_task(parent)
        else:
            list_item_node = self.create_node(NoteAst.ListItemNode)
            list_item_node.left_padding = ''
            list_item_node.level = level
            list_item_node.mark = m.group(1)
            list_item_node.text = m.group(2)
            parent.childs.append(list_item_node)
        return True

    def try_parse_task(self, parent: NoteAst.Node):
        l = self.next_line()
        m = re.match(r'^(-+) \(([^)]*)\) (.*)', l)
        if not m:
            self.back_line()
            return False
        level = len(m.group(1))
        task_tag_content = m.group(2)
        task_node = self.create_node(NoteAst.TaskNode)
        task_node.isDone = task_tag_content[0] == 'x'
        task_node.isInProgress = task_tag_content[0] == '-'
        task_node.isOnHold = task_tag_content[0] == '='
        task_node.isCanceled = task_tag_content[0] == '_'
        task_node.text = m.group(3)
        task_node.prefix = f"{m.group(1)} ({m.group(2)}) "
        task_node.level = level
        parent.childs.append(task_node)
        while self.try_parse_task_sub_element(task_node):
            pass
        return True

    def try_parse_text(self):
        text_node = self.get_or_create_last_node(NoteAst.TextNode)
        text_node.value += self.next_line()


class NorgNoteFormat(CommonNoteFormat):
    def __init__(self):
        super().__init__()

    def get_default_file_extension(self):
        return "norg"

    def parse(self, s: str):
        from Note import NoteLoadException
        self.fullText = s
        parser = NorgNoteFormatParser(self.fullText)
        parser.parse()
        self.noteNode = parser.noteNode

        firstChild = self.noteNode.childs[0]
        if not isinstance(firstChild, NoteAst.CodeNode):
            raise NoteLoadException("No params in Note (no code)")
        if firstChild.lang != 'yaml':
            raise NoteLoadException("No params in Note (first code block is not in yaml)")
        self.params = yaml.safe_load(firstChild.code)

        self.text = ""
        for child in self.noteNode.childs[1:]:
            self.text += child.to_text()

    def from_text(self, s: str):
        from Note import NoteLoadException
        self.parse(s)
        ls = s.splitlines()
        q = "text"
        params_s = ""
        text = ""
        for i, l in enumerate(ls):
            if i == 0 and l == "@code yaml":
                q = "params"
            elif q == "params" and l == "@end":
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
        s = "@code yaml\n"
        s += yaml.safe_dump(params, allow_unicode=True)
        s += "@end\n\n"
        s += text.strip() + "\n"
        return s

    def node_to_text(self, node: Optional[NoteAst.Node] = None):
        if not node:
            node = self.noteNode
        if isinstance(node, NoteAst.Note):
            s = ''
            for child in node.childs:
                s += self.node_to_text(child)
            return s
        else:
            return node.to_text()
