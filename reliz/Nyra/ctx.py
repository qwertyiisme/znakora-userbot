import json
import os
import sys
import time

BOT_NAME = "nyra"
CREATOR = "@qwertyiisme"
CHANNEL = "@nyra"
START_TIME = time.monotonic()
IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".chat_ids.json")


def load_ids():
    if os.environ.get("ZNAKORA_CHAT_IDS"):
        return [v.strip() for v in os.environ["ZNAKORA_CHAT_IDS"].split(",") if v.strip()]
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def edit(bot, message, text):
    bot.call("edit_message", chat_id=message["chat_id"], message_id=message["id"], text=text[:2000])


def fmt_uptime(seconds):
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}д")
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}м")
    parts.append(f"{secs}с")
    return " ".join(parts)


def restart(bot=None):
    if bot is not None:
        try:
            bot.close()
            print("[nyra] сессия закрыта")
        except Exception as e:
            print("[nyra] не удалось корректно закрыть сессию:", e)
    core = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core.py")
    os.execv(sys.executable, [sys.executable, core, *sys.argv[1:]])


class Ctx:
    def __init__(self, bot, registry, mod_loader=None, sys_loader=None):
        self.bot = bot
        self.registry = registry
        self.mod_loader = mod_loader
        self.sys_loader = sys_loader
