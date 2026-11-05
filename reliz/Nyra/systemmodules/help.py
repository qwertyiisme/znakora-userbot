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
    @router.command(".elp", help="список команд юзербота")
    def elp_cmd(message):
        edit(bot, message, _commands_text(loader.ctx.registry) or "пусто")

    router.command(".help", help="список команд юзербота")(elp_cmd)
