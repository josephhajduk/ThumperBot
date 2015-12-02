import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import User, Character
import telepot


class ForwardMessage(BotCommand):
    def __init__(self, telegram_id, bot):
        super(ForwardMessage, self).__init__(telegram_id, bot)
        self.bot = bot
        self.current_handler = self.initial_handler

    key = "/fm"
    description = "Forwards a message from you to another user"
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
                self._target_user = Character.select().where(Character.name == char_name).get().user
                self.current_handler = self.handle_message
                yield from chat_handler.sender.sendMessage(_s["msg_forwardmessageq"])
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_cantfindchar"])

    @asyncio.coroutine
    def handle_message(self, msg, chat_handler):
        self.bot.sendMessage(self._target_user.telegram_id, "Message from:" + chat_handler.user.main_character.name)
        self.bot.forwardMessage(self._target_user.telegram_id, chat_handler.user.telegram_id, msg["message_id"])
        self.finished()
        yield from chat_handler.sender.sendMessage("Message forwarded...")