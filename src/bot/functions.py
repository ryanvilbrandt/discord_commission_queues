from random import shuffle
from typing import Dict, Optional

from discord import Message, Emoji, Embed, Member
from discord.ext.commands import Bot
from discord.ui import View
from discord.utils import get as discord_get
from googleapiclient.discovery import build

from src.bot.embed_buttons import EmbedButtonsView
from src.db.db import Db
from src.utils import CHANNELS, build_embed, get_channel_name, get_name_by_member_id

GOOGLE_SHEETS_DEVELOPER_KEY = None
SHEET_ID = None


class Functions:
    channels = {}
    emoji_cache = {}

    def __init__(self, bot: Bot):
        with Db() as db:
            db.check_version()
        self.bot = bot

    async def init(self):
        self.save_channels()
        await self.cleanup_and_resend_messages()

    def save_channels(self):
        channel_list = self.bot.get_all_channels()
        for channel in channel_list:
            if channel.name in CHANNELS:
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

    async def cleanup_and_resend_messages(self, randomize=True, queue=None):
        await self.cleanup_channels(queue)
        print("Resending commissions...")
        with Db() as db:
            commissions = list(db.get_all_commissions_for_queue(queue) if queue else db.get_all_commissions())
            if randomize:
                shuffle(commissions)
            for commission in commissions:
                print(f"Sending {commission}")
                await self.send_commission_embed(db, commission, set_counter=False)

    async def cleanup_channels(self, queue: bool=None):
        for channel_name, channel_id in self.channels.items():
            if queue is not None and channel_name != queue:
                continue
            print(f"Cleaning {channel_name}...")
            channel = self.bot.get_channel(channel_id)
            async for message in channel.history():
                if message.author.name == "CommissionQueueBot":
                    await message.delete()

    async def send_to_channel(self, channel_name: str, embed: Embed, view: Optional[View]) -> Message:
        channel = self.bot.get_channel(self.channels[channel_name])
        return await channel.send(embed=embed, view=view)

    async def delete_message(self, channel_name: str, message_id: int):
        channel = self.bot.get_channel(self.channels[channel_name])
        message = await channel.fetch_message(message_id)
        await message.delete()

    async def update_commissions_information(self, randomize=True):
        rows = self.get_commissions_info_from_spreadsheet()
        if randomize:
            shuffle(rows)
        commissions_to_send = []
        with Db() as db:
            for row in rows:
                commission = db.get_commission_by_email(row[0], row[2])
                if commission is None:
                    # Add commissions to a list, so we can possibly randomize them before sending
                    commissions_to_send.append(self.prep_commission(db, row))
            if commissions_to_send:
                if randomize:
                    shuffle(rows)
                for commission in commissions_to_send:
                    await self.send_commission_embed(db, commission)
        print("Done processing new commissions")

    @staticmethod
    def prep_commission(db: Db, row: list) -> dict:
        del row[1]  # Delete TOS agreement
        timestamp, email = row[0], row[1]
        commission = db.add_commission(row)
        # Assign the commission to someone based on artist_choice
        if commission["artist_choice"].startswith("Any artist"):
            assigned_to = None
        else:
            assigned_to = commission["artist_choice"]
        commission = db.assign_commission(assigned_to, timestamp, email)
        # Set allow_any_artist flag
        allow_any_artist = "void" not in (commission.get("if_queue_is_full") or "").lower()
        return db.set_allow_any_artist(allow_any_artist, timestamp, email)

    @staticmethod
    def get_commissions_info_from_spreadsheet():
        print("Loading Google Sheet of commission info...")
        sheet_range = "Form Responses 1!A2:M"
        service = build('sheets', 'v4', developerKey=GOOGLE_SHEETS_DEVELOPER_KEY)
        # Call the Sheets API
        sheet = service.spreadsheets()
        thing = sheet.values().get(spreadsheetId=SHEET_ID, range=sheet_range)
        result = thing.execute()["values"]
        print(f"Got {len(result)} results")
        return result

    async def send_commission_embed(self, db: Db, commission: Dict, set_counter=True):
        if commission["assigned_to"] is None:
            channel_name = get_channel_name("!Any artist" if commission["allow_any_artist"] else "!Void")
        else:
            channel_name = get_channel_name(commission["assigned_to"])
        timestamp, email = commission["timestamp"], commission["email"]
        if set_counter:
            # Increment channel counter, to track how many messages were sent on this channel
            counter = db.increment_channel_counter(channel_name)
            # Update the counter value on the given commission, so it's passed to the build embed
            commission = db.update_commission_counter(timestamp, email, counter)
        # Build the embed and view data
        embed = build_embed(**commission)
        view = EmbedButtonsView(self, commission["assigned_to"] is None, **commission)
        # Send message to channel
        message = await self.send_to_channel(channel_name, embed, view)
        # Update the message ID for editing later
        db.update_message_id(timestamp, email, channel_name, message_id=message.id)

    async def claim_commission(self, member: Member, message_id: int) -> bool:
        with Db() as db:
            commission = db.get_commission_by_message_id(message_id)
            # The commission must not currently be assigned to anyone to allow a claim
            if commission["assigned_to"] is not None:
                print(f"A user ({member}) tried to claim a commission that was already claimed. How??")
                await member.send(
                    f"You tried to claim a commission that was already claimed. Please tell Trick-Candle how.",
                    delete_after=60
                )
                return False
            # The claiming user must have a channel assigned to them
            name = get_name_by_member_id(member.id)
            if name is None:
                print(f"An invalid user ({member}) tried to claim a commission.")
                await member.send("You cannot claim commissions.", delete_after=60)
                return False
            # If the commission is limited to a specific artist, the claiming artist must be that artist
            if not commission["allow_any_artist"] and commission["artist_choice"] != name:
                return False
            old_channel_name, old_message_id = commission["channel_name"], commission["message_id"]
            db.assign_commission(name, message_id=message_id)
            commission = db.accept_commission(message_id, accepted=True)
            await self.send_commission_embed(db, commission)
            await self.delete_message(old_channel_name, old_message_id)
            return True

    # @staticmethod
    # async def check_if_user_can_accept_reject(db: Db, member: Member, message_id: int, action: str):
    #     commission = db.get_commission_by_message_id(message_id)
    #     name = get_name_by_member_id(member.id)
    #     if name != commission["assigned_to"]:
    #         print(f"A user ({member} | {name}) tried to {action} a commission "
    #               f"when it wasn't assigned to them ({commission['assigned_to']}).")
    #         await member.send(f"You can't {action} a commission that isn't assigned to you.", delete_after=60)
    #         return None
    #     return commission

    async def reject_commission(self, member: Member, message_id: int) -> bool:
        with Db() as db:
            commission = db.get_commission_by_message_id(message_id)
            old_channel_name, old_message_id = commission["channel_name"], commission["message_id"]
            db.assign_commission(None, message_id=message_id)
            commission = db.accept_commission(message_id, accepted=False)
            await self.send_commission_embed(db, commission)
            await self.delete_message(old_channel_name, old_message_id)
            return True

    @staticmethod
    async def accept_commission(member: Member, message_id: int) -> Optional[dict]:
        with Db() as db:
            return db.accept_commission(message_id, accepted=True)

    @staticmethod
    async def show_commission(message_id: int) -> dict:
        with Db() as db:
            return db.hide_commission(message_id, False)

    @staticmethod
    async def hide_commission(message_id: int) -> dict:
        with Db() as db:
            return db.hide_commission(message_id, True)

    @staticmethod
    async def invoice_commission(message_id: int) -> dict:
        with Db() as db:
            return db.invoice_commission(message_id)

    @staticmethod
    async def pay_commission(message_id: int) -> dict:
        with Db() as db:
            return db.pay_commission(message_id)

    @staticmethod
    async def finish_commission(message_id: int) -> dict:
        with Db() as db:
            db.finish_commission(message_id)
            return db.hide_commission(message_id, hidden=True)
