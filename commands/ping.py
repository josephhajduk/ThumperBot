import asyncio
import telepot
import math
import time
from commands.botcommand import BotCommand, assert_text, _s
from botdata import Group, GroupMembership


class Ping(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Ping, self).__init__(telegram_id, bot)
        self.bot = bot
        self.current_handler = self.initial_handler
        self._group = None

    key = "/ping"
    description = "Sends a broadcast out to every member of the specified group."
    auth_level = 2

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        if len(Group.select()) > 0:
            groups = "Please respond with the name of the group you would like to ping\n\n"
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
                self._group = Group.select().where(Group.group_name == group_name).get()
                self.current_handler = self.handle_message
                yield from chat_handler.sender.sendMessage(_s["msg_pingmessageq"],reply_markup={'hide_keyboard': True})
            else:
                yield from chat_handler.sender.sendMessage(_s["msg_notagroup"])

    @asyncio.coroutine
    def handle_message(self, msg, chat_handler):
        content_type, chat_type, chat_id = telepot.glance2(msg)
        tasks = []
        success = 0
        failure = 0

        for group_membership in GroupMembership.select().where(GroupMembership.group == self._group):
            try:
                telegram_id = group_membership.user.telegram_id
                main_character_name = chat_handler.user.main_character.name
                group_name = self._group.group_name

                if content_type == "text":
                    tasks.append(self.bot.sendMessage(telegram_id, "Ping from:" + main_character_name + " to " + group_name + ":\n\n" + msg["text"]))

                elif content_type == "photo":
                    tasks.append(self.bot.sendMessage(telegram_id,"Ping from:" + main_character_name + " to " + group_name))
                    tasks.append(self.bot.sendPhoto(telegram_id, msg["photo"]["file_id"], caption=msg["caption"]))

                elif content_type == "document":
                    tasks.append(self.bot.sendMessage(telegram_id,"Ping from:" + main_character_name + " to " + group_name))
                    tasks.append(self.bot.sendDocument(telegram_id, msg["document"]["file_id"]))

                elif content_type == "voice":
                    tasks.append(self.bot.sendMessage(telegram_id,"Ping from:" + main_character_name + " to " + group_name))
                    tasks.append(self.bot.sendVoice(telegram_id, msg["voice"]["file_id"]))

                elif content_type == "video":
                    tasks.append(self.bot.sendMessage(telegram_id,"Ping from:" + main_character_name + " to " + group_name))
                    tasks.append(self.bot.sendVideo(telegram_id, msg["video"]["file_id"]))

                elif content_type == "sticker":
                    tasks.append(self.bot.sendMessage(telegram_id,"Ping from:" + main_character_name + " to " + group_name))
                    tasks.append(self.bot.sendSticker(telegram_id, msg["sticker"]["file_id"]))
                success += 1
            except:
                failure += 1

        self.finished()

        start_time = time.time()
        yield from chat_handler.throttle(tasks)
        elapsed = time.time() - start_time

        rounded = math.floor(elapsed*100)/100

        yield from chat_handler.sender.sendMessage(
            "Ping sent to "+str(success)+" users in "+str(rounded)+" seconds"
        )