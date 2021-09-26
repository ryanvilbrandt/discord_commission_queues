import traceback
from time import ctime

from discord import Message
from discord.ext.commands import Context, Cog, command

from src.bot import functions


class Commands(Cog):

    def __init__(self, bot):
        self.bot = bot
        functions.check_version()

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

    @command(name='newlist', help="Create a new list")
    async def new_list(self, context: Context):
        response_message = await self.handle_command(context, functions.new_list)
        if response_message:
            functions.set_last_message_id(context, context.author, response_message)
