# https://ops.ncdot.co.uk/currentops&pw=pvG8fOpHNQ

import asyncio
import aiohttp
import traceback
from commands.botcommand import BotCommand
from botdata import Group, GroupMembership


class Ops(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Ops, self).__init__(telegram_id, bot)

    key = "/ops"
    description = "Lists ncdot ops"
    auth_level = 0
    template = BotCommand.load_template("ops")

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Group.select().where(Group.group_name == "ncdot")) > 0:
            ncdotgroup = Group.select().where(Group.group_name == "ncdot").get()
            if len(GroupMembership.select().where(GroupMembership.group == ncdotgroup, GroupMembership.user == chat_handler.user))> 0:
                try:
                    r = yield from aiohttp.get('https://ops.ncdot.co.uk/currentops&pw=pvG8fOpHNQ')
                    self._ops = (yield from r.json())["ops"]
                    self.finished()
                    yield from self.send_template(chat_handler, "OPS")
                except:
                    traceback.print_exc()
                    self.finished()
                    yield from chat_handler.sender.sendMessage("error getting !ops")
            else:
                self.finished()
                yield from chat_handler.sender.sendMessage("you are not in ncdot group")
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage("no ncdot group")
