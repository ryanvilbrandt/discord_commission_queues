from json import loads
from time import sleep

import discord
from discord.ext.commands import Bot, Context

from src.bot import functions
from src.bot.commands import Commands

VERSION = (0, 1, 0)

with open("conf/credentials.json") as f:
    json = loads(f.read())
    PREFIX = json["prefix"]
    TOKEN = json["token"]
    MASTER_IDS = json["master_id"]
    functions.GOOGLE_SHEETS_DEVELOPER_KEY = json["developer_key"]
    functions.SHEET_ID = json["spreadsheet_id"]


def init_bot():
    return Bot(command_prefix=PREFIX)


def load_commands(bot):
    commands = Commands(bot)
    bot.add_cog(commands)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(PREFIX + "help"))
        await commands.init()
        print(f"{bot.user.name} has connected to Discord!")

    @bot.command(name='version')
    async def version(context: Context):
        await context.send("Version " + ".".join([str(c) for c in VERSION]))

    @bot.command(name='logout')
    async def logout(context: Context):
        if context.author.id in MASTER_IDS:
            await context.channel.send("Okay, Dad. Logging out...")
            print("Logging out...")
            await bot.change_presence(status=discord.Status.offline)
            sleep(1)
            await bot.close()
        else:
            # await context.author.send("You're not my real dad!")
            await context.channel.send("You're not my real dad!")
            print("Fake dad tried to shut me down. :( {}".format(context.author.id))


def run_bot():
    bot = init_bot()
    load_commands(bot)
    bot.run(TOKEN)
