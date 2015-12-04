import asyncio
import datetime
from commands.botcommand import BotCommand, assert_text, _s
from botdata import GroupMembership, Mute, Group


class MuteGroup(BotCommand):
    def __init__(self, telegram_id, bot):
        super(MuteGroup, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/mutegroup"
    description = "Mutes a specific group for a certain amount of time"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(GroupMembership.select().where(GroupMembership.user == chat_handler.user)) > 0:
            groups = "Please respond with the name of the group you would like to mute\n\n"
            groups += "Currently you are in the following groups:\n"
            options = []
            for group_mem in GroupMembership.select().where(GroupMembership.user == chat_handler.user):
                groups += "  " + group_mem.group.group_name + "\n"
                options.append(group_mem.group.group_name)

            self.current_handler = self.handle_group
            yield from chat_handler.sender.sendMessage(groups, reply_markup={'keyboard': [options]})
        else:
            yield from chat_handler.sender.sendMessage(_s["msg_usernogroups"])

    @asyncio.coroutine
    def handle_group(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            group_name = msg["text"]

            if len(Group.select().where(Group.group_name == group_name)) > 0:
                self._group = Group.select().where(Group.group_name == group_name).get()
                if len(Mute.select().where(Mute.group == self._group, Mute.user == chat_handler.user)) == 0:

                    show_keyboard = {'keyboard': [['60','1440'],['2160','10080']]}
                    self.current_handler = self.handle_time
                    yield from chat_handler.sender.sendMessage(_s["msg_howlongmute"], reply_markup=show_keyboard)
                else:
                    self.cancel()
                    yield from chat_handler.sender.sendMessage("You are already muting this group",reply_markup={'hide_keyboard': True})
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_notagroup"])

    @asyncio.coroutine
    def handle_time(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            try:
                mute_until = datetime.datetime.now() + datetime.timedelta(minutes=int(msg["text"]))

                Mute.create(
                    user=chat_handler.user,
                    group=self._group,
                    until=mute_until)

                self.finished()
                yield from chat_handler.sender.sendMessage(_s["msg_mutegroupuntil"]+str(mute_until),
                                                           reply_markup={'hide_keyboard': True})
            except ValueError:
                yield from chat_handler.sender.sendMessage(_s["msg_expectint"])
