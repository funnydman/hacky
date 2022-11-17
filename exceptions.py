class HackyBaseException(Exception):
    ...


class HackySyntaxError(HackyBaseException):
    ...


class HackyFailedToProcessFileError(HackyBaseException):
    ...


class HackyAInstructionOutOfBoundary(HackySyntaxError):
    ...
