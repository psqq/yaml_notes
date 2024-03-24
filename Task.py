from datetime import datetime
from typing import Optional

from Note import Note
from formats.common.NoteAst import TaskNode


class Task:
    def __init__(self):
        self.id = 0
        self.parent_task_id = 0
        self.note_id = 0
        self.line_number_in_note = 0
        self.text = ''
        self.order = 0
        self.priority = 0
        self.urgency = 0
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.indexed_at: datetime = datetime.now()
        self.deleted_at: Optional[datetime] = None
        self.done_at: Optional[datetime] = None
        self.canceled_at: Optional[datetime] = None
        self.suspended_until: Optional[datetime] = None

    def from_task_node(self, task_node: TaskNode, note: Note):
        self.note_id = note.get_id()
        self.text = task_node.text
        self.line_number_in_note = task_node.line_number
        self.priority = task_node.priority
        self.urgency = task_node.urgency
        self.urgency = task_node.urgency
        self.created_at = note.get_created_at()
        self.updated_at = note.get_created_at()
        self.done_at = datetime.now() if task_node.isDone else None
        self.canceled_at = datetime.now() if task_node.isCanceled else None
        return self
