import asyncio
import apipull.eveapi
import datetime
import logging
import traceback
from botdata import *
from conversationhandler.strings import strings
from apipull import eveapi

_s = strings

@asyncio.coroutine
def get_key_details(key_id, verification_code):
    try:
        eveapi.set_user_agent("eveapi.py/1.3")
        api = eveapi.EVEAPIConnection()
        auth = api.auth(keyID=key_id, vCode=verification_code)
        api_key_info = auth.account.APIKeyInfo().key
        return {
            "accessMask": api_key_info.accessMask,
            "expires": api_key_info.expires,
            "type": api_key_info.type,
        }
    except:
        return None

@asyncio.coroutine
def run_key(bot,apikey):

    apikey_user = apikey.user
    key_id = apikey.key_id
    code = apikey.verification_code
    mainname = "NOMAIN"
    if apikey_user.main_character is not None:
        mainname= apikey_user.main_character.name
    invalid = False

    try:
        eveapi.set_user_agent("eveapi.py/1.3")
        api = eveapi.EVEAPIConnection()

        auth = api.auth(keyID=key_id, vCode=code)

        minimal_mask = 16777216
        result1 = auth.account.APIKeyInfo().key

        if not result1.accessMask & minimal_mask:
            logging.error("INVALID MASK KEY: " + str(
                key_id) + " : " + code + " for " + mainname)
            invalid = True

        apikey.mask = result1.accessMask

        if result1.expires != "":
            logging.error("EXPIRING KEY: " + str(
                key_id) + " : " + code + " for " + mainname)
            invalid = True

        if result1.type != "Account":
            logging.error("WRONG TYPE KEY: " + str(
                key_id) + " : " + code + " for " + mainname)
            invalid = True

        if not invalid:
            result2 = auth.account.Characters()

            charstring = ""

            for character in result2.characters:

                charInfo = auth.eve.CharacterInfo(characterID=character.characterID)

                print(character.name)

                #what happens when char changes corp or alliance OR LOCATION?!?!?!?!?


                dbchar, created = Character.get_or_create(
                    user=apikey_user,
                    name=character.name,
                    eve_id=character.characterID,
                    api_key=apikey)


                location = ""
                if hasattr(charInfo,"lastKnownLocation"):
                    location = charInfo.lastKnownLocation

                if hasattr(charInfo, "alliance"):
                    dbchar.corporation_name=charInfo.corporation
                    dbchar.corporation_id=charInfo.corporationID
                    dbchar.alliance_name=charInfo.alliance
                    dbchar.alliance_id=charInfo.allianceID
                    dbchar.shiptype_name=charInfo.shipTypeName
                    dbchar.shiptype_id=charInfo.shipTypeID
                    dbchar.location=location
                else:
                    if hasattr(charInfo, "alliance"):
                        dbchar.corporation_name=charInfo.corporation
                        dbchar.corporation_id=charInfo.corporationID
                        dbchar.shiptype_name=charInfo.shipTypeName
                        dbchar.shiptype_id=charInfo.shipTypeID
                        dbchar.location=location

                dbchar.save()

                charstring += "  " + character.name + "\n"
    except Exception as ex:
        if ex.code == 403:
            invalid = True

        logging.error("API ERROR: BAD KEY: " + str(
            key_id) + " : " + code + " for " + mainname)
        traceback.print_exc()


    apikey.last_queried = datetime.datetime.now()
    apikey.invalid = invalid
    apikey.save()

    try:

        if invalid:
            logging.warning("Purging characters from key: " + str(key_id))
            for delcharacter in Character.select().where(Character.api_key == apikey):
                delcharacter.delete_instance(recursive=True)

            yield from bot.sendMessage(apikey_user.telegram_id, "API KEY: " + str(
                key_id) + " has been made invalid,  your characters on this key have been purged.  Please readd a new proper key")

        if apikey_user.main_character is None:
            if not invalid:
                yield from bot.sendMessage(apikey_user.telegram_id, _s["msg_keysrun"])

    except:
        print("FAIL1")
        traceback.print_exc()
    pass


async def check_api_loop(bot, loop):
    while True:
        try:
            tasks = [run_key(bot, apikey) for apikey in ApiKey.select().where(
                ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8)
            )]

            print("Running "+str(len(tasks))+" api keys...")

            def chunks(l, n):
                for i in range(0, len(l), n):
                    yield l[i:i+n]

            #limit to 15 per second

            for chunk in chunks(tasks, 15):
                await asyncio.gather(*chunk)
                await asyncio.sleep(1)

            await asyncio.sleep(60 * 3)  # run apis every 3 minutes
        except:
            print("FAIL2")
            traceback.print_exc()
            await asyncio.sleep(60 * 3)  # run apis every 3 minutes
