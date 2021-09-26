icons = {
    "ACCEPTED": ":white_check_mark:",
    "REJECTED": ":x:",
}


def get_icon(name):
    return icons[name]


class BotError(Exception):
    pass
