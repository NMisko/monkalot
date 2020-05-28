"""Module for storing custom error classes. """


class UserNotFoundError(ValueError):
    """Raised when a username is not found."""

    def __init__(self, username):
        self.username = username
