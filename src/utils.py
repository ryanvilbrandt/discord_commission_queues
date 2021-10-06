import re
from datetime import datetime
from enum import Enum
from typing import NamedTuple, Tuple

from discord import Embed

CHANNELS = {
    "incoming-commissions": "!Any artist",
    "caytlins-queue": "Caytlin Vilbrandt",
    "izzys-queue": "IzzySqueakzy",
    "laurens-queue": "Lauren Pierre",
    "scotts-queue": "Scott Fraser",
    "knacks-queue": "Knack Whittle",
    "jonas-queue": "Jonas",
    "voided-queue": "!Void",
    "bot-spam": "Trick-Candle",
}

USERS = {
    255143773577805836: "Caytlin Vilbrandt",
    122346745773424640: "IzzySqueakzy",
    460147480856756234: "Lauren Pierre",
    111219993600892928: "Scott Fraser",
    308753138872221696: "Knack Whittle",
    188456317004939264: "Jonas",
    235133902895841281: "Trick-Candle"
}


COLORS = [
    0xFF0000,
    0xFFA500,
    0xFFFF00,
    0x008000,
    0x00FFFF,
    0x0000FF,
    0x800080,
    0xEE82EE,
]


class StatusTuple(NamedTuple):
    color: int
    name: str
    emoji: str


class Status(Enum):
    ClaimableAnyone = StatusTuple(0x55ACEE, "Claimable by Anyone", "🔵")
    ClaimableExclusive = StatusTuple(0xAA8ED6, "Claimable Only by {}", "🟣")
    Invoiced = StatusTuple(0xFDCB58, "Invoiced", "🟡")
    Paid = StatusTuple(0x78B159, "Paid", "🟢")
    Finished = StatusTuple(0xE6E7E8, "Done", "⚪")


class BotError(Exception):
    pass


def build_embed(id: int, timestamp: str, name: str, email: str, description: str, expression: str, notes: str,
                reference_images: str, artist_choice: str, twitch: str, twitter: str, discord: str, hidden: bool,
                allow_any_artist: bool, invoiced: bool, paid: bool, finished: bool, **kwargs) -> Tuple[str, Embed]:
    # print("Unused kwargs: {}".format(kwargs))

    if finished:
        status = Status.Finished
    elif paid:
        status = Status.Paid
    elif invoiced:
        status = Status.Invoiced
    elif allow_any_artist:
        status = Status.ClaimableAnyone
    else:
        status = Status.ClaimableExclusive

    color = status.value.color
    status_name = status.value.name
    if status == Status.ClaimableExclusive:
        status_name = status_name.format(artist_choice)
    emoji = status.value.emoji

    content = "{} Commission for {} (#{} {})".format(emoji, name, id, email)

    embed = Embed(
        type="rich",
        description="",
        color=color,
        timestamp=ts_to_dt(timestamp)
    )
    trunc = False  # A message was truncated
    if not hidden:
        trunc = add_field(embed, "Status", status_name, False) or trunc
        if description:
            trunc = add_field(embed, "Character description", description, False) or trunc
        if expression:
            trunc = add_field(embed, "Specific expression", expression, False) or trunc
        if notes:
            trunc = add_field(embed, "Additional notes", notes, False) or trunc
        if reference_images:
            trunc = add_field(embed, "Reference images", reference_images, False) or trunc
        if twitch:
            trunc = add_field(embed, "Twitch username", twitch, True) or trunc
        if twitter:
            trunc = add_field(embed, "Twitter username", twitter, True) or trunc
        if discord:
            trunc = add_field(embed, "Discord handle", discord, True) or trunc
        trunc = add_field(embed, "Artist requested", artist_choice, False) or trunc
        url = get_url(reference_images)
        if url:
            embed.set_thumbnail(url=url)
    else:
        embed.description = "<hidden>"

    return content, embed


def add_field(embed: Embed, name: str, value: str, inline=False, force_add=False) -> bool:
    message_truncated = False
    if len(value) > 1024:
        value = value[:1021] + "..."
        message_truncated = True
    if value or force_add:
        embed.add_field(
            name=name,
            value=value,
            inline=inline
        )
    return message_truncated


def get_color(counter: int) -> int:
    return COLORS[counter % len(COLORS)]


def get_url(text: str) -> str:
    """
    Gets first URL-like string from the given text
    :param text:
    :return:
    """
    m = re.search(r"(?P<url>https?://[^\s'\",]+)", text)
    return m.group("url") if m else None


def get_channel_name(i_want_this_artist: str) -> str:
    for channel_name, artist_name in CHANNELS.items():
        if artist_name == i_want_this_artist:
            return channel_name
    return "incoming-commissions"


def ts_to_dt(ts):
    return datetime.strptime(ts, "%m/%d/%Y %H:%M:%S")


def get_name_by_member_id(member_id: int):
    return USERS.get(member_id)
