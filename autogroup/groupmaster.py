import asyncio
import datetime
import logging
from botdata import *

async def group_loop(bot, loop):
    while True:
        logging.info("Starting autogroup loop")
        for user in User.select():
            await auto_group(user)
        await asyncio.sleep(60 * 5)  # run check every 5 minutes

@asyncio.coroutine
def auto_group(user):
    playername = "TELID:"+str(user.telegram_id)
    if user.main_character != None:
        playername = user.main_character.name

    logging.info("Autogrouping "+playername)

    #kill all linked groups
    for group_membership in user.groups.filter(GroupMembership.linked == True):
        group_membership.delete_instance()
        group_membership.save()
        logging.info("purged "+user.main_character.name + " from " +group_membership.group.group_name)

    #get corp links
    corp_links = [list(set(
        [link.group.group_name for link in GroupCorpLinks.select().where(GroupCorpLinks.corp == mycorp)]
    )) for mycorp in [char.corporation_name for char in user.characters]]

    flat_corp_links = list(set(sum(corp_links, [])))

    #get alliance links
    alliance_links = [list(set(
        [link.group.group_name for link in GroupAllianceLinks.select().where(GroupAllianceLinks.alliance == myalliance)]
    )) for myalliance in [char.alliance_name for char in user.characters]]

    flat_alliance_links = list(set(sum(alliance_links, [])))

    #get ship links
    ship_links = [list(set(
        [link.group.group_name for link in GroupShipTypeLinks.select().where(GroupShipTypeLinks.shiptype == myshiptype)]
    )) for myshiptype in [char.shiptype_name for char in user.characters]]

    flat_ship_links = list(set(sum(ship_links, [])))

    linked_groups = flat_corp_links+flat_alliance_links+flat_ship_links

    logging.info(playername+"'s linked groups are:"+str(linked_groups))

    for group_name in linked_groups:
        group_query = Group.select().where(Group.group_name==group_name)
        if len(group_query) > 0:
            group = group_query.get()

            GroupMembership.get_or_create(
                user=user,
                group=group
            )
