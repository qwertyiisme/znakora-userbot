from ctx import edit
from modloader import CFG


def _mask(key, value):
    if not value:
        return value
    secret = any(s in key.lower() for s in ("token", "pass", "secret", "key", "api"))
    return "••••••••" if secret else value


def setup(bot, router, loader):
    root = CFG.root()

    @router.command(".acfg", help="показать изменяемые переменные конфигурации")
    def acfg(message):
        lines = []
        for mod in root.modules():
            scope = root.scope(mod)
            section = []
            for var in scope.list_vars():
                val = scope.get(var, "")
                meta = scope.defaults.get(var, {})
                desc = meta.get("desc", "модуль")
                lines_var = f"{var} = {_mask(var, val)}"
                if desc:
                    lines_var += f"  # {desc}"
                section.append(lines_var)
            if section:
                lines.append(f"## {mod}")
                lines.extend("  " + s for s in section)
        edit(bot, message, "\n".join(lines) or "нет переменных")

    @router.command(".fcfg", help="присвоить переменной конфигурации значение: .fcfg <VAR> <VALUE>")
    def fcfg(message):
        parts = message["text"].split(maxsplit=2)
        if len(parts) < 3 or parts[0] != ".fcfg":
            edit(bot, message, ".fcfg <VAR> <VALUE>")
            return
        var, val = parts[1].strip(), parts[2].strip()
        owners = [m for m in root.modules() if var in root.scope(m).list_vars()]
        if not owners:
            edit(bot, message, f"❌ Неизвестная переменная: {var}")
            return
        if len(owners) > 1:
            edit(bot, message, f"❌ Переменная есть в нескольких модулях: {', '.join(owners)}. Уточните: .fcfg {owners[0]}/{var} <VALUE>")
            return
        root.scope(owners[0]).set(var, val)
        edit(bot, message, f"✅ {var} = {_mask(var, val)}")
