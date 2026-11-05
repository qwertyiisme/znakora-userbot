import base64
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import traceback

from cryptography.fernet import Fernet, InvalidToken

from znakora_userbot.tools import Router


class CommandRegistry:
    def __init__(self):
        self.commands = {}

    def add(self, name, help_text=None, module="core"):
        self.commands[name] = {"help": (help_text or "").strip() or None, "module": module}

    def remove_module(self, module):
        for name in [n for n, i in list(self.commands.items()) if i["module"] == module]:
            del self.commands[name]

    def render(self):
        lines = []
        for name in sorted(self.commands):
            item = self.commands[name]
            part = f"• {name}"
            if item["help"]:
                part += f" — {item['help']}"
            if item["module"] != "core":
                part += f" (модуль: {item['module']})"
            lines.append(part)
        return "\n".join(lines)


class ScopedCfg:
    def __init__(self, store, module):
        self.store = store
        self.module = module
        self.fernet = store._fernet_for(module)
        self.defaults = {}
        self.enc = {}

    def default(self, var, value="", desc="", secret=False):
        self.defaults[var] = {"desc": desc or "", "secret": bool(secret)}
        if var not in self.enc and value not in ("", None):
            self.set(var, value, _save=True)

    def get(self, var, fallback=None):
        if var in self.enc:
            try:
                return self.fernet.decrypt(self.enc[var].encode()).decode()
            except (InvalidToken, ValueError):
                print(f"[cfg {self.module}] не удалось расшифровать {var}")
                return fallback
        if var in self.store.common.enc:
            return self.store.common.get(var)
        return fallback

    def set(self, var, value, _save=True):
        value = str(value)
        self.enc[var] = self.fernet.encrypt(value.encode()).decode()
        if _save:
            self.store.save()
        return value

    def delete(self, var):
        self.enc.pop(var, None)
        self.store.save()

    def list_vars(self):
        return sorted(set(self.defaults) | set(self.enc))


class CfgStore:
    def __init__(self, key_path=None, data_path=None):
        base = os.path.join(os.path.expanduser("~"), ".config", "znakora")
        self.key_path = key_path or os.path.join(base, "nyra.cfgkey")
        self.data_path = data_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".cfg.json")
        self.master = self._load_master()
        self.scopes = {}
        self.common = self.scoped("common")

    # старый API модулей, не перешедших на скоупы: общий namespace "common"
    def get(self, key, default=None):
        return self.common.get(key, default)

    def set(self, key, value):
        return self.common.set(key, value)

    def scoped(self, module):
        if module not in self.scopes:
            self.scopes[module] = ScopedCfg(self, module)
        return self.scopes[module]

    def _fernet_for(self, module):
        digest = hashlib.sha256()
        digest.update(b"mod:" + module.encode())
        digest.update(self.master)
        return Fernet(base64.urlsafe_b64encode(digest.digest()))

    def _load_master(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                data = f.read().strip()
            try:
                return base64.urlsafe_b64decode(data)
            except ValueError:
                pass
        raw = os.urandom(32)
        enc_dir = os.path.dirname(self.key_path)
        os.makedirs(enc_dir, mode=0o700, exist_ok=True)
        with open(self.key_path, "wb") as f:
            f.write(base64.urlsafe_b64encode(raw))
        os.chmod(self.key_path, 0o600)
        return raw

    def load(self):
        if not os.path.exists(self.data_path):
            return
        try:
            with open(self.data_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print("[cfg] файл конфигурации повреждён:", e)
            return
        mods = data.get("modules", {})
        broken = []
        for mod, sec in mods.items():
            scope = self.scoped(mod)
            for var, enc in (sec or {}).items():
                try:
                    scope.fernet.decrypt(enc.encode())
                    scope.enc[var] = enc
                except (InvalidToken, ValueError):
                    broken.append(f"{mod}.{var}")
        if broken:
            print("[cfg] не расшифровано:", ", ".join(broken))

    def save(self):
        mods = {m: dict(s.enc) for m, s in self.scopes.items()}
        payload = json.dumps({"version": 1, "modules": mods}, ensure_ascii=False)
        ddir = os.path.dirname(self.data_path)
        os.makedirs(ddir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=ddir, prefix=".cfg.", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.data_path)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise

    def modules(self):
        return sorted(self.scopes)


CFG = CfgStore()


class SafeRouter(Router):
    def __init__(self, bot, registry=None, name="?"):
        super().__init__(bot)
        self.registry = registry
        self.name = name

    def command(self, name, help=None):
        def decorate(handler):
            Router.command(self, name)(handler)
            if self.registry is not None:
                self.registry.add(name, help or getattr(handler, "__doc__", None), module=self.name)
            return handler
        return decorate

    def dispatch(self, message):
        if message.get("automated") or message.get("unavailable"):
            return
        for predicate, handler in list(self.rules):
            if predicate(message):
                try:
                    handler(message)
                except Exception:
                    print(f"[модуль {self.name}] ошибка в обработчике (сессия продолжает работать):")
                    traceback.print_exc()


class ModLoader:
    def __init__(self, bot, modules_dir, registry=None):
        self.bot = bot
        self.dir = os.path.abspath(modules_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.registry = registry
        self.loaded = {}

    def _pattern_ok(self, name):
        return bool(re.fullmatch(r"[a-z][a-z0-9_]*", name))

    def names(self):
        return sorted(self.loaded)

    def load_all(self):
        for fn in sorted(os.listdir(self.dir)):
            if fn.endswith(".py") and not fn.startswith("_"):
                try:
                    self.load(fn[:-3])
                except Exception:
                    print(f"[loader] не удалось загрузить {fn}:")
                    traceback.print_exc()

    def load(self, name):
        if not self._pattern_ok(name):
            raise ValueError(f"недопустимое имя модуля: {name!r}")
        path = os.path.join(self.dir, name + ".py")
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        if name in self.loaded:
            self.unload(name)
        before = list(self.bot._handlers["message"])
        if self.dir not in sys.path:
            sys.path.insert(0, self.dir)
        spec = importlib.util.spec_from_file_location(f"znakora_mod_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        router = SafeRouter(self.bot, self.registry, name)
        setup = getattr(module, "setup", None)
        if callable(setup):
            setup(self.bot, router, self)
        after = list(self.bot._handlers["message"])
        delta = [cb for cb in after if cb not in before]
        self.loaded[name] = {"module": module, "router": router, "callback": delta[0] if delta else None}
        print(f"[loader] модуль загружен: {name}")

    def unload(self, name):
        info = self.loaded.pop(name, None)
        if info is None:
            raise KeyError(name)
        cb = info["callback"]
        if cb is not None:
            try:
                self.bot._handlers["message"].remove(cb)
            except ValueError:
                pass
        close = getattr(info["module"], "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                traceback.print_exc()
        if self.registry is not None:
            self.registry.remove_module(name)
        print(f"[loader] модуль выгружен: {name}")

    def reload(self, name):
        self.load(name)
