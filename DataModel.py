from peewee import *
import os
import datetime

db = SqliteDatabase(os.path.dirname(os.path.realpath(__file__))+'/Thumper.db')

class BaseModel(Model):
    class Meta:
        database = db # This model uses the "people.db" database.

CharacterProxy = Proxy()

class User(BaseModel):
    telegram_id = IntegerField(unique=True, index=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    auth_level = IntegerField(default="0")
    main_character = ForeignKeyField(CharacterProxy, index=True, null=True, default=None)


class ApiKey(BaseModel):
    user = ForeignKeyField(User)
    key_id = IntegerField(unique=True)
    verification_code = TextField()
    last_queried = DateTimeField(default=datetime.datetime.min)
    mask = TextField(default="")


class Characters(BaseModel):
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


CharacterProxy.initialize(Characters)


class Groups(BaseModel):
    group_name = TextField(unique=True, index=True)
    legacy_name = TextField(unique=True, index=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    auto_add_condition = TextField(default="")
    auto_remove_condition = TextField(default="")


class GroupMembership(BaseModel):
    group = ForeignKeyField(Groups, related_name='members')
    user = ForeignKeyField(User, related_name='groups')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )


class GroupOperators(BaseModel):
    group = ForeignKeyField(Groups, related_name='ops')
    user = ForeignKeyField(User, related_name='group_ops')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )


class GroupApplications(BaseModel):
    group = ForeignKeyField(Groups, related_name='applications')
    user = ForeignKeyField(User, related_name='group_applications')
    status = TextField()

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )

db.connect()
#db.drop_tables([User, ApiKey, Characters, Groups, GroupApplications, GroupOperators, GroupMembership])
#db.create_tables([User, ApiKey, Characters, Groups, GroupApplications, GroupOperators, GroupMembership])
