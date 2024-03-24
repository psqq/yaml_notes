import unittest

from tests.test_Base import TestBase
from cli import Cli
import db
import json


class TestNoteManager(TestBase):
    def setUp(self) -> None:
        self.setup_db()
        self.setup_notes_manager()

    def test_1_check_that_json_parameters_exists(self):
        note = self.nm.make_note()
        note.add_tag("tag-a")
        note.set_bool_param("bool_param", True)
        note.set_bool_param("bool_param_2", False)
        note.set_param("int_param", 123)
        note.set_param("str_param", "string")
        note.set_param("arr_param", [1, 2, 3])
        note.set_param(
            "obj_param",
            {
                "str": "str_val",
                "int": 321,
                "arr": ["x", "y", "z"],
            },
        )
        note.save()
        cli = Cli()
        cli.default()
        res = db.cur.execute("SELECT * FROM yaml_notes").fetchone()
        data = json.loads(res["json_parameters"])
        self.assertEqual(data["bool_param"], True)
        self.assertEqual(data["bool_param_2"], False)
        self.assertEqual(data["int_param"], 123)
        self.assertEqual(data["str_param"], "string")
        self.assertEqual(data["arr_param"], [1, 2, 3])
        self.assertEqual(
            data["obj_param"],
            {
                "str": "str_val",
                "int": 321,
                "arr": ["x", "y", "z"],
            },
        )


if __name__ == "__main__":
    unittest.main()
