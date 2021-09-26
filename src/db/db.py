import sqlite3
from json import dumps, loads
from typing import List, Optional

VERSION_NEEDED = 1


class Db:

    def __init__(self, filename="database_files/list-keeper.db", auto_commit=True):
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
        tables = ["owners", "tasks", "lists"]
        pandas.set_option("display.width", None)
        for t in tables:
            print("="*20 + t + "="*20)
            print(pandas.read_sql_query(f"SELECT * FROM {t}", self.conn))
            print('')

    def new_list(self, list_items, owner_id):
        """
        :param owner_id:
        :param list_items: List of ints
        :return:
        """
        sql = """
        INSERT INTO lists (items, owner_id) VALUES (?, ?);
        """
        json_list = dumps(list_items)
        try:
            self.cur.execute(sql, [json_list, owner_id])
            return
        except sqlite3.IntegrityError:
            pass

        sql = """
        UPDATE lists 
        SET
          items = ?,
          created_ts = CURRENT_TIMESTAMP,
          updated_ts = CURRENT_TIMESTAMP
        WHERE
          owner_id = ? 
        """
        self.cur.execute(sql, [json_list, owner_id])

    def get_list(self, owner_id):
        sql = "SELECT items, owner_id, created_ts, updated_ts FROM lists WHERE owner_id = ?"
        response = list(self.cur.execute(sql, [owner_id]).fetchone())
        response[0] = loads(response[0])
        return response

    def get_list_items(self, owner_id) -> Optional[List[int]]:
        sql = "SELECT items FROM lists WHERE owner_id = ?"
        response = self.cur.execute(sql, [owner_id]).fetchone()
        if response is None:
            return None
        return loads(response[0])

    def update_list_items(self, list_items, owner_id):
        sql = """
        UPDATE lists 
        SET
          items = ?,
          updated_ts = CURRENT_TIMESTAMP
        WHERE
          owner_id = ? 
        """
        json_list = dumps(list_items)
        self.cur.execute(sql, [json_list, owner_id])

    def get_last_message_id(self, owner_id, channel_id):
        sql = "SELECT last_messages FROM lists WHERE owner_id=?"
        last_messages = loads(self.cur.execute(sql, [owner_id]).fetchone()[0])
        return last_messages.get(str(channel_id))

    def set_last_message_id(self, owner_id, channel_id, message_id):
        sql = "SELECT last_messages FROM lists WHERE owner_id=?"
        last_messages = loads(self.cur.execute(sql, [owner_id]).fetchone()[0])
        last_messages[str(channel_id)] = message_id
        sql = "UPDATE lists SET last_messages=? WHERE owner_id=?"
        self.cur.execute(sql, [dumps(last_messages), owner_id])


if __name__ == "__main__":
    with Db(filename=r"..\..\database_files\main.db") as db:
        db.print_tables()
