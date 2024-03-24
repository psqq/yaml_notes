import unittest

from tests.test_Base import TestBase
from cli import Cli


class TestNoteManager(TestBase):
    def setUp(self) -> None:
        self.setup_db()
        self.setup_notes_manager()

    def test_1_changing_note_folder_to_yes(self):
        note = self.nm.make_note()
        note.save()
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)
        note.set_bool_param("folder", True)
        note.save()
        self.nm.move_in_dirs_by_tags(note)
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)

    def test_2_changing_note_folder_with_cli(self):
        cli = Cli()
        cli.add()
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)
        note = notes[0]
        note.set_bool_param("folder", True)
        note.save()
        cli.default()
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)


if __name__ == "__main__":
    unittest.main()
