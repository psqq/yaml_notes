import unittest
import json

from tests.test_Base import TestBase
from cli import Cli


class TestNoteJsonSearch(TestBase):
    def setUp(self) -> None:
        self.setup_db()
        self.setup_notes_manager()

    def test_1_json_search_by_tags(self):
        cli = Cli()
        cli.add()
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)
        note = notes[0]
        note.add_tag("tag1")
        note.save()
        cli.default()
        notes = [note for note in self.nm.iter_notes_by_db()]
        self.assertEqual(len(notes), 1)
        note_dict_from_json = json.loads(cli.get_json_search_result("et", "asdasd"))
        self.assertEqual(len(note_dict_from_json["notes"]), 1)
        note_dict_from_json = json.loads(cli.get_json_search_result("et", "tag1"))
        self.assertEqual(len(note_dict_from_json["notes"]), 0)
        note_dict_from_json = json.loads(cli.get_json_search_result("t", "tag1"))
        self.assertEqual(len(note_dict_from_json["notes"]), 1)
        note_dict_from_json = json.loads(cli.get_json_search_result("t", "tag2"))
        self.assertEqual(len(note_dict_from_json["notes"]), 0)
        note_dict_from_json = json.loads(cli.get_json_search_result("t", "tag1"))
        self.assertDictEqual(
            {"notes": [note.to_dict_for_json()]},
            note_dict_from_json,
        )
        self.assertEqual(
            note_dict_from_json["notes"][0]["parameters_object"]["id"],
            note_dict_from_json["notes"][0]["parameters_array"][0]["id"],
        )


if __name__ == "__main__":
    unittest.main()
