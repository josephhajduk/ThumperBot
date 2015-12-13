import asyncio
import telepot

from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

from conversationhandler import ConversationHandler
from apipull.apipull import check_api_loop
from autogroup.groupmaster import group_loop

from web import pingforward_web_init

from botdata import get_config_item

TOKEN2 = "170018274:AAHJ_J3dGa4bQVyHk5KNXtITswr-2sfk2dM"
TOKEN3 = "154397353:AAEChVXNz7BXxenwjNokfryfZqUgiwZLN6A"


class LoggedDelegatorBot(telepot.async.DelegatorBot):
    def __init__(self, token, delegation_patterns, loop=None):
        super(LoggedDelegatorBot, self).__init__(token, delegation_patterns, loop)

    @asyncio.coroutine
    def sendMessage(self, chat_id, text, parse_mode=None, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
        print("[REPLY TO: "+str(chat_id)+"]:\n"+str(text))
        yield from super(LoggedDelegatorBot, self).sendMessage(chat_id, text, parse_mode, disable_web_page_preview, reply_to_message_id, reply_markup)

bot = LoggedDelegatorBot(get_config_item("TELEPOT_TOKEN", TOKEN3), [
    (per_chat_id(), create_open(ConversationHandler, timeout=get_config_item("TELEPOT_CONVO_TIMEOUT", 60*10))),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())
loop.create_task(check_api_loop(bot, loop))
loop.create_task(group_loop(bot, loop))
loop.create_task(pingforward_web_init(bot,loop))
loop.run_forever()
