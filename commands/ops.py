# https://ops.ncdot.co.uk/currentops&pw=pvG8fOpHNQ

import asyncio
import aiohttp
import traceback
from commands.botcommand import BotCommand
from botdata import Group, GroupMembership, get_config_item


class Ops(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Ops, self).__init__(telegram_id, bot)

    key = "/ops"
    description = "Lists ncdot ops"
    auth_level = 0
    template = BotCommand.load_template("ops")


    async def initial_handler(self, msg, chat_handler):
        if len(Group.select().where(Group.group_name == get_config_item("OPS_GROUP", "ncdot"))) > 0:
            ncdotgroup = Group.select().where(Group.group_name == get_config_item("OPS_GROUP", "ncdot")).get()
            if len(GroupMembership.select().where(GroupMembership.group == ncdotgroup, GroupMembership.user == chat_handler.user))> 0:
                try:
                    r = await aiohttp.get(get_config_item("OPS_JSON_URL", 'ncdotopsurl'))
                    self._ops = (await r.json())["ops"]
                    self.finished()
                    if self._ops != []:
                        await self.send_template(chat_handler, "OPS")
                    else:
                        await chat_handler.sender.sendMessage("No ops planned")
                except:
                    traceback.print_exc()
                    self.finished()
                    await chat_handler.sender.sendMessage("error getting !ops")
            else:
                self.finished()
                await chat_handler.sender.sendMessage("you are not in ncdot group")
        else:
            self.finished()
            await chat_handler.sender.sendMessage("no ncdot group")
