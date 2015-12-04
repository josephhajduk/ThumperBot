import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import User,Character


class SetMain(BotCommand):
    def __init__(self, telegram_id, bot):
        super(SetMain, self).__init__(telegram_id, bot)
        self._keyid = None
        self._verification_code = None
        self.current_handler = self.initial_handler

    key = "/setmain"
    description = "Set your main character"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Character.select().where(Character.user == chat_handler.user)) > 0:
            chars = "Please respond with the name of your main character\n\n"
            chars += "Currently I know of the following characters:\n"
            options = []
            for char in Character.select().where(Character.user == chat_handler.user):
                chars += "  " + char.name + "\n"
                options.append(char.name)

            show_keyboard = {'keyboard': [options]}

            self.current_handler = self.handle_character
            yield from chat_handler.sender.sendMessage(chars, reply_markup=show_keyboard)
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_nochars"])


    @asyncio.coroutine
    def handle_character(self, msg, chat_handler):
        if (yield from assert_text(msg, chat_handler)):
            character_name = msg["text"]
            if len(Character.select().where(Character.user == chat_handler.user,
                                            Character.name == character_name)) > 0:
                char = Character.select().where(Character.user == chat_handler.user,
                                                Character.name == character_name).get()
                chat_handler.user.main_character = char
                chat_handler.user.save()
                self.finished()
                yield from chat_handler.sender.sendMessage(_s["msg_maincharset"]+char.name,
                                                           reply_markup={'hide_keyboard': True})
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_notyourchar"])


