import abc


class InstructionABC(abc.ABC):
    @abc.abstractmethod
    def opcode(self, *args, **kwargs) -> str:
        ...
