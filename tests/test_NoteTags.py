import unittest

from tests.test_Base import TestBase
from cli import Cli
import db
import config
from os import path


class TestNoteManager(TestBase):
    def setUp(self) -> None:
        self.setup_db()
        self.setup_notes_manager()

    def test_1_adding_tags_to_notes(self):
        note_a = self.nm.make_note()
        note_a.add_tag("tag-a")
        note_a.save()
        note_b = self.nm.make_note()
        note_b.add_tag("tag-b")
        note_b.save()
        cli = Cli()
        cli.default()
        notesByDb = [note for note in self.nm.iter_notes_by_db()]
        notesByDb.sort(key=lambda n: n.get_id())
        self.assertEqual(len(notesByDb), 2)
        self.assertEqual(
            path.relpath(notesByDb[0].filepath, config.notes_dir), "001_tag-a.md"
        )
        self.assertEqual(
            path.relpath(notesByDb[1].filepath, config.notes_dir), "002_tag-b.md"
        )

    def test_2_tags_for_dirs(self):
        db.set_json_option(
            db.TAGS_FOR_DIRS_KEY,
            [
                ["tag-a"],
                ["tag-b"],
            ],
        )
        note_a = self.nm.make_note()
        note_a.add_tag("tag-a")
        note_a.save()
        note_b = self.nm.make_note()
        note_b.add_tag("tag-b")
        note_b.save()
        cli = Cli()
        cli.default()
        notesByDb = [note for note in self.nm.iter_notes_by_db()]
        notesByDb.sort(key=lambda n: n.get_id())
        self.assertEqual(len(notesByDb), 2)
        self.assertEqual(
            path.relpath(notesByDb[0].filepath, config.notes_dir), "tag-a/001_tag-a.md"
        )
        self.assertEqual(
            path.relpath(notesByDb[1].filepath, config.notes_dir), "tag-b/002_tag-b.md"
        )


if __name__ == "__main__":
    unittest.main()
