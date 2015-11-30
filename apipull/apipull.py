import asyncio
import apipull.eveapi
import datetime
import logging
from botdata import *
from conversationhandler.strings import strings
from apipull import eveapi

_s = strings

async def check_api_loop(bot, loop):
    while True:

        # Provide a good User-Agent header
        eveapi.set_user_agent("eveapi.py/1.3")
        api = eveapi.EVEAPIConnection()

        print(len(ApiKey.select().where(
            ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8))))

        for apikey in ApiKey.select().where(
                        ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(hours=8)):
            try:
                #todo: CHECK MASK

                auth = api.auth(keyID=apikey.key_id, vCode=apikey.verification_code)
                result2 = auth.account.Characters()

                charstring = ""

                for character in result2.characters:

                    charInfo = auth.eve.CharacterInfo(characterID=character.characterID)

                    print(character.name)

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
                            location=charInfo.lastKnownLocation)
                    else:
                        dbchar, created = Character.get_or_create(
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
                logging.error("API ERROR: maybe i should add more debug info here but i didn't")

            apikey.last_queried = datetime.datetime.now()
            apikey.save()

            if apikey.user.main_character is None:
                await bot.sendMessage(apikey.user.telegram_id, _s["msg_keysrun"])

        await asyncio.sleep(60 * 5)  # run apis every 5 minutes
