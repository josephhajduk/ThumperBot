import asyncio
import datetime
from commands.botcommand import BotCommand, assert_text, _s


class Silence(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Silence, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/silence"
    description = "Silence pings, pms, fms, xups, and polls for a specified period of time"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        show_keyboard = {'keyboard': [['60','1440'],['2160','10080']]}
        self.current_handler = self.handle_time
        yield from chat_handler.sender.sendMessage(_s["msg_silence"], reply_markup=show_keyboard)

    @asyncio.coroutine
    def handle_time(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            try:
                chat_handler.user.silence_until = datetime.datetime.now() + datetime.timedelta(minutes=int(msg["text"]))
                chat_handler.user.save()
                self.finished()
                yield from chat_handler.sender.sendMessage(_s["msg_silence_set"]+str(chat_handler.user.silence_until),
                                                           reply_markup={'hide_keyboard': True})
            except ValueError:
                yield from chat_handler.sender.sendMessage(_s["msg_expectint"])
