import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import User, Character


class AltsOf(BotCommand):
    def __init__(self, telegram_id, bot):
        super(AltsOf, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/altsof"
    description = "List  known characters of a certain user"
    auth_level = 3

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_character
        yield from chat_handler.sender.sendMessage(_s["msg_whichcharacter"])

    @asyncio.coroutine
    def handle_character(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            char_name = msg["text"]
            if len(Character.select().where(Character.name == char_name)) > 0:
                user = Character.select().where(Character.name == char_name).get().user

                chars = "Currently I know of the following alts:\n"
                for char in Character.select().where(Character.user == user):
                    chars += "  " + char.name + "\n"

                self.finished()
                yield from chat_handler.sender.sendMessage(chars)
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_cantfindchar"])

