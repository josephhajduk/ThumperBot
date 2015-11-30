import asyncio
import re
from commands.botcommand import BotCommand, assert_text, _s
from botdata import ApiKey


class RegisterApi(BotCommand):
    def __init__(self, telegram_id, bot):
        super(RegisterApi, self).__init__(telegram_id, bot)
        self._keyid = None
        self._verification_code = None
        self.current_handler = self.initial_handler

    key = "/registerapi"
    description = "Register an EVE API Key"
    auth_level = 0

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_keyid
        yield from chat_handler.sender.sendMessage(_s['msg_q_keyid'])

    @asyncio.coroutine
    def handle_keyid(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            try:
                self._keyid = int(msg["text"])

                if self._keyid < 1000000:
                    return (yield from chat_handler.sender.sendMessage(_s["msg_keyidinvalid"]))

                self.current_handler = self.handle_verification_code
                yield from chat_handler.sender.sendMessage(_s["msg_q_vcode"])
            except ValueError:
                yield from chat_handler.sender.sendMessage(_s["msg_expectint"])

    @asyncio.coroutine
    def handle_verification_code(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            self._verification_code = msg["text"]

            r = re.compile("^[a-zA-Z0-9]{64}")
            if r.match(self._verification_code) is not None:

                api_key, created = ApiKey.create_or_get(
                    user=chat_handler.user,
                    key_id=self._keyid,
                    verification_code=self._verification_code)

                if not created:
                    self.cancel()
                    yield from chat_handler.sender.sendMessage(_s["msg_keyexists"])
                else:
                    self.finished()
                    yield from chat_handler.sender.sendMessage(_s["msg_keyadded"])

            else:
                yield from chat_handler.sender.sendMessage(_s["msg_vcodeinvalid"])
