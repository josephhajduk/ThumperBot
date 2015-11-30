import asyncio
from commands.botcommand import BotCommand


class Help(BotCommand):
    def __init__(self, telegram_id, bot):
        super(Help, self).__init__(telegram_id, bot)

    key = "/help"
    description = "Provides a list of current commands"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):

        user_auth_level = chat_handler.user.auth_level

        hmsg = "Here are the available commands:\n"

        for command in (c for c in chat_handler.commands.values() if c.auth_level <= user_auth_level):
            hmsg += "  "+command.key+" - "+command.description+"\n"

        hmsg += "\nMost commands are usually invoked without any parameters, however when passing parameters directly" \
                " to a command they should be passed like console commands"
        hmsg += '\n\ni.e.: /pm "Christopher Berger"'
        hmsg += '\nnot: /pm Christopher Berger'
        hmsg += "\n"
        hmsg += "\nYou can cancel whatever you are doing at any time with /cancel"
        hmsg += "\n"
        hmsg += "\nYour current authorization level is: "+str(user_auth_level)

        self.finished()

        yield from chat_handler.sender.sendMessage(hmsg)