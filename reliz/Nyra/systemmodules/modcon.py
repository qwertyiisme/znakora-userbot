import threading

from ctx import edit, restart


def _reload_many(ldr, names):
    ok, errs = [], []
    for name in names:
        try:
            ldr.reload(name)
            ok.append(name)
        except Exception as e:
            errs.append(f"{name}: {e}")
    res = ", ".join(ok) or "нет"
    if errs:
        res += "\n❌ " + "; ".join(errs)
    return res


def setup(bot, router, loader):
    @router.command(".mods", help="список загруженных модулей")
    def mods(message):
        c = loader.ctx
        lines = [
            "📦 Системные: " + (", ".join(c.sys_loader.names()) or "нет"),
            "📦 Модули: " + (", ".join(c.mod_loader.names()) or "нет"),
        ]
        edit(bot, message, "\n".join(lines))

    @router.command(".load", help="загрузить модуль из modules/<имя>.py")
    def load_cmd(message):
        parts = message["text"].split(maxsplit=1)
        if len(parts) < 2:
            edit(bot, message, ".load <имя>")
            return
        try:
            loader.ctx.mod_loader.load(parts[1].strip())
            edit(bot, message, f"✅ Модуль {parts[1].strip()} загружен")
        except Exception as e:
            edit(bot, message, f"❌ Не загрузить: {e}")

    @router.command(".unload", help="выгрузить модуль")
    def unload_cmd(message):
        parts = message["text"].split(maxsplit=1)
        if len(parts) < 2:
            edit(bot, message, ".unload <имя>")
            return
        try:
            loader.ctx.mod_loader.unload(parts[1].strip())
            edit(bot, message, f"🚫 Модуль {parts[1].strip()} выгружен")
        except Exception as e:
            edit(bot, message, f"❌ Не выгрузить: {e}")

    @router.command(".reload", help="перезагрузить модули (.reload), системные (.reload sys), всё (.reload all) или ядро (.reload core = рестарт)")
    def reload_cmd(message):
        parts = message["text"].split(maxsplit=1)
        arg = parts[1].strip() if len(parts) > 1 else ""
        c = loader.ctx
        if arg == "core":
            edit(bot, message, "🔁 Ядро перезагружается через рестарт…")
            threading.Thread(target=restart, args=(bot,), daemon=True).start()
            return
        if arg == "sys":
            edit(bot, message, "🔄 Системные перезагружены: " + _reload_many(c.sys_loader, list(c.sys_loader.loaded)))
            return
        if arg == "all":
            sys_res = _reload_many(c.sys_loader, list(c.sys_loader.loaded))
            usr_res = _reload_many(c.mod_loader, list(c.mod_loader.loaded))
            edit(bot, message, "🔄 Всё перезагружено.\nСистемные: " + sys_res + "\nМодули: " + usr_res)
            return
        if not arg:
            edit(bot, message, "🔄 Модули перезагружены: " + _reload_many(c.mod_loader, list(c.mod_loader.loaded)))
            return
        edit(bot, message, "🔄 Перезагружено: " + _reload_many(c.mod_loader, [arg]))

    @router.command(".restart", help="закрыть сессию и полностью перезапустить nyra")
    def restart_cmd(message):
        edit(bot, message, "🔁 Перезапускаюсь…")
        threading.Thread(target=restart, args=(bot,), daemon=True).start()
