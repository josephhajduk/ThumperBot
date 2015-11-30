from peewee import *
import os

db = SqliteDatabase(os.path.dirname(os.path.realpath(__file__))+'/bot_data.db')


class BaseModel(Model):
    class Meta:
        database = db # This model uses the "people.db" database.

BaseModel = BaseModel
