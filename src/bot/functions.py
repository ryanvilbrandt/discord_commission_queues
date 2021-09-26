from re import match

from discord import Message
from discord.ext.commands import Context

from src.db.db import Db


def check_version():
    with Db() as db:
        db.check_version()


def new_list(context, owner: Message.author, message):
    if message == "":
        return "I need items to make a list. Put each separate item on a new line."
    task_names = message.split("\n")
    with Db() as db:
        db.add_owner(owner.id, owner.name)
        task_ids = db.add_tasks(task_names, owner.id)
        db.new_list(task_ids, owner.id)
        return f"Created a new list for {owner.name}\n" + print_task_list(db, owner), None, None
