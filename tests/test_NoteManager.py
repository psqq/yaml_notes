import unittest

from tests.test_Base import TestBase


class TestNoteManager(TestBase):
    def setUp(self) -> None:
        self.setup_db()
        self.setup_notes_manager()

    def test_1_empty_notes_folder(self):
        notes = [note for note in self.nm.iter_notes_by_fs_walk()]
        self.assertEqual(len(notes), 0)
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 0)

    def test_2_create_one_note(self):
        notes = [note for note in self.nm.iter_notes_by_fs_walk()]
        self.assertEqual(len(notes), 0)
        note = self.nm.make_note()
        note.save()
        notes = [note for note in self.nm.iter_notes_by_fs_walk()]
        self.assertEqual(len(notes), 1)
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)


if __name__ == "__main__":
    unittest.main()
