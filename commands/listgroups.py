import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Group


class ListGroups(BotCommand):
    def __init__(self, telegram_id, bot):
        super(ListGroups, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/listgroups"
    description = "List all groups"
    auth_level = 4

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Group.select()) > 0:
            groups = "Here are the groups:\n"
            for group in Group.select():
                groups += "  " + group.group_name + "\n"

            self.finished()
            yield from chat_handler.sender.sendMessage(groups)
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_nogroups"])



