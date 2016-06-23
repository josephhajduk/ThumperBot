import logging
import os
import asyncio
import telepot
import re
from jinja2 import Template
from conversationhandler.strings import strings
from botdata import get_config_item

LOG_FILENAME = os.path.dirname(os.path.realpath(__file__)) + '/../log.txt'

logging.basicConfig(filename=get_config_item("LOG_FILENAME", LOG_FILENAME),
                    level=get_config_item("LOG_LEVEL", logging.WARNING))

_s = strings


async def assert_text(msg, chat_handler):
    content_type, chat_type, chat_id = telepot.glance2(msg)
    if content_type != 'text':
        await chat_handler.sender.sendMessage(
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

    async def send_template(self, chat_handler, template_key,disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
        await chat_handler.sender.sendMessage(self.render_template(template_key, chat_handler), parse_mode="Markdown",
                                              reply_to_message_id=reply_to_message_id,
                                              reply_markup=reply_markup,
                                              disable_web_page_preview=disable_web_page_preview)

    @staticmethod
    def load_template(command):
        file_path = os.path.dirname(os.path.realpath(__file__)) + '/templates/' + command + ".jinja2"

        with open(file_path, "r") as myfile:
            raw_string = myfile.read()
            data = re.split("\(\(\(\(\(\s([\w_]*)\s\)\)\)\)\)\n", raw_string)[1:]
            temp_dict = {data[n]: Template(data[n + 1]) for n in range(0, len(data), 2)}
            return temp_dict

    def render_template(self, template_id, chat_handler):
        return self.template[template_id].render(handler=chat_handler, command=self)

    async def msg(self, msg, chat_handler):
        await (self.current_handler(msg, chat_handler))

    async def initial_handler(self, msg, chat_handler):
        raise NotImplementedError("Please Implement this method")

    async def finished_handler(self, msg, chat_handler):
        raise NotImplementedError("Please Implement this method")

    async def cancelled_handler(self, msg, chat_handler):
        raise NotImplementedError("Please Implement this method")

    def cancel(self):
        self.isFinished = True
        self.current_handler = self.cancelled_handler

    def finished(self):
        self.isFinished = True
        self.current_handler = self.finished_handler


BotCommand = BotCommand
