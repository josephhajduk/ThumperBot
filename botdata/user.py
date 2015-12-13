from peewee import *
import datetime
from botdata.base import BaseModel

CharacterProxy = Proxy()
GroupProxy = Proxy()

class User(BaseModel):
    telegram_id = IntegerField(unique=True, index=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    auth_level = IntegerField(default="0")
    main_character = ForeignKeyField(CharacterProxy, index=True, null=True, default=None)

    def display_name(self):
        if self.main_character is not None:
            return self.main_character.name
        else:
            return "TELEGRAM_ID:"+str(self.telegram_id)

class Mute(BaseModel):
    group = ForeignKeyField(GroupProxy, related_name='user_mutes', index=True)
    user = ForeignKeyField(User, related_name='group_mutes')
    until = DateTimeField(default=datetime.datetime.min)