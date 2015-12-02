import asyncio
from commands.botcommand import BotCommand
from collections import OrderedDict


class Help(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Help, self).__init__(telegram_id, bot)

    key = "/help"
    description = "Provides a list of current commands"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):

        user_auth_level = chat_handler.user.auth_level

        hmsg = "Here are the available commands:\n\n"

        commands = (c for c in chat_handler.commands.values() if c.auth_level <= user_auth_level)

        command_key_lens = (len(c.key) for c in commands)

        maxlen = max(command_key_lens)

        ocommands = sorted((c for c in chat_handler.commands.values() if c.auth_level <= user_auth_level), key=lambda t: t.key)

        for command in ocommands:
            hmsg += command.key.rjust(maxlen, " ")+" - "+command.description+"\n"

        hmsg += "\n"
        hmsg += "\nYou can cancel whatever you are doing at any time with /cancel"
        hmsg += "\n"
        hmsg += "\nYour current authorization level is: "+str(user_auth_level)

        self.finished()

        yield from chat_handler.sender.sendMessage(hmsg)