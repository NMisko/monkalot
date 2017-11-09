import logging

def sanitizeUserName(username):
    if username.startswith("@"):
        username = username[1:] # remove "@"
    return username.lower()
