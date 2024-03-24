from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TypeVar, Type

DEFAULT_LEVEL_PADDING = '  '

T = TypeVar('T')

@dataclass
class Node:
    parent: Optional[Node] = None
    childs: list[Node] = field(default_factory=list)
    line_number: int = 0

    def is_empty(self):
        return True

    def to_text(self) -> str:
        s = ""
        for node in self.childs:
            s += node.to_text()
        return s

    def remove_empty_childs(self):
        self.childs = list(filter(lambda x: not x.is_empty(), self.childs))

    def find_parent(self, node_class: Type[T]) -> Optional[T]:
        if not self.parent:
            return None
        if isinstance(self.parent, node_class):
            return self.parent
        return self.parent.find_parent(node_class)

    def iter_tasks(self):
        for child in self.childs:
            if isinstance(child, TaskNode):
                yield child
            for task in child.iter_tasks():
                yield task


@dataclass
class TextNode(Node):
    value: str = ''

    def is_empty(self):
        return self.value == ''


@dataclass
class ListItemNode(Node):
    text: str = ''
    mark: str = ''
    level: int = 0
    left_padding: str = ''
    is_code: bool = False

    def is_empty(self):
        return False

    def to_text(self) -> str:
        return self.left_padding + self.mark + ' ' + self.text


@dataclass
class TaskNode(Node):
    isDone: bool = False
    prefix: str = ''
    text: str = ''
    isOnHold: bool = False
    isCanceled: bool = False
    isInProgress: bool = False
    priority: Optional[int] = None
    urgency: Optional[int] = None
    date: Optional[datetime] = None
    level: int = 0
    left_padding: str = ''

    def is_simple(self):
        return not self.isOnHold and not self.isCanceled and not self.isInProgress

    def is_empty(self):
        return False

    def to_text(self) -> str:
        s = self.left_padding + self.prefix + self.text + '\n'
        for child in self.childs:
            s += child.to_text()
        return s

    def is_sorted(self):
        return self.priority is not None and self.urgency is not None


@dataclass
class CodeNode(Node):
    header: str = ''
    lang: str = ''
    code: str = ''
    footer: str = ''

    def to_text(self) -> str:
        return self.header + self.code + self.footer

    def is_empty(self):
        return False


@dataclass
class Note(Node):
    pass
