# Nyra — Python Userbot для Знакоры

Юзербот на Python для автоматизации профиля в Знакоре (znakora.ru). Работает через официальный Python SDK 0.1.2.

## Возможности

- Авторизация email/пароль; первый запуск — код запуска из системного чата, дальше сессия сохраняется и восстанавливается сама
- Горячая загрузка/выгрузка модулей без перезапуска (`.load`, `.unload`, `.reload`)
- Системные модули в `systemmodules/`, пользовательские в `modules/` — 1 файл = 1 категория команд
- Шифрованная конфигурация: у каждого модуля свой ключ (Fernet, мастер-ключ в `~/.config/znakora/nyra.cfgkey`), значения хранятся на диске только шифротекстом
- Секреты в `.acfg` под маской; пароль входа сохраняется локально (chmod 600)

## Структура

```
Nyra/
  core.py        — ядро: логин, дискавери чатов, два загрузчика модулей
  ctx.py         — общий контекст (константы, edit, restart)
  modloader.py   — загрузчик модулей + шифрованная конфигурация (ScopedCfg/CfgStore)
  systemmodules/ — системные модули
    config.py    — .acfg / .fcfg
    help.py      — .elp / .help
    modcon.py    — .mods / .load / .unload / .reload / .restart
    ping.py      — .ping
    ubinfo.py    — .ubinfo
  modules/       — пользовательские модули
 ```

## Быстрый старт

```bash
git clone https://github.com/qwertyiisme/znakora-userbot.git
cd znakora-userbot
python3 -m venv .venv
.venv/bin/python -m pip install https://www.znakora.ru/userbots/python-sdk.zip
.venv/bin/python Nyra/core.py
```

При первом запуске: email, пароль и 6-значный код запуска. Далее бот запускается автоматически.

## Команды

| Команда | Описание |
|---------|----------|
| `.ping` | Пинг до сервера + время работы |
| `.elp` / `.help` | Список всех команд по категориям |
| `.ubinfo` | Информация о юзерботе |
| `.acfg` | Переменные конфигурации по модулям (секреты под маской) |
| `.fcfg <VAR> <VALUE>` | Изменить переменную (запись шифруется) |
| `.mods` | Системные модули и модули |
| `.load <имя>` | Загрузить модуль из `modules/` |
| `.unload <имя>` | Выгрузить модуль |
| `.reload` / `.reload <имя>` | Перезагрузить модули |
| `.reload sys` / `all` | Перезагрузить системные / всё |
| `.restart` | Полный перезапуск |

## Свои модули

Файл в `Nyra/modules/<имя>.py` с функцией `setup(bot, router, loader)`:

```python
def setup(bot, router, loader):
    cfg = CFG.scoped("<имя>")          # свой скоуп конфига
    cfg.default("VAR", "", desc="описание", secret=False)

    @router.command(".cmd", help="описание")
    def cmd(message):
        bot.call("edit_message", chat_id=message["chat_id"],
                 message_id=message["id"], text="готово")
```
