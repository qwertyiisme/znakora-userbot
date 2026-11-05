import getpass
import json
import os
import threading

from znakora_userbot import Client

import ctx
from ctx import BOT_NAME, Ctx, load_ids
from modloader import CFG, CommandRegistry, ModLoader

MAX_CHATS = 20
CRED_DIR = os.path.join(os.path.expanduser("~"), ".config", "znakora")
CRED_FILE = os.path.join(CRED_DIR, "nyra.json")


def load_creds():
    try:
        with open(CRED_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("email") and data.get("password"):
            return data
    except Exception:
        pass
    return {}


def save_creds(email, password):
    os.makedirs(CRED_DIR, mode=0o700, exist_ok=True)
    with open(CRED_FILE, "w", encoding="utf-8") as f:
        json.dump({"email": email, "password": password}, f)
    os.chmod(CRED_FILE, 0o600)


def save_ids(ids):
    with open(ctx.IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(ids, f)


def discover_ids(bot, limit=MAX_CHATS):
    ids = []
    before = None
    while len(ids) < limit:
        kwargs = {"before": before} if before else {}
        res = bot.call("discover_chats", **kwargs)
        for item in res.get("chats") or res.get("items") or []:
            cid = item.get("id") if isinstance(item, dict) else item
            if cid and cid not in ids:
                ids.append(cid)
        before = res.get("next_before") or res.get("cursor")
        if not before:
            break
    save_ids(ids[:limit])
    print(f"Список чатов обновлён ({len(ids)}).")
    return ids


def _refresh(bot):
    try:
        discover_ids(bot)
    except Exception as e:
        print("Не удалось обновить список чатов (кэш остался прежним):", e)


CAP_URL = os.environ.get("ZNAKORA_CAPABILITIES_URL", "https://www.znakora.ru/api/userbots/v1/capabilities")


def _persistence_supported():
    try:
        import json
        import urllib.request
        with urllib.request.urlopen(CAP_URL, timeout=10) as r:
            return bool(json.load(r).get("persistence_supported"))
    except Exception as e:
        print("[nyra] не удалось узнать возможности сервера:", e)
        return False


def _login(bot, email, password, name, scopes, chat_ids):
    persist = _persistence_supported()
    if not persist:
        print(f"[nyra] сохранение сессий недоступно, вхожу разово ({name})")
    try:
        bot.login(email, password, name=name, scopes=scopes, chat_ids=chat_ids,
                  persist_session=persist)
    except Exception as e:
        if getattr(e, "code", "") == "PERSISTENCE_NOT_SUPPORTED":
            print(f"[nyra] сервер отклонил persist, вхожу разово ({name})")
            bot.login(email, password, name=name, scopes=scopes, chat_ids=chat_ids,
                      persist_session=False)
        else:
            raise


def _ask_creds():
    creds = load_creds()
    had_saved = bool(creds)
    email = os.environ.get("ZNAKORA_EMAIL") or creds.get("email") or input("Email: ")
    password = os.environ.get("ZNAKORA_PASSWORD") or creds.get("password") or getpass.getpass("Пароль: ")
    return email, password, had_saved


def _wipe_creds():
    try:
        os.remove(CRED_FILE)
        print("[nyra] сохранённые данные входа удалены, повторите ввод")
    except OSError:
        pass


def main():
    from znakora_userbot import UserbotError

    while True:
        chat_ids_current = load_ids()
        email, password, had_saved = _ask_creds()
        try:
            if not chat_ids_current:
                print("Первый запуск: поиск чатов (нужен код запуска).")
                with Client() as bot:
                    _login(bot, email, password, "nyra-discovery", scopes=["chats.list"], chat_ids=[])
                    discover_ids(bot)
                chat_ids_current = load_ids()

            print("Запуск nyra.")
            CFG.load()
            with Client() as bot:
                _login(bot, email, password, BOT_NAME,
                       scopes=["chats.list", "events.read", "messages.edit", "messages.send",
                               "messages.delete", "files.write"],
                       chat_ids=chat_ids_current)

                if not had_saved:
                    save_creds(email, password)
                    print(f"Данные входа сохранены в {CRED_FILE} (не публикуйте этот файл).")

                threading.Thread(target=_refresh, args=(bot,), daemon=True).start()

                base = os.path.dirname(os.path.abspath(__file__))
                registry = CommandRegistry()
                mod_loader = ModLoader(bot, os.path.join(base, "modules"), registry)
                sys_loader = ModLoader(bot, os.path.join(base, "systemmodules"), registry, trusted=True)
                context = Ctx(bot, registry, mod_loader, sys_loader)
                mod_loader.ctx = context
                sys_loader.ctx = context

                sys_loader.load_all()
                mod_loader.load_all()
                try:
                    bot.run(include_own=True)
                    return
                except KeyboardInterrupt:
                    bot.stop()
                    return
        except UserbotError as e:
            bad_creds = getattr(e, "status", 0) == 401
            if bad_creds and not os.environ.get("ZNAKORA_PASSWORD"):
                if had_saved:
                    _wipe_creds()
                    continue
                print("[nyra] неверные данные входа, повторите")
                continue
            raise


if __name__ == "__main__":
    main()
