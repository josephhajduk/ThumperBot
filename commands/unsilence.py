import asyncio
import datetime
from commands.botcommand import BotCommand, assert_text, _s


class Unsilence(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Unsilence, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/unsilence"
    description = "Removes any silence status"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        chat_handler.user.silence_until = datetime.datetime.now()
        chat_handler.user.save()
        self.finished()
        yield from chat_handler.sender.sendMessage(_s["msg_unsilence"])
