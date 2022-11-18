class HackyBaseException(Exception):
    """Base exception for all Hacky error"""


class HackySyntaxError(HackyBaseException):
    """Base exceptions for all Hacky syntax error"""


class HackyFailedToProcessFileError(HackyBaseException):
    ...


class HackyFailedToWriteFile(HackyBaseException):
    ...


class HackyInternalError(HackySyntaxError):
    ...
