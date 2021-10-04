import asyncio
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

    async def cleanup_and_resend_messages(self):
        await self.cleanup_channels()
        print("Resending commissions...")
        with Db() as db:
            for commission in db.get_all_commissions():
                print(f"Sending {commission}")
                await self.send_commission_embed(db, commission, set_counter=False)

    async def cleanup_channels(self):
        for channel_name, channel_id in self.channels.items():
            if channel_name == "bot-spam":
                continue
            print(f"Checking {channel_name}...")
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

    async def update_commissions_information(self):
        rows = self.get_commissions_info_from_spreadsheet()
        with Db() as db:
            for row in rows:
                timestamp, email = row[0], row[2]
                commission = db.get_commission_by_email(timestamp, email)
                if commission is None:
                    del row[1]  # Delete TOS agreement
                    commission = db.add_commission(row)
                    # Assign the commission to someone based on artist_choice
                    if commission["artist_choice"].startswith("Any artist"):
                        assigned_to = None
                    else:
                        assigned_to = commission["artist_choice"]
                    commission = db.assign_commission(assigned_to, timestamp, email)
                    await self.send_commission_embed(db, commission)
        print("Done processing new commissions")

    @staticmethod
    def get_commissions_info_from_spreadsheet():
        print("Loading Google Sheet of commission info...")
        sheet_range = "Form Responses 1!A2:L"
        service = build('sheets', 'v4', developerKey=GOOGLE_SHEETS_DEVELOPER_KEY)
        # Call the Sheets API
        sheet = service.spreadsheets()
        thing = sheet.values().get(spreadsheetId=SHEET_ID, range=sheet_range)
        result = thing.execute()["values"]
        print(f"Got {len(result)} results")
        return result

    async def send_commission_embed(self, db: Db, commission: Dict, set_counter=True):
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
            if commission["assigned_to"] is not None:
                print(f"A user ({member}) tried to claim a commission that was already claimed. How??")
                return False
            else:
                name = get_name_by_member_id(member.id)
                if name is None:
                    print(f"An invalid user ({member}) tried to claim a commission.")
                    return False
                else:
                    old_channel_name, old_message_id = commission["channel_name"], commission["message_id"]
                    db.assign_commission(name, message_id=message_id)
                    commission = db.accept_commission(message_id, accepted=True)
                    await self.send_commission_embed(db, commission)
                    await self.delete_message(old_channel_name, old_message_id)
                    return True

    @staticmethod
    def check_if_user_can_accept_reject(db: Db, member: Member, message_id: int, action: str):
        commission = db.get_commission_by_message_id(message_id)
        name = get_name_by_member_id(member.id)
        if name != commission["assigned_to"]:
            print(f"A user ({member} | {name}) tried to {action} a commission "
                  f"when it wasn't assigned to them ({commission['assigned_to']}).")
            return None
        return commission

    async def reject_commission(self, member: Member, message_id: int) -> bool:
        with Db() as db:
            commission = self.check_if_user_can_accept_reject(db, member, message_id, "reject")
            if not commission:
                return False
            old_channel_name, old_message_id = commission["channel_name"], commission["message_id"]
            db.assign_commission(None, message_id=message_id)
            commission = db.accept_commission(message_id, accepted=False)
            await self.send_commission_embed(db, commission)
            await self.delete_message(old_channel_name, old_message_id)
            return True

    def accept_commission(self, member: Member, message_id: int) -> Optional[dict]:
        with Db() as db:
            commission = self.check_if_user_can_accept_reject(db, member, message_id, "accept")
            if not commission:
                return None
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
