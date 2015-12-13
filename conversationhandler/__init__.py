import telepot
import shlex
import datetime
import logging
from conversationhandler import strings
from commands import *
from botdata import User, get_config_item

_s = strings.strings


class ConversationHandler(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(ConversationHandler, self).__init__(seed_tuple, timeout)
        self._start_time = datetime.datetime.now
        self.user = None
        self.telegram_id = None
        self.commands = {c.key: c for c in [
            Help,
            RegisterApi,
            SetMain,
            ListChars,
            #Silence,
            #Unsilence,
            MuteGroup,
            UnMute,
            MyGroups,
            Ping,
            AltsOf,
            Locate,
            ListGroups,
            CreateGroup,
            LinkCorp,
            LinkAlliance,
            LinkShipType,
            Ban,
            Friend,
            Trust,
            Elevate,
            GiveAdmin,
            UnBan,
            UnFriend,
            UnTrust,
            UnElevate,
            TakeAdmin,
            ForwardMessage,
            Ops,
        ]}
        self.current_command = None

    @asyncio.coroutine
    def throttle(self, tasks):
        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i+n]

        for chunk in chunks(tasks, get_config_item("THROTTLE_CHUNK_SIZE", 20)):
            yield from asyncio.gather(*chunk)
            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def open(self, initial_msg, seed):
        if initial_msg["from"]:
            self.telegram_id = initial_msg["from"]["id"]
            self.user, created = User.create_or_get(telegram_id=self.telegram_id)

            if self.user.main_character is None:
                yield from self.sender.sendMessage(_s["msg_welcome"])
        else:
            yield from self.sender.sendMessage(_s["msg_nofrom"])

    @asyncio.coroutine
    def on_message(self, msg):
        print(msg)

        #update user every message
        if msg["from"]:
            self.telegram_id = msg["from"]["id"]
            self.user, created = User.create_or_get(telegram_id=self.telegram_id)

        content_type, chat_type, chat_id = telepot.glance2(msg)

        logging.info("received message:"+str(msg))

        if self.current_command is not None:
            if self.current_command.isFinished:
                self.current_command = None
                yield from self.on_message(msg)
            else:
                if content_type == 'text':
                    if msg["text"] == "/cancel":
                        self.current_command.cancel()
                        return (yield from self.sender.sendMessage(_s["msg_cancelled_command"],
                                                                   reply_markup={'hide_keyboard': True}))
                yield from self.current_command.msg(msg, self)
        else:
            if content_type == 'text':
                command_arguments = shlex.split(msg['text'])
                if command_arguments[0] in self.commands:
                    if self.commands[command_arguments[0]].auth_level <= self.user.auth_level:
                        self.current_command = self.commands[command_arguments[0]](self.telegram_id, self._bot)
                        yield from self.current_command.msg(msg, self)
                else:
                    yield from self.sender.sendMessage(_s["msg_notvalid"])
            else:
                yield from self.sender.sendMessage(_s["msg_expecttext"])


    @asyncio.coroutine
    def on_close(self, exception):
        if isinstance(exception, telepot.helper.WaitTooLong):
            if self.current_command is not None:
                self.current_command.cancel()
