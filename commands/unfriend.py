import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Character


class UnFriend(BotCommand):
    def __init__(self, telegram_id, bot):
        super(UnFriend, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/unfriend"
    description = "Unfriends a user"
    auth_level = 4

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
                user.auth_level = min(user.auth_level, 0)
                user.save()
                self.finished()
                yield from chat_handler.sender.sendMessage(_s["msg_usertakefriend"])
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_cantfindchar"])