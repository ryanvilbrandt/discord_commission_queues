import re
from datetime import datetime
from enum import Enum
from json import loads
from typing import NamedTuple, Tuple, List

from discord import Embed

CHANNELS = {}

USERS = {}


def load_config(filepath="conf/config.json") -> dict:
    global CHANNELS, USERS
    with open(filepath) as f:
        j = loads(f.read())
        CHANNELS = j["channels"]
        USERS = j["users"]
    return j


class StatusTuple(NamedTuple):
    color: int
    name: str
    emoji: str
    sort_key: int


class Status(Enum):
    ClaimableAnyone = StatusTuple(0x55ACEE, "Claimable by Anyone", "🔵", 0)
    ClaimableExclusive = StatusTuple(0xAA8ED6, "Claimable Only by {}", "🟣", 1)
    Accepted = StatusTuple(0xF4900C, "Claimed", "🟠", 2)
    Invoiced = StatusTuple(0xFDCB58, "Invoiced", "🟡", 3)
    Paid = StatusTuple(0x78B159, "Paid", "🟢", 4)
    Finished = StatusTuple(0xE6E7E8, "Done", "⚪", 5)


class BotError(Exception):
    pass


def get_status(allow_any_artist: bool, accepted: bool, invoiced: bool, paid: bool, finished: bool, **kwargs) -> Status:
    if finished:
        return Status.Finished
    elif paid:
        return Status.Paid
    elif invoiced:
        return Status.Invoiced
    elif accepted:
        return Status.Accepted
    elif allow_any_artist:
        return Status.ClaimableAnyone
    else:
        return Status.ClaimableExclusive


def build_embed(id: int, timestamp: str, name: str, email: str, description: str, expression: str, notes: str,
                reference_images: str, artist_choice: str, twitch: str, twitter: str, discord: str, hidden: bool,
                allow_any_artist: bool, accepted: bool, invoiced: bool, paid: bool, finished: bool, specialty: bool,
                **kwargs) -> Tuple[str, Embed]:
    # print("Unused kwargs: {}".format(kwargs))

    status = get_status(allow_any_artist, accepted, invoiced, paid, finished)

    color = status.value.color
    status_name = status.value.name
    if status == Status.ClaimableExclusive:
        status_name = status_name.format(artist_choice)
    if not allow_any_artist:
        status_name += " 🌟"
    emoji = status.value.emoji

    if specialty:
        commission_type = ":frame_photo: Specialty commission"
    else:
        commission_type = "Commission"
    content = "{} {} for {} (#{})".format(emoji, commission_type, name, id)

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


def get_url(text: str) -> str:
    """
    Gets first URL-like string from the given text
    :param text:
    :return:
    """
    m = re.search(r"(?P<url>https?://[^\s'\",]+)", text)
    return m.group("url") if m else None


def build_commissions_status_page(commissions: List[dict]) -> str:
    s = "Commissions status:\n```"
    row_fmt = "\n {:^02} | {:^24} | {:^36} | {:^20}"
    s += row_fmt.format("ID", "NAME", "STATUS", "ASSIGNED TO")
    row_fmt = row_fmt.replace("^", "<")
    for commission in commissions:
        commission["status"] = get_status(**commission)
    sorted_commissions = sorted(commissions, key=lambda c: c["status"].value.sort_key)
    finished_commissions = 0
    for commission in sorted_commissions:
        if commission["status"] == Status.Finished:
            finished_commissions += 1
            continue
        if commission["channel_name"] == "voided-queue":
            status_name = "Voided"
        else:
            status_name = commission["status"].value.name.format(commission["assigned_to"])
        s += row_fmt.format(
            commission["id"],
            commission["name"],
            "{} {}".format(commission["status"].value.emoji, status_name),
            str(commission["assigned_to"])
        )
    s += "\n\nFinished commissions: {}".format(finished_commissions)
    s += "\n```"
    return s


def get_channel_name(i_want_this_artist: str) -> str:
    for channel_name, artist_name in CHANNELS.items():
        if artist_name == i_want_this_artist:
            return channel_name
    return "incoming-commissions"


def ts_to_dt(ts):
    return datetime.strptime(ts, "%m/%d/%Y %H:%M:%S")


def get_name_by_member_id(member_id: int):
    return USERS.get(str(member_id))
