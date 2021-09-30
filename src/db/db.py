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
        tables = ["commissions"]
        pandas.set_option("display.width", None)
        for t in tables:
            print(" {} ".format(t).center(50, "="))
            print(pandas.read_sql_query(f"SELECT * FROM {t}", self.conn))
            print('')

    def add_commission(self, row):
        sql = """
        INSERT INTO commissions(timestamp, email, twitch_username, twitter_username, discord_username, 
            reference_images, description, expression, notes, artist_of_choice, if_queue_is_full) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        values = row.copy()
        if len(values) == 10:
            values.append(None)
        print(f"Adding to DB: {values}")
        return self.cur.execute(sql, values)

    def check_for_commission(self, timestamp, email):
        sql = """
            SELECT COUNT(*) FROM commissions WHERE timestamp=? AND email=?;
        """
        result = self.cur.execute(sql, [timestamp, email]).fetchone()[0]
        print(f"({timestamp}, {email}) = {result}")
        return result


if __name__ == "__main__":
    with Db(filename=r"..\..\database_files\main.db") as db:
        db.print_tables()
