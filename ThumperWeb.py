
from aiohttp import web
from DataModel import *
import telepot
import asyncio



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
    for member in GroupMembership.select().where(GroupMembership.group==Groups.select().where(Groups.legacy_name == group)):
        await bot.sendMessage(member.user.telegram_id, "legacy ping to "+group+":\n\n"+text)

    # await bot.sendMessage(userid,text)
    return web.Response(body="{}".encode('utf-8'))


async def legacy_pingplayer(request):
    player = request.match_info.get('player', "player")
    text = request.match_info.get('text', "Message")

    # look up the player in api keys,  find who registered it,  get their id,  then send the message
    await bot.sendMessage(Characters.select().where(Characters.name == player).get().user.telegram_id, text)


    # await bot.sendMessage(userid,text)
    return web.Response(body="{}".encode('utf-8'))


async def thumper_web_init(botref,loop):
    global bot

    bot = botref

    app = web.Application(loop=loop)
    app.router.add_route('GET', '/TEST/{id}/{text}', testhandle)

    app.router.add_route('GET', '/LEGACY/PINGGROUP/{group}/{text}', legacy_pinggroup)

    app.router.add_route('GET', '/LEGACY/PINGPLAYER/{player}/{text}', legacy_pingplayer)

    srv = await loop.create_server(app.make_handler(),
                                   '0.0.0.0', 8080)
    print("Server started at http://127.0.0.1:8080")
    return srv
