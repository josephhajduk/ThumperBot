import asyncio
import apipull.eveapi
import datetime
import logging
import traceback
from botdata import *
from conversationhandler.strings import strings
from apipull import eveapi
from apipull.eveapi import AuthenticationError

_s = strings

async def get_key_details(key_id, verification_code):
    try:
        eveapi.set_user_agent(get_config_item("EVEAPI_USERAGENT", "eveapi.py/1.3"))
        api = eveapi.EVEAPIConnection()
        auth = api.auth(keyID=key_id, vCode=verification_code)
        api_key_info = (await auth.account.APIKeyInfo()).key
        return {
            "accessMask": api_key_info.accessMask,
            "expires": api_key_info.expires,
            "type": api_key_info.type,
        }
    except:
        return None


async def run_key(bot, apikey):
    apikey_user = apikey.user
    key_id = apikey.key_id
    code = apikey.verification_code
    main_name = "NOMAIN"
    if apikey_user.main_character is not None:
        main_name = apikey_user.main_character.name
    invalid = False

    try:
        eveapi.set_user_agent(get_config_item("EVEAPI_USERAGENT", "eveapi.py/1.3"))
        api = eveapi.EVEAPIConnection()

        auth = api.auth(keyID=key_id, vCode=code)


        minimal_mask = get_config_item("API_MINIMUM_MASK", 16777216)
        result1 = (await auth.account.APIKeyInfo()).key

        if not result1.accessMask & minimal_mask:
            logging.error("INVALID MASK KEY: " + str(
                key_id) + " : " + code + " for " + main_name)
            invalid = True

        apikey.mask = result1.accessMask

        if result1.expires != "":
            logging.error("EXPIRING KEY: " + str(
                key_id) + " : " + code + " for " + main_name)
            invalid = True

        if result1.type != "Account":
            logging.error("WRONG TYPE KEY: " + str(
                key_id) + " : " + code + " for " + main_name)
            invalid = True

        if not invalid:
            result2 = await auth.account.Characters()

            characters_string = ""

            for api_character in result2.characters:

                character_info = await auth.eve.CharacterInfo(characterID=api_character.characterID)

                print(api_character.name)

                db_character, created = Character.get_or_create(
                    user=apikey_user,
                    name=api_character.name,
                    eve_id=api_character.characterID,
                    api_key=apikey)

                location = ""
                if hasattr(character_info, "lastKnownLocation"):
                    location = character_info.lastKnownLocation

                if hasattr(character_info, "alliance"):
                    db_character.alliance_name = character_info.alliance
                    db_character.alliance_id = character_info.allianceID
                    db_character.shiptype_name = character_info.shipTypeName
                    db_character.shiptype_id = character_info.shipTypeID
                    db_character.location = location
                else:
                    db_character.corporation_name = character_info.corporation
                    db_character.corporation_id = character_info.corporationID
                    db_character.shiptype_name = character_info.shipTypeName
                    db_character.shiptype_id = character_info.shipTypeID
                    db_character.location = location

                db_character.save()

                characters_string += "  " + api_character.name + "\n"
    except IntegrityError:
        invalid = True

        logging.error("API DBERROR: BAD KEY: " + str(
            key_id) + " : " + code + " for " + main_name)
        traceback.print_exc()
    except AuthenticationError as ex:
        if ex.code == 403:
            invalid = True

        logging.error("API DELETED: BAD KEY: " + str(
            key_id) + " : " + code + " for " + main_name)
        traceback.print_exc()
    except:
        logging.error("API ERROR: BAD KEY: " + str(
            key_id) + " : " + code + " for " + main_name)
        traceback.print_exc()

    apikey.last_queried = datetime.datetime.now()
    apikey.invalid = invalid
    apikey.save()

    try:
        if invalid:
            logging.warning("Purging characters from key: " + str(key_id))
            for del_character in Character.select().where(Character.api_key == apikey):
                del_character.delete_instance(recursive=True)

            await bot.sendMessage(apikey_user.telegram_id, "API KEY: " + str(key_id) +
                                  " has been made invalid,  your characters on this key have been purged.  "
                                  "Please readd a new proper key")

        if apikey_user.main_character is None:
            if not invalid:
                await bot.sendMessage(apikey_user.telegram_id, _s["msg_keysrun"])

    except:
        traceback.print_exc()


async def check_api_loop(bot, loop):
    while True:
        try:
            tasks = [run_key(bot, apikey) for apikey in ApiKey.select().where(
                ApiKey.last_queried < datetime.datetime.now() - datetime.timedelta(
                    hours=get_config_item("API_REFRESH_HOURS", 8)),
                ApiKey.invalid == False
            )]

            def chunks(l, n):
                for i in range(0, len(l), n):
                    yield l[i:i + n]

            # limit to 10 per second
            for chunk in chunks(tasks, get_config_item("EVEAPI_TROTTLE_RATE", 10)):
                await asyncio.gather(*chunk)
                await asyncio.sleep(1)

        except:
            traceback.print_exc()

        await asyncio.sleep(get_config_item("API_LOOP", 60 * 3))  # run every 3 minutes
