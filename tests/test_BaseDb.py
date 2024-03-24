import unittest
import db
from tests.test_Base import TestBase


class TestBaseDb(TestBase):
    def setUp(self) -> None:
        self.setup_db()

    def test_empty_db_has_only_config_options(self):
        for k, v in db.get_options().items():
            self.assertTrue(k.startswith("config__"))


if __name__ == "__main__":
    unittest.main()
