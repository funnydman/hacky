class HackyBaseException(Exception):
    """Base exception for all Hacky error"""


class HackySyntaxError(HackyBaseException):
    ...


class HackyFailedToProcessFileError(HackyBaseException):
    ...


class HackyFailedToWriteFile(HackyBaseException):
    ...


class HackyInternalError(HackySyntaxError):
    ...
