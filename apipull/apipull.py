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

async def check_api_loop(bot, loop):
    while True:
        try:
            # Provide a good User-Agent header
            eveapi.set_user_agent("eveapi.py/1.3")
            api = eveapi.EVEAPIConnection()

            print(len(ApiKey.select().where(
                (ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8)))))

            for apikey in ApiKey.select().where(
                    (ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8))):
                mainname = "nomainset"
                if apikey.user.main_character is not None:
                    mainname= apikey.user.main_character.name
                invalid = False

                try:
                    auth = api.auth(keyID=apikey.key_id, vCode=apikey.verification_code)

                    minimal_mask = 16777216
                    result1 = auth.account.APIKeyInfo().key

                    if not result1.accessMask & minimal_mask:
                        logging.error("INVALID MASK KEY: "+str(apikey.key_id)+" : "+apikey.verification_code+" for "+mainname)
                        invalid = True

                    apikey.mask = result1.accessMask

                    if result1.expires != "":
                        logging.error("EXPIRING KEY: "+str(apikey.key_id)+" : "+apikey.verification_code+" for "+mainname)
                        invalid = True

                    if result1.type != "Account":
                        logging.error("WRONG TYPE KEY: "+str(apikey.key_id)+" : "+apikey.verification_code+" for "+mainname)
                        invalid = True

                    if not invalid:
                        result2 = auth.account.Characters()

                        charstring = ""

                        for character in result2.characters:

                            charInfo = auth.eve.CharacterInfo(characterID=character.characterID)

                            print(character.name)

                            location = ""
                            if hasattr(charInfo,"lastKnownLocation"):
                                location = charInfo.lastKnownLocation

                            if hasattr(charInfo, "alliance"):
                                dbchar, created = Character.get_or_create(
                                    user=apikey.user,
                                    name=character.name,
                                    eve_id=character.characterID,
                                    corporation_name=charInfo.corporation,
                                    corporation_id=charInfo.corporationID,
                                    alliance_name=charInfo.alliance,
                                    alliance_id=charInfo.allianceID,
                                    shiptype_name=charInfo.shipTypeName,
                                    shiptype_id=charInfo.shipTypeID,
                                    location=location,
                                    api_key=apikey)
                            else:
                                dbchar, created = Character.get_or_create(
                                    user=apikey.user,
                                    name=character.name,
                                    eve_id=character.characterID,
                                    corporation_name=charInfo.corporation,
                                    corporation_id=charInfo.corporationID,
                                    shiptype_name=charInfo.shipTypeName,
                                    shiptype_id=charInfo.shipTypeID,
                                    location=location,
                                    api_key=apikey)

                            charstring += "  " + character.name + "\n"
                except:
                    invalid = True
                    logging.error("API ERROR: BAD KEY: "+str(apikey.key_id)+" : "+apikey.verification_code+" for "+mainname)


                apikey.last_queried = datetime.datetime.now()
                apikey.invalid = invalid
                apikey.save()

                try:

                    if invalid:
                        logging.info("Purging characters from key: "+str(apikey.key_id))
                        for delcharacter in Character.select().where(Character.api_key == apikey):
                            delcharacter.delete_instance(recursive=True)

                        await bot.sendMessage(apikey.user.telegram_id, "API KEY: "+str(apikey.key_id)+" has been made invalid,  your characters on this key have been purged.  Please readd a new proper key")


                    if apikey.user.main_character is None:
                        if not invalid:
                            await bot.sendMessage(apikey.user.telegram_id, _s["msg_keysrun"])

                except:
                    print("FAIL1")
                    traceback.print_exc()

            await asyncio.sleep(60 * 3)  # run apis every 3 minutes
        except:
            print("FAIL2")
            traceback.print_exc()
            await asyncio.sleep(60 * 3)  # run apis every 3 minutes
