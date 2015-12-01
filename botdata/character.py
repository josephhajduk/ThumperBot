from peewee import *
from botdata.base import BaseModel
from botdata.user import User, CharacterProxy
from botdata.apikey import ApiKey


class Character(BaseModel):
    user = ForeignKeyField(User, related_name='characters', index=True)
    name = TextField(unique=True, index=True)
    eve_id = IntegerField(unique=True, index=True)
    location = TextField(index=True, default="")
    shiptype_name = TextField(index=True, default="")
    shiptype_id = TextField(index=True, default="")
    corporation_name = TextField(index=True, default="")
    corporation_id = IntegerField(index=True, default=0)
    alliance_name = TextField(index=True, default="")
    alliance_id = IntegerField(index=True, default=0)
    api_key = ForeignKeyField(ApiKey, related_name='chars')

CharacterProxy.initialize(Character)