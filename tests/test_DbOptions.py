import unittest
import db
from os import path, mkdir
import shutil
from tests.test_Base import TestBase

_dir = path.dirname(__file__)


class TestBaseDb(TestBase):
    def setUp(self) -> None:
        self.setup_db()

    def test_empty_db(self):
        db.set_option("key", "value")
        self.assertEqual(db.get_options()["key"], "value")
        db.set_option("key2", "value2")
        self.assertEqual(db.get_options()["key"], "value")
        self.assertEqual(db.get_options()["key2"], "value2")
        json_option_value = {"json_key": "json_value", "json_array": [1, 2, 3]}
        db.set_json_option("key_for_json_option", json_option_value)
        self.assertDictEqual(
            db.get_json_option("key_for_json_option"), json_option_value
        )

    def test_bool_db_options(self):
        db.set_option("true_key", True)
        self.assertEqual(db.get_options()["true_key"], "True")
        db.set_option("false_key", False)
        self.assertEqual(db.get_options()["false_key"], "False")


if __name__ == "__main__":
    unittest.main()
