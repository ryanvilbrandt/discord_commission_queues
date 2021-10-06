from typing import Optional

from discord.ext.commands import Context, Cog, command, Bot
from discord.ext.tasks import loop

from src.bot.functions import Functions


class Commands(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.f = Functions(bot)

    async def init(self):
        await self.f.init()
        self.update_loop.start()

    @loop(seconds=60)
    async def update_loop(self):
        await self.f.update_commissions_information()

    @update_loop.before_loop
    async def update_loop_before(self):
        await self.bot.wait_until_ready()

    @command(name="update")
    async def update(self, context: Context, randomize=True):
        await self.f.update_commissions_information(randomize)

    @command(name="cleanup")
    async def cleanup(self, context: Context, queue: Optional[str]=None):
        await self.f.cleanup_channels(queue)

    @command(name="shuffle")
    async def cleanup(self, context: Context, queue: Optional[str]=None):
        await self.f.cleanup_and_resend_messages(True, queue)
