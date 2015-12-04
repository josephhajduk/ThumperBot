import asyncio
import datetime
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Mute, Group


class UnMute(BotCommand):
    def __init__(self, telegram_id, bot):
        super(UnMute, self).__init__(telegram_id, bot)
        self.current_handler = self.initial_handler

    key = "/unmute"
    description = "Unmutes a specific group "
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Mute.select().where(Mute.user == chat_handler.user, Mute.until > datetime.datetime.now())) > 0:
            groups = "Please respond with the name of the group you would like to mute\n\n"
            groups += "Currently you are muting the following groups:\n"
            options = []
            for group_mem in Mute.select().where(Mute.user == chat_handler.user, Mute.until > datetime.datetime.now()):
                groups += "  " + group_mem.group.group_name + "\n"
                options.append(group_mem.group.group_name)

            self.current_handler = self.handle_group
            yield from chat_handler.sender.sendMessage(groups, reply_markup={'keyboard': [options]})
        else:
            self.finished()
            yield from chat_handler.sender.sendMessage(_s["msg_notmuting"])

    @asyncio.coroutine
    def handle_group(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            group_name = msg["text"]

            if len(Group.select().where(Group.group_name == group_name)) > 0:

                self._group = Group.select().where(Group.group_name == group_name).get()
                mute_instance = Mute.select().where(Mute.user == chat_handler.user, Mute.group ==self._group).get()
                mute_instance.delete_instance()

                self.finished()
                yield from chat_handler.sender.sendMessage(_s["msg_groupunmuted"], reply_markup={'hide_keyboard': True})
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_notagroup"])

