import re
from datetime import datetime
from typing import List, Dict, Union

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


class BotError(Exception):
    pass


def build_embed(timestamp: str, email: str, counter: int, description: str, expression: str, notes: str,
                reference_images: str, artist_choice: str, twitch: str, twitter: str, discord: str, hidden: bool,
                **kwargs) -> Embed:
    embed = Embed(
        type="rich",
        title=f"Commission from {email}",
        description="",
        color=get_color(counter),
        timestamp=ts_to_dt(timestamp)
    )
    if hidden:
        embed.description = "Hidden, to show click the Show button below"
    else:
        if description:
            embed.add_field(name="Character description", value=description, inline=False)
        if expression:
            embed.add_field(name="Specific expression", value=expression, inline=False)
        if notes:
            embed.add_field(name="Additional notes", value=notes, inline=False)
        if reference_images:
            embed.add_field(name="Reference images", value=reference_images, inline=False)
        if twitch:
            embed.add_field(name="Twitch username", value=twitch, inline=True)
        if twitter:
            embed.add_field(name="Twitter username", value=twitter, inline=True)
        if discord:
            embed.add_field(name="Discord handle", value=discord, inline=True)
        embed.add_field(name="Artist requested", value=artist_choice, inline=False)
        url = get_url(reference_images)
        if url:
            embed.set_thumbnail(url=url)

    return embed


def add_field(fields: List[Dict[str, Union[str, bool]]], name: str, value: str, inline=False, force_add=False):
    if value or force_add:
        fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })


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
