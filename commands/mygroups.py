import asyncio
from commands.botcommand import BotCommand, assert_text, _s
from botdata import GroupMembership


class MyGroups(BotCommand):
    def __init__(self, telegram_id, bot):
        super(MyGroups, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/mygroups"
    description = "List all of your groups"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(GroupMembership.select().where(GroupMembership.user == chat_handler.user)) > 0:
            groups = "Here are your groups:\n"
            for group_mem in GroupMembership.select().where(GroupMembership.user == chat_handler.user):
                groups += "  " + group_mem.group.group_name + "\n"

            self.finished()
            yield from chat_handler.sender.sendMessage(groups)
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_nousergroups"])



