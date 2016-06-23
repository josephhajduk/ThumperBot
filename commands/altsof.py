import asyncio
from commands.botcommand import BotCommand, assert_text
from botdata import Character


class AltsOf(BotCommand):
    def __init__(self, telegram_id, bot):
        super(AltsOf, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/altsof"
    description = "List  known characters of a certain user"
    auth_level = 3
    template = BotCommand.load_template("altsof")

    async def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_character
        await self.send_template(chat_handler, "WHICH_CHARACTER")

    async def handle_character(self, msg, chat_handler):
        if await assert_text(msg, chat_handler):
            self.char_name = msg["text"]
            if len(Character.select().where(Character.name == self.char_name)) > 0:
                user = Character.select().where(Character.name == self.char_name).get().user
                self.characters = [char for char in Character.select().where(Character.user == user)]
                self.finished()
                await self.send_template(chat_handler, "ALTSOF")
            else:
                await self.send_template(chat_handler, "CANT_FIND_CHARACTER")
