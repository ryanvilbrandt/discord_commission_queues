import sqlite3
from json import dumps, loads
from typing import List, Optional

from src.db.build_db import show_tables

VERSION_NEEDED = 1


class Db:

    def __init__(self, filename="database_files/main.db", auto_commit=True):
        self.conn = sqlite3.connect(filename)
        self.cur = self.conn.cursor()
        self.check_version()
        self.auto_commit = auto_commit

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type:
                    self.conn.rollback()
                elif self.auto_commit:
                    self.conn.commit()
            finally:
                self.conn.close()

    def check_version(self):
        sql = "SELECT version FROM version;"
        version = self.cur.execute(sql).fetchone()[0]
        if not version == VERSION_NEEDED:
            raise ValueError(f"Incorrect DB version: {version} != {VERSION_NEEDED}")

    def print_tables(self):
        import pandas
        tables = ["commissions", "message_ids"]
        pandas.set_option("display.width", None)
        for t in tables:
            print(" {} ".format(t).center(50, "="))
            print(pandas.read_sql_query(f"SELECT * FROM {t}", self.conn))
            print('')

    def get_message_id(self, channel_name, message_name):
        sql = "SELECT id FROM message_ids WHERE channel=? AND name=?;"
        return self.cur.execute(sql, [channel_name, message_name]).fetchone()[0]

    def set_message_id(self, channel_name, message_name, message_id):
        sql = "INSERT INTO message_ids VALUES (?, ?, ?);"
        self.cur.execute(sql, [channel_name, message_name, message_id])


if __name__ == "__main__":
    with Db(filename=r"..\..\database_files\main.db") as db:
        db.print_tables()
