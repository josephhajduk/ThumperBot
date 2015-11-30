from peewee import *
from botdata.base import BaseModel
from botdata.user import User
import datetime

class ApiKey(BaseModel):
    user = ForeignKeyField(User)
    key_id = IntegerField(unique=True)
    verification_code = TextField()
    last_queried = DateTimeField(default=datetime.datetime.min)
    mask = TextField(default="")
