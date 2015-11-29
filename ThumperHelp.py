def help_message(authlevel):
    if authlevel < 0:
        return "You are banned."
    else:
        result = "Here are the currently availible commands:"
