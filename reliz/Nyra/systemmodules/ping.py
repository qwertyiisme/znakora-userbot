import time

from ctx import START_TIME, edit, fmt_uptime


def _measure(bot):
    start = time.perf_counter()
    bot.call("get_me")
    return round((time.perf_counter() - start) * 1000)


def setup(bot, router, loader):
    @router.command(".ping", help="пинг до сервера Знакоры")
    def ping(message):
        try:
            ms = _measure(bot)
            uptime = fmt_uptime(time.monotonic() - START_TIME)
            edit(bot, message, f"Pong: {ms} ms\nUptime: {uptime}")
        except Exception as e:
            print("Ошибка ответа:", e)
            raise
