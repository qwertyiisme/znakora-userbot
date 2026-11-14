from ctx import edit


def _commands_text(registry):
    groups = {}
    for name in sorted(registry.commands):
        item = registry.commands[name]
        groups.setdefault(item["module"], []).append((name, item["help"] or ""))
    lines = []
    for module in sorted(groups):
        lines.append(f"## {module}")
        for name, h in groups[module]:
            lines.append(f"  {name} — {h}")
    return "\n".join(lines)


def setup(bot, router, loader):
    def show_module_help(module_name):
        reg = loader.ctx.registry
        commands = []
        for name in sorted(reg.commands):
            item = reg.commands[name]
            if item["module"].lower() == module_name:
                cmd = f"`{name}`"
                if item["help"]:
                    cmd += f" — {item['help']}"
                commands.append(cmd)

        if not commands:
            return None

        header = f"**{module_name} — справка**"
        return header + "\n\n" + "\n".join(commands)

    @router.command(".elp", help="список команд юзербота")
    def elp_cmd(message):
        arg = message["text"][5:].strip().lower()
        if arg == "eval":
            help_text = (
                "**Eval модуль — справка**\n\n"
                "`.e <код>` — выполнить Python код\n"
                "`.ebash <команда>` — выполнить shell команду\n\n"
                "**Отправка файлов через .e:**\n"
                "`.e send <путь> [подпись]` — отправить как документ\n"
                "`.e sendphoto <путь> [подпись]` — отправить как фото\n"
                "`.e sendvideo <путь> [подпись]` — отправить как видео\n"
                "`.e sendvoice <путь>` — отправить как голосовое\n"
                "`.e sendnote <путь>` — отправить как кружок"
            )
            edit(bot, message, help_text)
            return
        if arg:
            module_help = show_module_help(arg)
            if module_help:
                edit(bot, message, module_help)
                return
        edit(bot, message, _commands_text(loader.ctx.registry) or "пусто")

    @router.command(".help", help="список команд юзербота")
    def help_cmd(message):
        arg = message["text"][6:].strip().lower()
        if arg == "eval":
            help_text = (
                "**Eval модуль — справка**\n\n"
                "`.e <код>` — выполнить Python код\n"
                "`.ebash <команда>` — выполнить shell команду\n\n"
                "**Отправка файлов через .e:**\n"
                "`.e send <путь> [подпись]` — отправить как документ\n"
                "`.e sendphoto <путь> [подпись]` — отправить как фото\n"
                "`.e sendvideo <путь> [подпись]` — отправить как видео\n"
                "`.e sendvoice <путь>` — отправить как голосовое\n"
                "`.e sendnote <путь>` — отправить как кружок"
            )
            edit(bot, message, help_text)
            return
        if arg:
            module_help = show_module_help(arg)
            if module_help:
                edit(bot, message, module_help)
                return
        edit(bot, message, _commands_text(loader.ctx.registry) or "пусто")
