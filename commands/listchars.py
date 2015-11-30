import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import User, Character


class ListChars(BotCommand):
    def __init__(self, telegram_id, bot):
        super(ListChars, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/listchars"
    description = "List all your known characters"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Character.select().where(Character.user == chat_handler.user)) > 0:
            chars = "Currently I know of the following characters:\n"
            options = []
            for char in Character.select().where(Character.user == chat_handler.user):
                chars += "  " + char.name + "\n"
                options.append(char.name)

            self.finished()
            yield from chat_handler.sender.sendMessage(chars)
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_nochars"])



