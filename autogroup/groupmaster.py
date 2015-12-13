import asyncio
import datetime
import traceback
import logging
import time
from botdata import Group, User, GroupLink, GroupMembership, GroupApproval, Character

async def group_loop(bot, loop):
    while True:
        logging.info("Starting autogroup loop")
        tasks = []
        for u in User.select():
            tasks.append(auto_group(u))
        await asyncio.gather(*tasks)
        await asyncio.sleep(60 * 5)  # run check every 5 minutes

async def auto_group_char(user, character):
    try:
        player_name = user.display_name()

        # find all group links for this character
        char_links = [
            set(link.group.group_name for link in GroupLink.select().where(
                GroupLink.character_field_name == field_name,
                GroupLink.field_value == getattr(character, field_name))
                )
            for field_name in Character._meta.fields.keys()
            ]

        flat_links = set.union(*char_links)

        for linked_group_name in flat_links:

            linked_group = Group.select().where(Group.group_name == linked_group_name).get()

            # make sure this character satisfies every link for this group
            add = True
            for link in GroupLink.select().where(GroupLink.group == linked_group):
                if getattr(character, link.character_field_name) != link.field_value:
                    add = False

            # see if this character has been approved
            approved = linked_group.auto_approval
            if len(GroupApproval.select().where(
                            GroupApproval.user == user,
                            GroupApproval.group == linked_group)) > 0:
                approved = True

            if add and approved:
                GroupMembership.create_or_get(
                    user=user,
                    group=linked_group
                )
                logging.info("Added "+player_name + " to " + linked_group.group_name)

    except:
        print("1")
        traceback.print_exc()

async def auto_group(user):
    try:
        player_name = user.display_name()
        characters = list(user.characters)

        logging.info("Autogrouping "+player_name)

        # kill all linked groups
        for group_membership in user.group_memberships.filter(GroupMembership.linked == True):
            group_membership.delete_instance()
            group_membership.save()
            logging.info("Purged "+player_name + " from " + group_membership.group.group_name)

        # add back groups
        for character in characters:
            await auto_group_char(user, character)
    except:
        logging.info("Failed to auto_group: "+player_name)
        traceback.print_exc()
