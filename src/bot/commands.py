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

    @loop(seconds=10)
    async def update_loop(self):
        await self.f.update_commissions_information()

    @update_loop.before_loop
    async def update_loop_before(self):
        await self.bot.wait_until_ready()

    @command(name="test")
    async def test_command(self, context: Context):
        # await self.send_to_channel("bot-spam", "I BEEN EDITED", message_name="Lauren",
        #                            reactions=[Reaction.ACCEPTED, Reaction.REJECTED])
        await self.f.update_commissions_information()
        # embed, view = build_embed("10/03/2021 15:36:00", "abc@gmail.com", 2, "abcd", "", "", "", "", "", "", "",
        #                           False, False, False, False)
        # await self.f.send_to_channel("bot-spam", embed, view)

    @command(name="cleanup")
    async def cleanup(self, context: Context):
        await self.f.cleanup_channels()
