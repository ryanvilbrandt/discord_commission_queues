from json import loads

import discord
from discord.ext.commands import Bot

from src.bot.commands import Commands

VERSION = (0, 1, 0)

with open("conf/credentials.json") as f:
    json = loads(f.read())
    PREFIX = json["prefix"]
    TOKEN = json["token"]
    MASTER_ID = json["master_id"]


def init_bot():
    return Bot(command_prefix=PREFIX)


def load_commands(bot):
    bot.add_cog(Commands(bot))

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(PREFIX + "help"))
        print(f"{bot.user.name} has connected to Discord!")

    @bot.command(name='version')
    async def version(context):
        await context.send("Version " + ".".join([str(c) for c in VERSION]))

    @bot.command(name='logout')
    async def logout(context):
        if context.author.id == MASTER_ID:
            print("Logging out...")
            await bot.change_presence(status=discord.Status.offline)
            await bot.logout()
        else:
            await context.author.send("You're not my real dad!")
            print("Fake dad tried to shut me down. :( {}".format(context.author.id))


def run_bot():
    bot = init_bot()
    load_commands(bot)
    bot.run(TOKEN)
