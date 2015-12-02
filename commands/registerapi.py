import asyncio
import re
import traceback
from commands.botcommand import BotCommand, assert_text, _s
from botdata import ApiKey
from apipull.apipull import get_key_details


class RegisterApi(BotCommand):
    def __init__(self, telegram_id, bot):
        super(RegisterApi, self).__init__(telegram_id, bot)
        self._keyid = None
        self._verification_code = None
        self.current_handler = self.initial_handler

    key = "/registerapi"
    description = "Register an EVE API Key"
    auth_level = 0
    template = BotCommand.load_template("registerapi")

    @asyncio.coroutine
    def initial_handler(self, msg, chat_handler):
        self.current_handler = self.handle_keyid
        yield from self.send_template(chat_handler, "QUERY_KEY_ID")

    @asyncio.coroutine
    def handle_keyid(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            try:
                self._keyid = msg["text"]
                self._keyid = int(msg["text"])

                if self._keyid < 100000:
                    yield from self.send_template(chat_handler, "KEYID_INVALID")
                else:
                    self.current_handler = self.handle_verification_code
                    yield from self.send_template(chat_handler, "QUERY_VERIFICATION_CODE")
            except ValueError:
                yield from self.send_template(chat_handler, "KEYID_NOT_INT")

    @asyncio.coroutine
    def handle_verification_code(self, msg, chat_handler):
        if (yield from assert_text(msg,chat_handler)):
            self._verification_code = msg["text"]

            r = re.compile("^[a-zA-Z0-9]{64}")
            if r.match(self._verification_code) is not None:

                key_details = yield from get_key_details(self._keyid,self._verification_code)

                if key_details is not None:
                    if key_details["type"] == "Account":
                        if key_details["accessMask"] & 16777216:
                            if key_details["expires"] == "":

                                api_key, created = ApiKey.create_or_get(
                                    user=chat_handler.user,
                                    key_id=self._keyid,
                                    verification_code=self._verification_code)

                                if not created:
                                    self.cancel()
                                    yield from self.send_template(chat_handler, "KEY_ALREADY_EXISTS")
                                else:
                                    self.finished()
                                    yield from self.send_template(chat_handler, "KEY_ADDED")
                            else:
                                self.finished()
                                yield from self.send_template(chat_handler, "KEY_EXPIRES")
                        else:
                            self.finished()
                            yield from self.send_template(chat_handler, "KEY_WRONG_MASK")
                    else:
                        self.finished()
                        yield from self.send_template(chat_handler, "KEY_NOT_ACCOUNT")
                else:
                    self.finished()
                    yield from self.send_template(chat_handler, "KEY_INVALID")
            else:
                yield from self.send_template(chat_handler, "VCODE_INVALID")
