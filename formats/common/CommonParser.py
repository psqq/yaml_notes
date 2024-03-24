from typing import TypeVar, Type
import formats.common.NoteAst as Ast

T = TypeVar('T')


class NoMoreLines(Exception):
    pass


class CommonParser:
    def __init__(self, text_for_parse):
        self.textForParse = text_for_parse
        self.noteNode = Ast.Note()
        self.lines: list[str] = self.textForParse.split('\n')
        self.current_line = 0

    def next_line(self):
        if self.current_line >= len(self.lines):
            raise NoMoreLines()
        l = self.lines[self.current_line]
        if self.current_line < len(self.lines) - 1 or self.textForParse[-1] == '\n':
            l += '\n'
        self.current_line += 1
        return l

    def back_line(self):
        self.current_line -= 1

    def get_or_create_last_node(self, node_class: Type[T]) -> T:
        if not self.noteNode.childs:
            last_node = self.create_node(node_class)
        else:
            last_node = self.noteNode.childs[-1]
            if isinstance(last_node, node_class):
                return last_node
            else:
                last_node = node_class()
        self.noteNode.childs.append(last_node)
        return last_node

    def create_node(self, node_class: Type[T]) -> T:
        node = node_class()
        node.line_number = self.current_line
        return node

    def try_parse_code(self):
        raise NotImplemented()

    def try_parse_task(self, parent: Ast.Node):
        raise NotImplemented()

    def try_parse_text(self):
        raise NotImplemented()

    def parse(self):
        try:
            i = 0
            while True:
                while self.try_parse_code():
                    pass
                while self.try_parse_task(self.noteNode):
                    pass
                self.try_parse_text()
                i += 1
                if i >= 100000:
                    raise Exception("Too many while iterations")
        except NoMoreLines:
            pass
        finally:
            self.noteNode.remove_empty_childs()
