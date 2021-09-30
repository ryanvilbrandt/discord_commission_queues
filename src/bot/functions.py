import os
from enum import Enum
from json import loads
from typing import Iterable

from discord import Message, Emoji
from discord.ext.commands import Bot
from discord.utils import get as discord_get
from googleapiclient.discovery import build

from src.db.db import Db

GOOGLE_SHEETS_DEVELOPER_KEY = None
SHEET_ID = None


class Reaction(Enum):
    ACCEPTED = "✅"
    REJECTED = "❌"


class Functions:
    channels = {
        "incoming-commissions": None,
        "current-queues": None,
        "bot-spam": None,
    }
    emoji_cache = {}

    def __init__(self, bot: Bot):
        self.check_version()
        self.bot = bot

    def init(self):
        self.save_channels()

    @staticmethod
    def check_version():
        with Db() as db:
            db.check_version()

    def save_channels(self):
        channel_list = self.bot.get_all_channels()
        for channel in channel_list:
            if channel.name in self.channels:
                self.channels[channel.name] = channel.id
        print(self.channels)

    def get_custom_emoji(self, emoji_name: str) -> Emoji:
        if emoji_name not in self.emoji_cache:
            for guild in self.bot.guilds:
                emoji = discord_get(guild.emojis, name=emoji_name)
                if emoji:
                    self.emoji_cache[emoji_name] = emoji
                    break
            else:
                raise ValueError("No emoji found for {}".format(emoji_name))
        return self.emoji_cache[emoji_name]

    async def send_to_channel(self, channel_name: str, text: str, message_name: str = None,
                              reactions: Iterable[Reaction] = None) -> Message:
        channel = self.bot.get_channel(self.channels[channel_name])
        with Db() as db:
            message, message_id = None, None
            # Check if message has already been posted, if so get message object and edit instead
            if message_name:
                message_id = db.get_message_id(channel_name, message_name)
                message = await channel.fetch_message(message_id)
            # If a previous message wasn't retrieved, send a new message, otherwise edit existing message
            if message is None:
                message = await channel.send(text)
            else:
                await message.edit(content=text)
            # If a message_name is defined and the message wasn't pulled from an already existing message,
            # save message_id
            if message_name and message_id != message.id:
                db.set_message_id(channel_name, message_name, message.id)
            # Add reactions if any
            if reactions:
                for reaction in reactions:
                    await message.add_reaction(reaction.value)
            return message

    def update_commissions_information(self):
        rows = self.get_commissions_info_from_spreadsheet()
        self.update_commissions_db(rows)

    def get_commissions_info_from_spreadsheet(self):
        print("Loading Google Sheet of commission info...")
        range = "Form Responses 1!A2:L"
        service = build('sheets', 'v4', developerKey=GOOGLE_SHEETS_DEVELOPER_KEY)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=range).execute()
        print(result["values"])
        return result["values"]

    def update_commissions_db(self, rows):
        with Db() as db:
            for row in rows:
                del row[1]
                if not db.check_for_commission(row[0], row[1]):
                    db.add_commission(row)

    def update_commissions_messages(self):
        pass


if __name__ == "__main__":
    os.chdir("../..")
    with open("conf/credentials.json") as f:
        json = loads(f.read())
        GOOGLE_SHEETS_DEVELOPER_KEY = json["developer_key"]
        SHEET_ID = json["spreadsheet_id"]

    # with Db() as db:
    #     db.print_tables()
    f = Functions(None)
    f.update_commissions_information()
