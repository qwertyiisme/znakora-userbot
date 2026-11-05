from ctx import BOT_NAME, CHANNEL, CREATOR, edit, load_ids


def setup(bot, router, loader):
    @router.command(".ubinfo", help="инфо о юзерботе")
    def ubinfo(message):
        reg = loader.ctx.registry
        text = (f"🌸 {BOT_NAME} — юзербот\n"
                f"Создатель: {CREATOR}\n"
                f"Канал: {CHANNEL}\n\n"
                f"Команд: {len(reg.commands)}\n"
                f"Чатов в списке: {len(load_ids())}\n")
        edit(bot, message, text)
