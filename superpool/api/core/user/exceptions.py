class UserNotFound(Exception):
    """
    Exception raised when a user is not found in the database
    """


class UserAlreadyExists(Exception):
    """
    Raised when a user is already in the database
    """


class UserNotLoggedIn(Exception):
    """
    Raised when a user is not logged in
    """


class UserNotAdmin(Exception):
    """
    Raised when a user is not an admin
    """


class TokenBlacklistedError(Exception):
    """
    Raised when a blacklisted token is used
    """


class InvalidVerificationToken(Exception):
    """
    Raised when a verification token is invalid
    """
