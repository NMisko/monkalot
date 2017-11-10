"""Utility functions for user data."""


def sanitizeUserName(username):
    """Remove the @ if a string starts with it."""
    if username.startswith("@"):
        username = username[1:]  # remove "@"
    return username.lower()
