import traceback
from time import ctime
from typing import Iterable

from discord import Message
from discord.ext.commands import Context, Cog, command, Bot

from src.bot import functions
from src.bot.functions import Functions, Reaction
from src.db.db import Db


class Commands(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.f = Functions(bot)

    def init(self):
        self.f.init()

    async def send_to_channel(self, channel_name: str, message: str, message_name: str=None, 
                              reactions: Iterable[Reaction]=None) -> Message:
        return await self.f.send_to_channel(channel_name, message, message_name, reactions)

    @staticmethod
    async def handle_command(context, func) -> Message:
        cmd = context.prefix + context.command.name
        # Get everything after the command
        message = context.message.content[len(cmd):].strip()
        try:
            output, edit, message_id = func(context, context.author, message)
            if message_id:
                retrieved_message = await context.fetch_message(message_id)
                await retrieved_message.edit(content=edit)
            if output:
                return await context.send(output)
        except Exception as e:
            print(ctime())
            traceback.print_exc()
            await context.send(e.args[0])
            print()

    @command(name="test")
    async def test_command(self, context: Context):
        # await self.send_to_channel("bot-spam", "I BEEN EDITED", message_name="Lauren",
        #                            reactions=[Reaction.ACCEPTED, Reaction.REJECTED])
        with Db() as db:
            db.print_tables()
        self.f.update_commissions_information()

    @command(name='newlist', help="Create a new list")
    async def new_list(self, context: Context):
        response_message = await self.handle_command(context, functions.new_list)
        if response_message:
            functions.set_last_message_id(context, context.author, response_message)
