import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Group


class CreateGroup(BotCommand):
    def __init__(self, telegram_id, bot):
        super(CreateGroup, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/creategroup"
    description = "Creates a group"
    auth_level = 4

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_group_name
        yield from chat_handler.sender.sendMessage(_s["msg_groupnameq"])

    @asyncio.coroutine
    def handle_group_name(self, msg, chat_handler):
        if (yield from assert_text(msg, chat_handler)):
            group_name = msg["text"]
            if len(Group.select().where(Group.group_name == group_name))>0:
                yield from chat_handler.sender.sendMessage(_s["msg_groupname_exists"])
            else:
                self.finished()
                Group.create(group_name=group_name)
                yield from chat_handler.sender.sendMessage(_s["msg_group_created"])

