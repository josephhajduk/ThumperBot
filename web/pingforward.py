
from aiohttp import web
from botdata import GroupMembership, Character, Group
import telepot
import asyncio
import time
import math
import json
import re


async def legacy_parse(request):
    data = await request.post()

    print("HELLO")

    raw = data["messages"]

    print("ITSME")

    if raw[-2:] == ",]":
        raw = raw[:-2]+"]"

    parsed = []

    try:
        parsed = json.loads(raw)
    except Exception:
        print(raw)

    r = re.compile("\[04BROADCAST04/([\w\s;]*)]\s(\w*)\:\s(.*)", re.IGNORECASE)

    msg = ""

    for pingrow in parsed:
        ping_time = pingrow["time"]
        sender = pingrow["sender"]
        message = pingrow["message"]

        m = r.search(message)

        legacy_groups = m.groups()[0].split(";")
        legacy_sender = m.groups()[1]
        message = m.groups()[2]

        for group in legacy_groups:
            group_name = group[2:].lower()
            tasks = []
            success = 0
            # look up the group,  for each user id send the 'message'
            for member in GroupMembership.select().where(GroupMembership.group==Group.select().where(Group.legacy_name == group_name)):
                tasks.append(bot.sendMessage(member.user.telegram_id, "Ping from "+legacy_sender+" to "+group_name+":\n\n"+message))
                success += 1

            def chunks(l, n):
                for i in range(0, len(l), n):
                    yield l[i:i+n]

            start_time = time.time()

            for chunk in chunks(tasks, 20):
                await asyncio.gather(*chunk)
                await asyncio.sleep(1)

            elapsed = time.time() - start_time

            rounded = math.floor(elapsed*100)/100

            msg += "Ping sent to  "+str(success)+" users for "+group_name+" in "+str(rounded)+" seconds\n"


    return web.Response(body=msg.encode('utf-8'))


async def legacy_pinggroup(request):
    group = request.match_info.get('group', "group")
    text = request.match_info.get('text', "'message'")
    fromp = request.match_info.get('from', "'message'")

    tasks = []
    success = 0
    # look up the group,  for each user id send the 'message'
    for member in GroupMembership.select().where(GroupMembership.group==Group.select().where(Group.legacy_name == group)):
        tasks.append(bot.sendMessage(member.user.telegram_id, "Ping from "+fromp+" to "+group+":\n\n"+text))
        success += 1

    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    start_time = time.time()

    for chunk in chunks(tasks, 20):
        await asyncio.gather(*chunk)
        await asyncio.sleep(1)

    elapsed = time.time() - start_time

    rounded = math.floor(elapsed*100)/100

    msg = "Ping sent to "+str(success)+" users in "+str(rounded)+" seconds"

    return web.Response(body=msg.encode('utf-8'))


async def legacy_pingplayer(request):
    player = request.match_info.get('player', "player")
    text = request.match_info.get('text', "'message'")

    # look up the player in api keys,  find who registered it,  get their id,  then send the 'message'
    await bot.sendMessage(Character.select().where(Character.name == player).get().user.telegram_id, text)

    return web.Response(body="{}".encode('utf-8'))


async def pingforward_web_init(botref, loop):
    global bot

    bot = botref

    app = web.Application(loop=loop)

    app.router.add_route('GET', '/pf/g/{group}/{from}/{text}', legacy_pinggroup)

    app.router.add_route('POST', '/pf/parse', legacy_parse)

    app.router.add_route('GET', '/pf/p/{player}/{from}/{text}', legacy_pingplayer)

    srv = await loop.create_server(app.make_handler(),
                                   '0.0.0.0', 8080)
    print("Server started at http://0.0.0.0:8080")
    return srv