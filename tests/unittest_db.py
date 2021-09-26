import os
import unittest
from datetime import datetime

from src.db.db import Db

OWNER_ID1 = -1
OWNER_NAME1 = "FunctionalTestUser1"
OWNER_ID2 = -2
OWNER_NAME2 = "FunctionalTestUser2"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def epoch_to_ts(epoch: int) -> str:
    return dt_to_ts(epoch_to_dt(epoch))


def epoch_to_dt(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch)


def ts_to_epoch(ts: str) -> int:
    return int(ts_to_dt(ts).timestamp())


def ts_to_dt(ts: str, fmt=TIME_FORMAT) -> datetime:
    return datetime.strptime(ts, fmt)


def dt_to_epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def dt_to_ts(dt: datetime) -> str:
    return dt.strftime(TIME_FORMAT)


def now_epoch() -> int:
    return dt_to_epoch(now_dt())


def now_ts() -> str:
    return dt_to_ts(now_dt())


def now_dt() -> datetime:
    return datetime.utcnow()


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Change pwd to root folder, same as when main.py is run
        os.chdir("..")

    def setUp(self):
        self.db = Db()

    def tearDown(self):
        self.db.conn.rollback()
        self.db.conn.close()

    def test_get_list_items_no_list(self):
        self.assertIsNone(self.db.get_list_items(OWNER_ID1))

    def test_add_new_list(self):
        self.db.new_list([1, 2, 3], OWNER_ID1)
        current_time = now_ts()
        retrieved_list = self.db.get_list(OWNER_ID1)
        self.assertEqual([[1, 2, 3], OWNER_ID1, current_time, current_time], retrieved_list)
        retrieved_list = self.db.get_list_items(OWNER_ID1)
        self.assertEqual([1, 2, 3], retrieved_list)

    def test_add_and_replace_new_list(self):
        self.db.new_list([1, 2, 3], OWNER_ID1)
        self.db.new_list([4, 5, 6], OWNER_ID1)
        retrieved_list = self.db.get_list_items(OWNER_ID1)
        self.assertEqual([4, 5, 6], retrieved_list)

    def test_update_list(self):
        self.db.new_list([1, 2, 3], OWNER_ID1)
        self.db.update_list_items([7, 8, 9], OWNER_ID1)
        retrieved_list = self.db.get_list_items(OWNER_ID1)
        self.assertEqual([7, 8, 9], retrieved_list)

    def test_get_last_message_id(self):
        self.db.new_list([1, 2, 3], OWNER_ID1)
        channel_name1 = "channel_name1"
        last_message_id1 = 1111111
        channel_name2 = "channel_name2"
        last_message_id2 = 2222222
        self.assertIsNone(self.db.get_last_message_id(OWNER_ID1, channel_name1))
        self.db.set_last_message_id(OWNER_ID1, channel_name1, last_message_id1)
        self.assertEqual(last_message_id1, self.db.get_last_message_id(OWNER_ID1, channel_name1))
        self.assertIsNone(self.db.get_last_message_id(OWNER_ID1, channel_name2))
        self.db.set_last_message_id(OWNER_ID1, channel_name2, last_message_id2)
        self.assertEqual(last_message_id1, self.db.get_last_message_id(OWNER_ID1, channel_name1))
        self.assertEqual(last_message_id2, self.db.get_last_message_id(OWNER_ID1, channel_name2))


if __name__ == "__main__":
    unittest.main()
