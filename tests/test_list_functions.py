import os
import unittest
from time import sleep
from typing import Iterable
from unittest import mock

from src.db.db import Db
from src.bot import functions as e
from src.utils import BotError


class Owner:
    id = -1
    name = "FunctionalTestUser"


OWNER = Owner()


def build_context(message_content="") -> Iterable:
    m = mock.MagicMock()
    return m, OWNER, message_content


class TestListFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Change pwd to root folder, same as when main.py is run
        os.chdir("..")

    def setUp(self):
        pass

    def tearDown(self):
        with Db() as db:
            db.wipe_owner_data(OWNER.id)

    def test_new_list(self):
        actual, _, _ = e.new_list(*build_context("foo\nbar\nbaz"))
        expected = f"Created a new list for {OWNER.name}\n" \
                   ":white_large_square: foo    (1)\n" \
                   ":white_large_square: bar    (2)\n" \
                   ":white_large_square: baz    (3)"
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
