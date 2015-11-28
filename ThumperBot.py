import sys
import asyncio
import telepot
import shlex
import datetime
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open
from aiohttp import web
from DataModel import *
import eveapi


## we will pipe in pings from here
async def testhandle(request):
    userid = request.match_info.get('id', "151887803")
    text = request.match_info.get('text', "Message")
    await bot.sendMessage(userid, text)
    return web.Response(body="{}".encode('utf-8'))


async def legacy_pinggroup(request):
    group = request.match_info.get('group', "group")
    text = request.match_info.get('text', "Message")

    # look up the group,  for each user id send the message

    # await bot.sendMessage(userid,text)
    return web.Response(body="{}".encode('utf-8'))


async def legacy_pingplayer(request):
    player = request.match_info.get('player', "player")
    text = request.match_info.get('text', "Message")

    # look up the player in api keys,  find who registered it,  get their id,  then send the message
    await bot.sendMessage(Characters.select().where(Characters.name == player).get().user.telegram_id, text)


    # await bot.sendMessage(userid,text)
    return web.Response(body="{}".encode('utf-8'))


async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/TEST/{id}/{text}', testhandle)

    app.router.add_route('GET', '/LEGACY/PINGGROUP/{group}/{text}', legacy_pinggroup)

    app.router.add_route('GET', '/LEGACY/PINGPLAYER/{player}/{text}', legacy_pingplayer)

    srv = await loop.create_server(app.make_handler(),
                                   '127.0.0.1', 8080)
    print("Server started at http://127.0.0.1:8080")
    return srv


async def checkAPIs(loop):
    while True:
        # await asyncio.sleep(60*5) #run apis every 5 minutes

        # Provide a good User-Agent header
        eveapi.set_user_agent("eveapi.py/1.3")
        api = eveapi.EVEAPIConnection()

        print(len(ApiKey.select().where(
            ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8))))

        for apikey in ApiKey.select().where(
                        ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8)):
            try:
                # TODO CHECK MASK

                auth = api.auth(keyID=apikey.key_id, vCode=apikey.verification_code)
                result2 = auth.account.Characters()

                charstring = ""

                for character in result2.characters:

                    charInfo = auth.eve.CharacterInfo(characterID=character.characterID)

                    print(character.name)

                    if hasattr(charInfo, "alliance"):
                        dbchar, created = Characters.get_or_create(
                            user=apikey.user,
                            name=character.name,
                            eve_id=character.characterID,
                            corporation_name=charInfo.corporation,
                            corporation_id=charInfo.corporationID,
                            alliance_name=charInfo.alliance,
                            alliance_id=charInfo.allianceID,
                            shiptype_name=charInfo.shipTypeName,
                            shiptype_id=charInfo.shipTypeID,
                            location=charInfo.lastKnownLocation)
                    else:
                        dbchar, created = Characters.get_or_create(
                            user=apikey.user,
                            name=character.name,
                            eve_id=character.characterID,
                            corporation_name=charInfo.corporation,
                            corporation_id=charInfo.corporationID,
                            shiptype_name=charInfo.shipTypeName,
                            shiptype_id=charInfo.shipTypeID,
                            location=charInfo.lastKnownLocation)

                    charstring += "  " + character.name + "\n"
            except:
                print("API FAILURE")

            apikey.last_queried = datetime.datetime.now()
            apikey.save()

            if apikey.user.main_character is None:
                await bot.sendMessage(apikey.user.telegram_id,
                                      "One of your api keys ran successfully.  These are the characters we just pulled.\n" + charstring + "\nPlease set your main character with /setmain.")

        await asyncio.sleep(60 * 5)  # run apis every 5 minutes


### DATA STRUCTURE ####

class MemberConversation(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(MemberConversation, self).__init__(seed_tuple, timeout)
        # store our start "datetime" so we can ignore messages prior.
        self._currentHandler = None

    @asyncio.coroutine
    def open(self, initial_msg, seed):
        content_type, chat_type, chat_id = telepot.glance2(initial_msg)

        if initial_msg["from"]:
            telegram_id = initial_msg["from"]["id"]
            user, created = User.create_or_get(telegram_id=telegram_id)
            user.save()
            db.commit()
            self._user = user

            if user.main_character == None:
                yield from self.sender.sendMessage(
                    "Hello, you  need to setup your API Keys and set your main character before you can do anything useful. If you require assistance type /help")
            else:
                yield from self.sender.sendMessage(
                    "Welcome back " + user.main_character.name + ", If you require assistance type /help ")

        else:
            yield from self.sender.sendMessage("Sorry I can't seem to tell who you are...")


    @asyncio.coroutine
    def pmPlayer(self, key_msg):
        content_type, chat_type, chat_id = telepot.glance2(key_msg)

        try:
            if content_type == "text":
                yield from bot.sendMessage(Characters.select().where(Characters.name == self._pmTarget).get().user.telegram_id,"Message from:"+self._user.main_character.name)
                yield from bot.sendMessage(Characters.select().where(Characters.name == self._pmTarget).get().user.telegram_id,key_msg["text"])
                yield from self.sender.sendMessage("Message sent...")
            else:
                yield from bot.sendMessage(Characters.select().where(Characters.name == self._pmTarget).get().user.telegram_id,"Message from:"+self._user.main_character.name)
                yield from bot.forwardMessage(Characters.select().where(Characters.name == self._pmTarget).get().user.telegram_id,self._user.telegram_id,key_msg["message_id"])
                yield from self.sender.sendMessage("Message sent...")
        except:
            yield from self.sender.sendMessage("Sorry I can't relay anything to that character")

        self._currentHandler = None

    @asyncio.coroutine
    def setMain(self, key_msg):
        content_type, chat_type, chat_id = telepot.glance2(key_msg)

        if content_type != 'text':
            yield from self.sender.sendMessage('Your character name should be text')
            return

        selection = key_msg["text"]

        if selection in [char.name for char in Characters.select().where(Characters.user == self._user)]:

            self._user.main_character = Characters.select().where(Characters.name == selection)
            self._user.save()

            self._currentHandler = None

            yield from self.sender.sendMessage(selection + " is now your main")
        else:
            yield from self.sender.sendMessage("I don't recognize that as one of your characters...")

    @asyncio.coroutine
    def register_apiKey(self, key_msg):
        content_type, chat_type, chat_id = telepot.glance2(key_msg)

        if content_type != 'text':
            yield from self.sender.sendMessage('Your API Key should be text')
            return

        try:
            self._key_int = int(key_msg["text"])
            self._currentHandler = self.register_VerificationCode
            yield from self.sender.sendMessage('Please provide me the verification code')
        except ValueError:
            yield from self.sender.sendMessage('Your API Key should be an integer')

    @asyncio.coroutine
    def register_VerificationCode(self, code_msg):
        content_type, chat_type, chat_id = telepot.glance2(code_msg)

        if content_type != 'text':
            yield from self.sender.sendMessage('Your verification code should be text')
            return

        code = code_msg["text"]

        # todo: check more stuff
        if len(code) != 64:
            yield from self.sender.sendMessage('Your verification code should be 64 characters')
            return

        try:
            apikey, created = ApiKey.get_or_create(key_id=self._key_int, verification_code=code, user=self._user)
        except:
            ex = sys.exc_info()
            print("Unexpected error:", ex)

        self._currentHandler = None

        if not created:
            yield from self.sender.sendMessage('Looks like I already have that key')
            return

        yield from self.sender.sendMessage(
            'The key has been added to your profile,  assuming it is a valid key you will hear from me shortly.')

    @asyncio.coroutine
    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        # debug
        print(msg)

        if content_type == "text":
            if msg["text"] == "cancel":
                self._currentHandler = None
                yield from self.sender.sendMessage('Ok...')

        if self._currentHandler != None:
            return (yield from self._currentHandler(msg))


        if content_type != 'text':
            yield from self.sender.sendMessage('I can only handle text at this time.')
            return True

        command = shlex.split(msg['text'])

        if self._user.auth_level < 0:
            # BANNED
            return
        if self._user.auth_level > -1:
            # NOAUTH
            if command[0] == "/help":
                yield from self.sender.sendMessage('This will be a useful help message describing my commands,  for now it is just a list :)\n  /registerapi\n  /setmain\n  /listchars\n  /pm <character name>\n  You can cancel whatever you are doing by sending "cancel"')
                return
            elif command[0] == "/registerapi":
                self._currentHandler = self.register_apiKey
                yield from self.sender.sendMessage('Please provide me a full access api key id')
                return
            elif command[0] == "/setmain":
                if len(Characters.select().where(Characters.user == self._user)) == 0:
                    yield from self.sender.sendMessage(
                        "I don't know any of your characters,  you should setup your API keys first")
                    return

                self._currentHandler = self.setMain

                chars = ""
                for char in Characters.select().where(Characters.user == self._user):
                    chars += "  " + char.name + "\n"

                yield from self.sender.sendMessage('Who is your main?\n' + chars)
                return
            elif command[0] == "/listchars":
                if len(Characters.select().where(Characters.user == self._user)) == 0:
                    yield from self.sender.sendMessage(
                        "I don't know any of your characters,  you should setup your API keys first")
                    return

                chars = ""
                for char in Characters.select().where(Characters.user == self._user):
                    chars += "  " + char.name + "\n"

                yield from self.sender.sendMessage('These are your characters:\n' + chars)
                return
        if self._user.auth_level > 0 and self._user.main_character is not None:
            #FRIENDS
            if command[0] == "/pm":
                #make sure target exists
                if len(Characters.select().where(Characters.name == command[1])) > 0:

                    self._currentHandler = self.pmPlayer
                    self._pmTarget = command[1]

                    yield from self.sender.sendMessage("What would you like to say to "+command[1]+"?\nNote if you send a non text message it will be 'forwarded' which means it will expose your telegram id to the recipient")
                    return
                else:
                    yield from self.sender.sendMessage("I don't know anybody who goes by " + command[1])
                    return
            elif command[0] == "/mygroups":
                pass
            elif command[0] == "/listgroups":
                pass
            elif command[0] == "/joingroups":
                pass
        if self._user.auth_level > 1 and self._user.main_character is not None:
            #TRUSTED
            if command[0] == "/groupadmin":
                pass
            elif command[0] == "/pinggroup":
                pass
            elif command[0] == "/xupgroup":
                pass
        if self._user.auth_level > 2 and self._user.main_character is not None:
            #SUPER TRUSTED
            if command[0] == "/locate":
                pass
            elif command[0] == "/listbyship":
                pass
            elif command[0] == "/altsof":
                pass
        if self._user.auth_level > 3 and self._user.main_character is not None:
            #ADMIN
            if command[0] == "/ban":
                pass
            elif command[0] == "/unban":
                pass
            elif command[0] == "/friend":
                pass
            elif command[0] == "/unfriend":
                pass
            elif command[0] == "/trust":
                pass
            elif command[0] == "/untrust":
                pass
            elif command[0] == "/elevated":
                pass
            elif command[0] == "/unelevated":
                pass
            elif command[0] == "/giveadmin":
                pass
            elif command[0] == "/takeadmin":
                pass
            elif command[0] == "/op":
                pass
            elif command[0] == "/deop":
                pass

        return

    @asyncio.coroutine
    def on_close(self, exception):
        print("closing")
        if isinstance(exception, telepot.helper.WaitTooLong):
            if self._currentHandler != None:
                self._currentHandler = None
                yield from self.sender.sendMessage('You took to long, start over')


TOKEN = "137055148:AAHOCCRyHsqlkcSZR1EyuSQxLVn76aYXirQ"

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(MemberConversation, timeout=60)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())
loop.create_task(init(loop))
loop.create_task(checkAPIs(loop))
loop.run_forever()
