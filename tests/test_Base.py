import unittest
from NotesManager import NotesManager
import db
from os import path, mkdir
import shutil
import config
import cli

_dir = path.dirname(__file__)


class TestBase(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tmp_current_test_dir = path.join(_dir, "tmp/current")
        self.tmp_current_test_notes_dir = path.join(self.tmp_current_test_dir, "notes")
        self.nm: NotesManager = None

    def setup_config(self):
        config.db_path = path.join(
            self.tmp_current_test_dir, "yaml_notes_test_db.sqlite3"
        )
        config.notes_dir = self.tmp_current_test_notes_dir

    def setup_tmp_dir(self):
        self.tmp_current_test_dir = path.join(_dir, "tmp/current")
        shutil.rmtree(self.tmp_current_test_dir, ignore_errors=True)
        mkdir(self.tmp_current_test_dir)

    def setup_db(self):
        self.setup_config()
        self.setup_tmp_dir()
        db.init_db()
        db.run_migrations()
        cli.save_config_in_db()

    def setup_notes_manager(self):
        self.nm = NotesManager(self.tmp_current_test_notes_dir)
        self.nm._verbose = False

    def load_test_note(self, filename: str) -> str:
        with open(path.join(_dir, "data/" + filename), "r", encoding="utf-8") as f:
            return f.read()
