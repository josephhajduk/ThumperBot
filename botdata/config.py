from peewee import *
import datetime
from botdata.base import BaseModel

class ConfigItem(BaseModel):
    config_id = TextField(unique=True, index=True)
    config_value = TextField(default="")


def get_config_item(item_id, default_value):
    if len(ConfigItem.select().where(ConfigItem.config_id == item_id)) > 0:
        if isinstance(default_value, int ):
            return int(ConfigItem.select().where(ConfigItem.config_id == item_id).get().config_value)
        elif isinstance(default_value, str ):
            return ConfigItem.select().where(ConfigItem.config_id == item_id).get().config_value
        else:
            raise TypeError("Only supports string and integer configuration values")
    else:
        ConfigItem.create_or_get(
            config_id=item_id,
            config_value=str(default_value),
        )
        return default_value