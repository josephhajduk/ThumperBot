from peewee import *
import datetime
from botdata.base import BaseModel
from botdata.user import User, GroupProxy


class Group(BaseModel):
    group_name = TextField(unique=True, index=True)
    legacy_name = TextField(index=True, default="")
    created_date = DateTimeField(default=datetime.datetime.now)
    description = TextField(default="")
    auto_approval = BooleanField(default=False)

GroupProxy.initialize(Group)


class GroupLink(BaseModel):
    group = ForeignKeyField(Group, related_name='group_links')
    character_field_name = TextField(default="")
    field_value = TextField(default="")


class GroupApproval(BaseModel):
    group = ForeignKeyField(Group, related_name='approvals',index=True)
    user = ForeignKeyField(User, related_name='group_approvals')
    approved = BooleanField(default=False)

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )


class GroupMembership(BaseModel):
    group = ForeignKeyField(Group, related_name='members', index=True)
    user = ForeignKeyField(User, related_name='group_memberships')
    linked = BooleanField(default=True)

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )


class GroupOperators(BaseModel):
    group = ForeignKeyField(Group, related_name='ops')
    user = ForeignKeyField(User, related_name='group_ops')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )


class GroupApplications(BaseModel):
    group = ForeignKeyField(Group, related_name='applications')
    user = ForeignKeyField(User, related_name='group_applications')
    status = TextField(default="Pending")

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('group', 'user'), True),
        )
