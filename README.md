This is a bot that broadcasts messages to Eve online players.

you have to provide a telegram bot token (see ThumperBot.py) and manually call db.createtables the first time you run.
`db.create_tables([Group,GroupAllianceLinks,GroupApplications,GroupCorpLinks,GroupMembership,GroupOperators,GroupShipTypeLinks])`