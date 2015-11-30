import asyncio
import datetime
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Group, Character, GroupCorpLinks
from collections import Counter


class LinkCorp(BotCommand):
    def __init__(self, telegram_id, bot):
        super(LinkCorp, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler
        self._group = None

    key = "/linkcorp"
    description = "Links an in game corp to a group."
    auth_level = 4

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Group.select()) > 0:
            groups = "Please respond with the name of the group you would like to link\n\n"
            options = []
            for group in Group.select():
                groups += "  " +group.group_name + "\n"
                options.append(group.group_name)

            self.current_handler = self.handle_group
            yield from chat_handler.sender.sendMessage(groups, reply_markup={'keyboard': [options]})
        else:
            yield from chat_handler.sender.sendMessage(_s["msg_nogroups"])

    @asyncio.coroutine
    def handle_group(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            group_name = msg["text"]

            if len(Group.select().where(Group.group_name==group_name)) > 0:
                corps = [c.corporation_name for c in Character.select()]
                corp_count = [t[0] for t in Counter(corps).most_common(10)]
                options = [corp_count[:5], corp_count[5:]]

                self._group = Group.select().where(Group.group_name==group_name).get()

                self.current_handler = self.handle_corp
                yield from chat_handler.sender.sendMessage(_s["msg_whichingamecorp"],reply_markup={'keyboard': options})
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_notagroup"])

    @asyncio.coroutine
    def handle_corp(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            corp_name = msg["text"]

            GroupCorpLinks.create_or_get(group=self._group,corp=corp_name)
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_linkadded"],reply_markup={'hide_keyboard': True})