import unittest

from Note import Note
from formats.md.MdNoteFormat import MdNoteFormat
from tests.test_Base import TestBase
from formats.common.NoteAst import TaskNode


class TestMdNoteFormat(TestBase):
    def test_note_with_task(self):
        full_note_text = self.load_test_note("note_with_one_task.md")
        note = Note()
        note.noteFormat = MdNoteFormat()
        note.from_text(full_note_text)
        self.assertEqual(note.get_id(), 42)
        tasks = list(note.noteFormat.noteNode.iter_tasks())
        self.assertEqual(len(tasks), 1)

    def test_note_with_all_tasks_types(self):
        full_note_text = self.load_test_note("note_with_all_tasks_types.md")
        note = Note()
        note.noteFormat = MdNoteFormat()
        note.from_text(full_note_text)
        self.assertEqual(note.get_id(), 42)
        tasks = list(note.noteFormat.noteNode.iter_tasks())
        self.assertEqual(tasks[0].isDone, False)
        self.assertEqual(tasks[0].line_number, 5)
        self.assertEqual(tasks[1].isDone, True)
        self.assertEqual(tasks[0].is_simple(), True)
        self.assertEqual(tasks[1].is_simple(), True)
        self.assertEqual(tasks[2].isInProgress, True)
        self.assertEqual(tasks[3].isCanceled, True)
        self.assertEqual(tasks[4].isOnHold, True)
        self.assertEqual(tasks[5].isCanceled, True)
        self.assertEqual(tasks[6].isCanceled, True)

    def test_note_with_subtasks(self):
        full_note_text = self.load_test_note("note_with_subtasks.md")
        note = Note()
        note.noteFormat = MdNoteFormat()
        note.from_text(full_note_text)
        self.assertEqual(note.get_id(), 42)
        tasks = list(note.noteFormat.noteNode.iter_tasks())
        self.assertEqual(len(tasks), 6)
        root_task = None
        for t in tasks:
            if t.text == "root task":
                root_task = t
        self.assertEqual(len(root_task.childs), 2)
        self.assertEqual(len(root_task.childs[0].childs), 2)
        self.assertEqual(len(root_task.childs[0].childs[0].childs), 1)
        self.assertEqual(len(root_task.childs[0].childs[1].childs), 1)
        self.assertEqual(len(root_task.childs[0].childs[1].childs[0].childs), 1)
        subtask_1_1: TaskNode = root_task.childs[0].childs[0]
        self.assertEqual(subtask_1_1.isCanceled, True)
        subtask_1_2_1: TaskNode = root_task.childs[0].childs[1].childs[0]
        self.assertEqual(subtask_1_2_1.isInProgress, True)

    def test_note_with_priority(self):
        full_note_text = self.load_test_note("note_with_priority.md")
        note = Note()
        note.noteFormat = MdNoteFormat()
        note.from_text(full_note_text)
        self.assertEqual(note.get_id(), 42)
        tasks = list(note.noteFormat.noteNode.iter_tasks())
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0].priority, 1)
        self.assertEqual(tasks[0].urgency, 3)
        self.assertEqual(tasks[0].is_sorted(), True)

        self.assertEqual(tasks[1].priority, 3)
        self.assertEqual(tasks[1].urgency, None)
        self.assertEqual(tasks[1].is_sorted(), False)

        self.assertEqual(tasks[2].priority, None)
        self.assertEqual(tasks[2].urgency, 30)
        self.assertEqual(tasks[2].is_sorted(), False)

        self.assertEqual(tasks[3].priority, 13)
        self.assertEqual(tasks[3].urgency, 21)
        self.assertEqual(tasks[3].is_sorted(), True)


if __name__ == "__main__":
    unittest.main()
