import unittest

from Note import Note
from formats.norg.NorgNoteFormat import NorgNoteFormat
from formats.common.NoteAst import TaskNode
from tests.test_Base import TestBase


class TestNorgNoteFormat(TestBase):
    def test_empty_note(self):
        norg_note = NorgNoteFormat()
        full_note_text = self.load_test_note("empty_note.norg")
        norg_note.parse(full_note_text)
        self.assertEqual(norg_note.noteNode.childs.__len__(), 1)
        self.assertEqual(norg_note.node_to_text(), full_note_text)

    def test_check_id(self):
        norg_note = NorgNoteFormat()
        full_note_text = self.load_test_note("note_with_id_42.norg")
        norg_note.parse(full_note_text)
        note = Note()
        note.params = norg_note.params
        self.assertEqual(note.get_id(), 42)

    def test_note_with_all_tasks_types(self):
        full_note_text = self.load_test_note("note_with_all_tasks_types.norg")
        note = Note()
        note.noteFormat = NorgNoteFormat()
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

    def test_note_with_subtasks(self):
        full_note_text = self.load_test_note("note_with_subtasks.norg")
        note = Note()
        note.noteFormat = NorgNoteFormat()
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
        self.assertEqual(len(root_task.childs[0].childs[0].childs), 0)
        self.assertEqual(len(root_task.childs[0].childs[1].childs), 1)
        subtask_1_1: TaskNode = root_task.childs[0].childs[0]
        self.assertEqual(subtask_1_1.isCanceled, True)
        subtask_1_2_1: TaskNode = root_task.childs[0].childs[1].childs[0]
        self.assertEqual(subtask_1_2_1.isInProgress, True)

    def test_note_with_task_with_sublist(self):
        full_note_text = self.load_test_note("note_with_task_with_sublist.norg")
        note = Note()
        note.noteFormat = NorgNoteFormat()
        note.from_text(full_note_text)
        self.assertEqual(note.get_id(), 42)


if __name__ == "__main__":
    unittest.main()
