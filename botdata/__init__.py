
from botdata.apikey import *
from botdata.character import *
from botdata.user import *
from botdata.base import *
from botdata.group import *

#db.drop_table(GroupMembership)
#db.create_table(GroupMembership)
db.drop_tables([GroupApproval,GroupMembership,GroupLink])
db.create_tables([GroupApproval,GroupMembership,GroupLink])

#db.create_tables([Mute])
#db.create_tables([User,ApiKey,Character])
#db.create_tables([Group,GroupAllianceLinks,GroupApplications,GroupCorpLinks,GroupMembership,GroupOperators,GroupShipTypeLinks])