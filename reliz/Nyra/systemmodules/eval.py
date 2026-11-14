import io
import os
import subprocess
import sys
import traceback

from ctx import edit


def _command(router, name, help=None, hidden=False):
    """Обёртка над router.command с поддержкой hidden=True"""
    if hidden:
        return router.command(name)
    return router.command(name, help=help)


def setup(bot, router, loader):
    # ==================== .e ====================
    @_command(router, ".e", help="выполнить Python-код (только для владельца)")
    def eval_cmd(message):
        code = message["text"][3:].strip()
        if not code:
            edit(bot, message, "Использование: .e <код>")
            return

        # Специальная обработка отправки файлов
        parts = code.split(maxsplit=2)
        if parts and parts[0] in ("send", "sendphoto", "sendvideo", "sendvoice", "sendnote"):
            kind_map = {
                "send": "file",
                "sendphoto": "image",
                "sendvideo": "video",
                "sendvoice": "voice",
                "sendnote": "video_note"
            }
            kind = kind_map[parts[0]]
            path = parts[1] if len(parts) > 1 else ""
            caption = parts[2] if len(parts) > 2 else ""

            if not path or not os.path.exists(path):
                edit(bot, message, f"❌ Файл не найден: {path}")
                return

            try:
                bot.send_file(message["chat_id"], path, kind=kind, text=caption)
                edit(bot, message, f"✅ Отправлено: {os.path.basename(path)}")
            except Exception as e:
                edit(bot, message, f"❌ Ошибка: {e}")
            return

        # Обычный eval
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        sys.stderr = redirected_output

        try:
            result = eval(code, {"bot": bot, "message": message})
            output = redirected_output.getvalue()
            if result is not None:
                output += "\n" + repr(result)

            response = f"**код:**\n{code}\n\n**результат:**\n{output.strip() or '✓ (без вывода)'}"
            edit(bot, message, response[:2000])
        except Exception:
            error = traceback.format_exc()
            response = f"**код:**\n{code}\n\n**результат:**\n❌ Ошибка\n{error}"
            edit(bot, message, response[:2000])
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    # ==================== .ebash ====================
    @_command(router, ".ebash", help="выполнить shell-команду (только для владельца)")
    def ebash_cmd(message):
        cmd = message["text"][7:].strip()
        if not cmd:
            edit(bot, message, "Использование: .ebash <команда>")
            return

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = (result.stdout + result.stderr).strip()
            response = f"**код:**\n{cmd}\n\n**результат:**\n{output or '✓ (без вывода)'}"
            edit(bot, message, response[:2000])
        except subprocess.TimeoutExpired:
            response = f"**код:**\n{cmd}\n\n**результат:**\n❌ Таймаут (30 сек)"
            edit(bot, message, response)
        except Exception as e:
            response = f"**код:**\n{cmd}\n\n**результат:**\n❌ Ошибка: {e}"
            edit(bot, message, response)

    # ==================== Отправка файлов через .e ====================
    def _send_file(bot, message, path, kind="file", caption=""):
        if not os.path.exists(path):
            edit(bot, message, f"❌ Файл не найден: {path}")
            return
        try:
            bot.send_file(message["chat_id"], path, kind=kind, text=caption)
            edit(bot, message, f"✅ Отправлено: {os.path.basename(path)}")
        except Exception as e:
            edit(bot, message, f"❌ Ошибка отправки: {e}")

    # ==================== .help eval (скрытая справка) ====================
    @_command(router, ".help eval", hidden=True)
    def help_eval(message):
        text = (
            "**Eval модуль — справка**\n\n"
            "`.e <код>` — выполнить Python код\n"
            "`.ebash <команда>` — выполнить shell команду\n\n"
            "**Отправка файлов через .e:**\n"
            "`.e send <путь> [подпись]` — отправить как документ\n"
            "`.e sendphoto <путь> [подпись]` — отправить как фото\n"
            "`.e sendvideo <путь> [подпись]` — отправить как видео\n"
            "`.e sendvoice <путь>` — отправить как голосовое\n"
            "`.e sendnote <путь>` — отправить как кружок\n\n"
            "Примеры:\n"
            "`.e 2 + 2`\n"
            "`.ebash ls -la`\n"
            "`.e send /home/user/file.pdf Документ`"
        )
        edit(bot, message, text)
