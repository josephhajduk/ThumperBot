import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Character


class Ban(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Ban, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/ban"
    description = "Prevents a user from accessing any commands, can still receive pings"
    auth_level = 4

    async def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_character
        await chat_handler.sender.sendMessage(_s["msg_whichcharacter"])

    async def handle_character(self, msg, chat_handler):
        if await assert_text(msg, chat_handler):
            char_name = msg["text"]
            if len(Character.select().where(Character.name == char_name)) > 0:
                user = Character.select().where(Character.name == char_name).get().user
                user.auth_level = -1
                user.save()
                self.finished()
                await chat_handler.sender.sendMessage(_s["msg_userbanned"])
            else:
                await chat_handler.sender.sendMessage(_s["msg_cantfindchar"])
