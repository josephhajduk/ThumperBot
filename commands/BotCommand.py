import logging
import os
import asyncio
import telepot
from conversationhandler.strings import strings

LOG_FILENAME = os.path.dirname(os.path.realpath(__file__))+'/command_log.txt'

logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )

_s = strings

@asyncio.coroutine
def assert_text(msg):
    content_type, chat_type, chat_id = telepot.glance2(msg)
    if content_type != 'text':
        yield from self.sender.sendMessage(
           _s["msg_expecttext"]
        )
        return False
    return True


class BotCommand:
    def __init__(self, telegram_id, bot):
        self.telegram_id = telegram_id
        self.bot = bot
        self.current_handler = self.initial_handler
        self.isFinished = False

    key = "/command_name"
    description = "command description"
    auth_level = 0

    @asyncio.coroutine
    def msg(self, msg, chat_handler):
        yield from (self.current_handler(msg, chat_handler))

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        print("CALL TO INITIAL COMMAND HANDLER")
        print(msg)

    @asyncio.coroutine
    def finished_handler(self, msg, chat_handler):
        print("CALL TO FINISHED COMMAND HANDLER")
        print(msg)

    @asyncio.coroutine
    def cancelled_handler(self, msg, chat_handler):
        print("CALL TO CANCELLED COMMAND HANDLER")
        print(msg)

    def cancel(self):
        self.isFinished = True
        self.current_handler = self.cancelled_handler

    def finished(self):
        self.isFinished = True
        self.current_handler = self.finished_handler

BotCommand = BotCommand
