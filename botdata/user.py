from peewee import *
import datetime
from botdata.base import BaseModel

CharacterProxy = Proxy()


class User(BaseModel):
    telegram_id = IntegerField(unique=True, index=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    auth_level = IntegerField(default="0")
    main_character = ForeignKeyField(CharacterProxy, index=True, null=True, default=None)

