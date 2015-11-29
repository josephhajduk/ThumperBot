import sys
import asyncio
import telepot
import shlex
import datetime
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open
from DataModel import *
from ThumperApiPull import check_api_loop
from ThumperWeb import thumper_web_init
from ThumperGroupMaster import group_loop

import time

class MemberConversation(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(MemberConversation, self).__init__(seed_tuple, timeout)
        self._start_time = datetime.datetime.now
        self._currentHandler = None
        self._query_params = {}

    @asyncio.coroutine
    def throttle(self, tasks):
        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i+n]

        for chunk in chunks(tasks,20):
            yield from asyncio.gather(*chunk)
            yield from asyncio.sleep(1)

    @asyncio.coroutine
    def assert_text(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)
        if content_type != 'text':
            yield from self.sender.sendMessage(
                'I am expecting a text message'
            )
            return False
        return True

    @asyncio.coroutine
    def open(self, initial_msg, seed):
        if initial_msg["from"]:
            telegram_id = initial_msg["from"]["id"]
            user, created = User.create_or_get(telegram_id=telegram_id)

            self._user = user

            if user.main_character == None:
                yield from self.sender.sendMessage(
                    "Hello, you  need to setup your API Keys and set your main character before you can do anything useful. If you require assistance type /help"
                )

        else:
            yield from self.sender.sendMessage(
                "Sorry I can't seem to tell who you are..."
            )

    @asyncio.coroutine
    def query_creategroup_name(self, key_msg):
        if (yield from self.assert_text(key_msg)):

            #todo enforce constraints on group names

            if len(Groups.select().where(Groups.group_name == key_msg["text"])) > 0:
                yield from self.sender.sendMessage(
                    'A group by that name already exists'
                )
            else:
                Groups.create_or_get(group_name=key_msg["text"])
                self._currentHandler = None
                yield from self.sender.sendMessage(
                    'Created a group called '+key_msg["text"]
                )

    @asyncio.coroutine
    def query_poll_message(self,msg):
        if (yield from self.assert_text(msg)):
            target_group = Groups.select().where(Groups.group_name==self._query_params["pollgroup"]).get()

            poll, created = Poll.create_or_get(message=msg["text"], target=target_group)

            self._query_params["current_poll"] = poll

            self._currentHandler = self.query_poll_options

            yield from self.sender.sendMessage(
                "Give me your poll options as separate text messages,  when you are done send me /done"
            )

    @asyncio.coroutine
    def query_poll_options(self, msg):
        if (yield from self.assert_text(msg)):
            if msg["text"] == "/done":
                self._currentHandler = self.query_poll_time

                yield from self.sender.sendMessage(
                    "Ok great, now how long do you want the poll to remain open in minutes?"
                )
            else:
                poll = self._query_params["current_poll"]
                text = msg["text"]
                PollOption.create(text=text, poll=poll)

    @asyncio.coroutine
    def query_poll_time(self,msg):
        if (yield from self.assert_text(msg)):
            try:
                poll = self._query_params["current_poll"]
                poll.ends = datetime.datetime.now() + datetime.timedelta(minutes=int(msg["text"]))
                poll.save()
                self._currentHandler = None

                options = [str(option.text) for option in poll.options]
                show_keyboard = {'keyboard': [options]}

                success = 0
                failure = 0
                sendtome = False

                options_str = ""
                for opt in poll.options:
                    options_str += "  "+str(opt.text)+"\n"

                themsg = "Poll from:"+self._user.main_character.name+" to "+poll.target.group_name+":\n\n"+poll.message+":\n"+options_str

                tasks = []

                for group_membership in GroupMembership.select().where(GroupMembership.group == poll.target):
                    try:
                        telegram_id = group_membership.user.telegram_id

                        poll_params[telegram_id] = poll
                        tasks.append(asyncio.ensure_future(bot.sendMessage(telegram_id, themsg, reply_markup=show_keyboard)))
                        success += 1
                    except:
                        failure += 1

                start_time = time.time()
                yield from self.throttle(*tasks)
                elapsed = time.time() - start_time

                yield from self.sender.sendMessage(
                    "Poll sent to "+str(success)+" users in "+str(elapsed)+" seconds, failed to send to "+str(failure)+" users\nYour poll id is: "+str(poll.id)+"\nYou can get your results with /poll"+str(poll.id)
                )
            except ValueError:
                yield from self.sender.sendMessage(
                    'I am expecting an integer'
                )



    @asyncio.coroutine
    def query_ping_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)
        ping_group = Groups.select().where(Groups.group_name == self._query_params["pinggroup"]).get()

        success = 0
        failure = 0

        tasks = []

        for group_membership in GroupMembership.select().where(GroupMembership.group == ping_group):
            try:
                telegram_id = group_membership.user.telegram_id
                if content_type == "text":
                    tasks.append(bot.sendMessage(telegram_id, "Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]+":\n\n"+msg["text"]))

                elif content_type == "photo":
                    tasks.append(bot.sendMessage(telegram_id,"Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]))
                    tasks.append(bot.sendPhoto(telegram_id, msg["photo"]["file_id"], caption=msg["caption"]))

                elif content_type == "document":
                    tasks.append(bot.sendMessage(telegram_id,"Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]))
                    tasks.append(bot.sendDocument(telegram_id, msg["document"]["file_id"]))

                elif content_type == "voice":
                    tasks.append(bot.sendMessage(telegram_id,"Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]))
                    tasks.append(bot.sendVoice(telegram_id, msg["voice"]["file_id"]))

                elif content_type == "video":
                    tasks.append(bot.sendMessage(telegram_id,"Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]))
                    tasks.append(bot.sendVideo(telegram_id, msg["video"]["file_id"]))

                elif content_type == "sticker":
                    tasks.append(bot.sendMessage(telegram_id,"Ping from:"+self._user.main_character.name+" to "+self._query_params["pinggroup"]))
                    tasks.append(bot.sendSticker(telegram_id, msg["sticker"]["file_id"]))
                success += 1
            except:
                failure += 1

        self._currentHandler = None

        start_time = time.time()

        yield from self.throttle(tasks)

        elapsed = time.time() - start_time

        yield from self.sender.sendMessage(
            "Ping sent to "+str(success)+" users,  failed to send to "+str(failure)+" users in "+str(elapsed)+" seconds"
        )

    @asyncio.coroutine
    def query_pm_message(self, key_msg):
        content_type, chat_type, chat_id = telepot.glance2(key_msg)
        try:
            pm_target = self._query_params["pm_target"]

            if content_type == "text":
                yield from bot.sendMessage(Characters.select().where(Characters.name == pm_target).get().user.telegram_id,"Message from:"+self._user.main_character.name)
                yield from bot.sendMessage(Characters.select().where(Characters.name == pm_target).get().user.telegram_id,key_msg["text"])
                yield from self.sender.sendMessage(
                    "Message sent..."
                )
            else:
            #    yield from bot.sendMessage(Characters.select().where(Characters.name == pm_target).get().user.telegram_id,"Message from:"+self._user.main_character.name)
            #    yield from bot.forwardMessage(Characters.select().where(Characters.name == pm_target).get().user.telegram_id,self._user.telegram_id,key_msg["message_id"])
                yield from self.sender.sendMessage(
                    "Non text PMs arn't supported yet..."
                )
        except:
            yield from self.sender.sendMessage(
                "Sorry I can't relay anything to that character"
            )
        self._currentHandler = None

    @asyncio.coroutine
    def query_setmain_main_character(self, key_msg):
        if (yield from self.assert_text(key_msg)):
            selection = key_msg["text"]

            if selection in [char.name for char in Characters.select().where(Characters.user == self._user)]:
                self._user.main_character = Characters.select().where(Characters.name == selection)
                self._user.save()
                self._currentHandler = None
                yield from self.sender.sendMessage(
                    selection + " is now your main"
                )
            else:
                yield from self.sender.sendMessage(
                    "I don't recognize that as one of your characters..."
                )

    @asyncio.coroutine
    def query_registerapi_keyid(self, key_msg):
        if (yield from self.assert_text(key_msg)):
            try:
                self._query_params["registerapi_keyid"] = int(key_msg["text"])
                self._currentHandler = self.query_registerapi_verification_code
                yield from self.sender.sendMessage(
                    'Please provide me the verification code'
                )
            except ValueError:
                yield from self.sender.sendMessage(
                    'Your API Key should be an integer'
                )

    @asyncio.coroutine
    def query_registerapi_verification_code(self, code_msg):
        if (yield from self.assert_text(code_msg)):

            code = code_msg["text"]

            # todo: check more stuff

            if len(code) != 64:
                return (yield from self.sender.sendMessage(
                    'Your verification code should be 64 characters'
                ))

            apikey, created = ApiKey.get_or_create(key_id=self._query_params["registerapi_keyid"], verification_code=code, user=self._user)

            self._currentHandler = None

            if not created:
                return (yield from self.sender.sendMessage(
                    'Looks like I already have that key'
                ))

            yield from self.sender.sendMessage(
                'The key has been added to your profile,  assuming it is a valid key you will hear from me shortly.'
            )


    @asyncio.coroutine
    def respond_to_poll(self, msg):
        if (yield from self.assert_text(msg)):
            poll = self._query_params["respond_to_poll"]

            msg_text = msg["text"]

            if len(PollOption.select().where(PollOption.text == msg_text and PollOption.poll == poll)) > 0:
                opt = PollOption.select().where(PollOption.text == msg_text and PollOption.poll == poll).get()
                PollResult.create(poll=poll, user=self._user, vote=opt)

                poll_params.pop(self._user.telegram_id, None)
                self._currentHandler = None

                yield from self.sender.sendMessage(
                    'Vote Recorded...', reply_markup={'hide_keyboard': True}
                )
            else:
                yield from self.sender.sendMessage(
                    'Not a valid response,  try again or /cancel'
                )


    @asyncio.coroutine
    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        print(msg)

        if content_type == "text":
            if msg["text"].lower() == "cancel":
                self._currentHandler = None
                self._query_params = {}

                poll_params.pop(self._user.telegram_id, None)

                return (yield from self.sender.sendMessage(
                    'Ok... lets start over'
                ))

        if self._user.telegram_id in poll_params:
            self._query_params["respond_to_poll"] = poll_params[self._user.telegram_id]

            if poll_params[self._user.telegram_id].ends > datetime.datetime.now():
                return (yield from self.respond_to_poll(msg))
            else:
                poll_params.pop(self._user.telegram_id, None)
                return (yield from self.sender.sendMessage(
                    "Poll has expired sorry...", reply_markup={'hide_keyboard': True}
                ))

        if self._currentHandler is not None:
            return (yield from self._currentHandler(msg))

        if (yield from self.assert_text(msg)):
            arguments = shlex.split(msg['text'])

            if self._user.auth_level < 0:
                # BANNED
                return
            if self._user.auth_level > -1:
                # NOAUTH
                if arguments[0] == "/help":
                    return (yield from self.sender.sendMessage(
                        """This will be a useful help message describing my commands,  for now it is just a list :)
  /registerapi
  /setmain
  /listchars
  /pm <character name>
You can cancel whatever you are doing by sending "cancel"

Note:  arguments with spaces must be enclosed in quotation marks.
"""))

                elif arguments[0] == "/registerapi":
                    self._currentHandler = self.query_registerapi_keyid
                    return (yield from self.sender.sendMessage('Please provide me a full access api key id'))

                elif arguments[0] == "/setmain":
                    if len(Characters.select().where(Characters.user == self._user)) == 0:
                        return (yield from self.sender.sendMessage(
                            "I don't know any of your characters,  you should setup your API keys first"
                        ))

                    self._currentHandler = self.query_setmain_main_character

                    chars = ""
                    for char in Characters.select().where(Characters.user == self._user):
                        chars += "  " + char.name + "\n"

                    return (yield from self.sender.sendMessage('Who is your main?\n' + chars))

                elif arguments[0] == "/listchars":
                    if len(Characters.select().where(Characters.user == self._user)) == 0:
                        yield from self.sender.sendMessage(
                            "I don't know any of your characters,  you should setup your API keys first")
                        return

                    chars = ""
                    for char in Characters.select().where(Characters.user == self._user):
                        chars += "  " + char.name + "\n"

                    return (yield from self.sender.sendMessage('These are your characters:\n' + chars))

            if self._user.auth_level > 0 and self._user.main_character is not None:
                #FRIENDS
                if arguments[0] == "/pm":
                    if len(Characters.select().where(Characters.name == arguments[1])) > 0:

                        self._currentHandler = self.query_pm_message
                        self._query_params["pm_target"] = arguments[1]

                        return (yield from self.sender.sendMessage(
                            "What would you like to say to "+arguments[1]+"?\nNote if you send a non text message it will be 'forwarded' which means it will expose your telegram id to the recipient"
                        ))
                    else:
                        return (yield from self.sender.sendMessage("I don't know anybody who goes by " + arguments[1]))

                elif arguments[0] == "/mygroups":

                    grouplist = ""

                    for groupmem in GroupMembership.select().where(GroupMembership.user == self._user):
                        grouplist += "  "+groupmem.group.group_name+"\n"

                    if grouplist == "":
                        yield from self.sender.sendMessage("You are not in any groups")
                    else:
                        yield from self.sender.sendMessage("These are your groups:\n"+grouplist)

                elif arguments[0] == "/joingroup":
                    if len(arguments) == 2:
                        if len(Groups.select().where(Groups.group_name == arguments[1])) > 0:
                            GroupApplications.create_or_get(group=Groups.select().where(Groups.group_name == arguments[1]).get(), user=self._user)
                            return (yield from self.sender.sendMessage(
                                "Application submitted..."
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't think that group exists"
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /joingroup <groupname>"
                        ))

            if self._user.auth_level > 1 and self._user.main_character is not None:
                #TRUSTED
                if arguments[0] == "/groupadmin":

                    #TODO  the big one

                    pass
                elif arguments[0] == "/ping":
                    if len(arguments) == 2:
                        if len(Groups.select().where(Groups.group_name == arguments[1])) > 0:

                            self._query_params["pinggroup"] = arguments[1]

                            self._currentHandler = self.query_ping_message

                            return (yield from self.sender.sendMessage(
                                "What would you like to ping?"
                            ))

                        else:
                            return (yield from self.sender.sendMessage(
                                "No such group: "+arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /ping <group>"
                        ))
                elif arguments[0] == "/poll":
                    if len(arguments) == 2:
                        if len(Groups.select().where(Groups.group_name == arguments[1])) > 0:

                            self._query_params["pollgroup"] = arguments[1]

                            self._currentHandler = self.query_poll_message

                            return (yield from self.sender.sendMessage(
                                "What is the question?"
                            ))

                        else:
                            return (yield from self.sender.sendMessage(
                                "No such group: "+arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /poll <group>"
                        ))


                elif arguments[0] == "/xupgroup":

                    #TODO  the really extra big one

                    pass

            if self._user.auth_level > 2 and self._user.main_character is not None:
                #SUPER TRUSTED
                if arguments[0] == "/locate":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:

                            location = Characters.select().where(Characters.name == arguments[1]).get().location

                            return (yield from self.sender.sendMessage(
                                arguments[1]+" is in "+location
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /locate <character>"
                        ))

                elif arguments[0] == "/listbyship":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.shiptype_name == arguments[1])) > 0:
                            chars = ""
                            for char in Characters.select().where(Characters.shiptype_name == arguments[1]):
                                chars += "  "+char.name+"\n"

                            return (yield from self.sender.sendMessage(
                                "Here are the characters in a "+arguments[1]+":\n"+chars
                            ))

                        else:
                           return (yield from self.sender.sendMessage(
                               "Nobody is sitting in a " + arguments[1]
                           ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /listbyship <shiptype>"
                        ))

                elif arguments[0] == "/altsof":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:

                            alts_target_user = Characters.select().where(Characters.name == arguments[1]).get().user

                            chars = ""

                            for char in Characters.select().where(Characters.user == alts_target_user):
                                chars += "  "+char.name+"\n"

                            return (yield from self.sender.sendMessage(
                                "Here are "+arguments[1]+"'s alts:\n"+chars
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /altsof <character>"
                        ))

                elif arguments[0] == "/listgroups":

                    grouplist = ""

                    for group in Groups.select():
                        grouplist += "  "+group.group_name+"\n"

                    if grouplist == "":
                        return (yield from self.sender.sendMessage(
                            "There are no groups"
                        ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "These are the groups:\n"+grouplist
                        ))

            if self._user.auth_level > 3 and self._user.main_character is not None:
                #ADMIN
                if arguments[0] == "/creategroup":
                        self._currentHandler = self.query_creategroup_name
                        return (yield from self.sender.sendMessage(
                            "What shall we call this group?"
                        ))

                elif arguments[0] == "/linkcorp":
                    if len(arguments) == 3:
                        if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                            group = Groups.select().where(Groups.group_name == arguments[2]).get()

                            GroupCorpLinks.create_or_get(group=group, corp=arguments[1])

                            return (yield from self.sender.sendMessage(
                                "Group " + arguments[2]+" linked to "+arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "There is no group called " + arguments[2]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /linkcorp <corporation_name> <group_name>"
                        ))

                elif arguments[0] == "/unlinkcorp":
                    if len(arguments) == 3:
                        if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                            group = Groups.select().where(Groups.group_name == arguments[2]).get()

                            query = GroupCorpLinks.select().where(GroupCorpLinks.group == group and GroupCorpLinks.corp == arguments[1])

                            if len(query) > 0:
                                query.get().delete_instance()

                                return (yield from self.sender.sendMessage(
                                    "Group " + arguments[2]+" unlinked from "+arguments[1]
                                ))
                            else:
                                return (yield from self.sender.sendMessage(
                                    "Group " + arguments[2]+" wasn't linked to "+arguments[1]
                                ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /unlinkcorp <corporation_name> <group_name>"
                        ))

                elif arguments[0] == "/linkalliance":
                    if len(arguments) == 3:
                        if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                            group = Groups.select().where(Groups.group_name == arguments[2]).get()

                            GroupAllianceLinks.create_or_get(group=group, alliance=arguments[1])

                            return (yield from self.sender.sendMessage(
                                "Group " + arguments[2]+" linked to "+arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "There is no group called " + arguments[2]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /linkalliance <alliance_name> <group_name>"
                        ))

                elif arguments[0] == "/unlinkalliance":
                    if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                        group = Groups.select().where(Groups.group_name == arguments[2]).get()

                        query = GroupAllianceLinks.select().where(GroupAllianceLinks.group == group and GroupAllianceLinks.corp == arguments[1])

                        if len(query) > 0:
                            query.get().delete_instance()

                            return (yield from self.sender.sendMessage(
                                "Group " + arguments[2]+" unlinked from "+arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "Group " + arguments[2]+" wasn't linked to "+arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /unlinkalliance <alliance_name> <group_name>"
                        ))

                elif arguments[0] == "/linkship":
                    if len(arguments) == 3:
                        if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                            group = Groups.select().where(Groups.group_name == arguments[2]).get()

                            GroupShipTypeLinks.create_or_get(group=group, shiptype=arguments[1])

                            return (yield from self.sender.sendMessage(
                                "Group " + arguments[2]+" linked to "+arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "There is no group called " + arguments[2]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /linkship <shiptype> <group_name>"
                        ))

                elif arguments[0] == "/unlinkship":
                    if len(arguments) == 3:
                        if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                            group = Groups.select().where(Groups.group_name == arguments[2]).get()

                            query = GroupShipTypeLinks.select().where(GroupShipTypeLinks.group == group and GroupShipTypeLinks.corp == arguments[1])

                            if len(query) > 0:
                                query.get().delete_instance()

                                return (yield from self.sender.sendMessage(
                                    "Group " + arguments[2]+" unlinked from "+arguments[1]
                                ))
                            else:
                                return (yield from self.sender.sendMessage(
                                    "Group " + arguments[2]+" wasn't linked to "+arguments[1]
                                ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /unlinkship <shiptype> <group_name>"
                        ))

                elif arguments[0] == "/ban":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = -1
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have banned " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /ban <character>"
                        ))

                elif arguments[0] == "/unban":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = max(player.auth_level,0)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have unbanned " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /unban <character>"
                        ))

                elif arguments[0] == "/friend":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = max(player.auth_level, 1)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have friended " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /friend <character>"
                        ))

                elif arguments[0] == "/unfriend":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = min(player.auth_level, 0)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have unfriended " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /unfriend <character>"
                        ))

                elif arguments[0] == "/trust":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = max(player.auth_level, 2)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have trusted " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /trust <character>"
                        ))

                elif arguments[0] == "/untrust":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = min(player.auth_level, 1)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have untrusted " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /untrust <character>"
                        ))

                elif arguments[0] == "/elevated":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = max(player.auth_level, 3)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have elevated " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /elevate <character>"
                        ))

                elif arguments[0] == "/unelevate":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = min(player.auth_level, 2)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have unelevated " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /unelevate <character>"
                        ))

                elif arguments[0] == "/giveadmin":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = max(player.auth_level, 4)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have given admin to " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /giveadmin <character>"
                        ))

                elif arguments[0] == "/removeadmin":
                    if len(arguments) == 2:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            player = Characters.select().where(Characters.name == arguments[1]).get().user
                            player.auth_level = min(player.auth_level, 3)
                            player.save()
                            return (yield from self.sender.sendMessage(
                                "I have taken admin from " + arguments[1]
                            ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))

                    else:
                        return (yield from self.sender.sendMessage(
                            "Usage: /removeadmin <character>"
                        ))

                elif arguments[0] == "/op":
                    if len(arguments) ==3:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                                group = Groups.select().where(Groups.group_name == arguments[2]).get()
                                user = Characters.select().where(Characters.name == arguments[1]).get().user

                                GroupOperators.create_or_get(
                                    user=user,
                                    group=group
                                )

                                yield from bot.sendMessage(user.telegram_id, "You are now an operator of the group "+arguments[2])
                                return (yield from self.sender.sendMessage(
                                    "User " + arguments[1] + " has been oped in "+arguments[2]
                                ))
                            else:
                                return (yield from self.sender.sendMessage(
                                    "There is no group called " + arguments[2]
                                ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /op <user> <group>"
                        ))

                elif arguments[0] == "/deop":
                    if len(arguments) ==3:
                        if len(Characters.select().where(Characters.name == arguments[1])) > 0:
                            if len(Groups.select().where(Groups.group_name == arguments[2])) > 0:
                                group = Groups.select().where(Groups.group_name == arguments[2]).get()
                                user = Characters.select().where(Characters.name == arguments[1]).get().user

                                GroupOperators.select().where(
                                    GroupOperators.user == user and GroupOperators.group == group
                                ).delete_instance()

                                return (yield from self.sender.sendMessage(
                                    "User " + arguments[1] + " has been deoped from "+arguments[2]
                                ))
                            else:
                                return (yield from self.sender.sendMessage(
                                    "There is no group called " + arguments[2]
                                ))
                        else:
                            return (yield from self.sender.sendMessage(
                                "I don't know anybody who goes by " + arguments[1]
                            ))
                    else:
                        return (yield from self.sender.sendMessage(
                            "usage: /deop <user> <group>"
                        ))

    @asyncio.coroutine
    def on_close(self, exception):
        print("closing")
        if isinstance(exception, telepot.helper.WaitTooLong):
            if self._currentHandler != None:
                self._currentHandler = None
                yield from self.sender.sendMessage('You took to long, start over')


TOKEN = "137055148:AAHOCCRyHsqlkcSZR1EyuSQxLVn76aYXirQ"

poll_params = {"Null":"Null"}

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(MemberConversation, timeout=60)),
])

loop = asyncio.get_event_loop()
loop.create_task(bot.messageLoop())
loop.create_task(thumper_web_init(bot, loop))
loop.create_task(check_api_loop(bot, loop))
loop.create_task(group_loop(bot, loop))
loop.run_forever()
