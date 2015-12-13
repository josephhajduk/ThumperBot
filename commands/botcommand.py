import logging
import os
import asyncio
import telepot
import re
from jinja2 import Template
from conversationhandler.strings import strings

LOG_FILENAME = os.path.dirname(os.path.realpath(__file__))+'/../log.txt'

logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.WARNING,
                    )

_s = strings

@asyncio.coroutine
def assert_text(msg, chat_handler):
    content_type, chat_type, chat_id = telepot.glance2(msg)
    if content_type != 'text':
        yield from chat_handler.sender.sendMessage(
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
    def send_template(self,chat_handler,template_key):
        yield from chat_handler.sender.sendMessage(self.render_template(template_key, chat_handler), parse_mode="Markdown")

    @staticmethod
    def load_template(command):
        file_path = os.path.dirname(os.path.realpath(__file__))+'/templates/'+command+".jinja2"

        with open (file_path, "r") as myfile:
            raw_string =myfile.read()
            data = re.split("\(\(\(\(\(\s([\w_]*)\s\)\)\)\)\)\n", raw_string)[1:]
            temp_dict = {data[n]: Template(data[n+1]) for n in range(0, len(data), 2)}
            return temp_dict

    def render_template(self, template_id, chat_handler):
        return self.template[template_id].render(handler=chat_handler,command=self)

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
