import asyncio
import telepot

from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

from conversationhandler import ConversationHandler
from apipull.apipull import check_api_loop
from autogroup.groupmaster import group_loop


TOKEN = "137055148:AAHOCCRyHsqlkcSZR1EyuSQxLVn76aYXirQ"
TOKEN2 = "170018274:AAHJ_J3dGa4bQVyHk5KNXtITswr-2sfk2dM"

bot = telepot.async.DelegatorBot(TOKEN2, [
    (per_chat_id(), create_open(ConversationHandler, timeout=60)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())
loop.create_task(check_api_loop(bot, loop))
loop.create_task(group_loop(bot, loop))

#loop.create_task(thumper_web_init(bot, loop))

loop.run_forever()
