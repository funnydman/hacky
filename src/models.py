from dataclasses import dataclass
from typing import Optional

from common.models import InstructionABC
from constants import (
    C_INST_OPCODE,
    A_INST_MARK,
    A_INST_OPCODE,
    INSTRUCTION_SIZE,
    A_CONSTANT_RANGE,
    ALLOWED_SYMBOL_CHARS
)
from exceptions import HackySyntaxError, HackyInternalError
from symbols import COMP_SYMBOLS_TABLE, DEST_SYMBOLS_TABLE, JUMP_SYMBOLS_TABLE
from utils import is_absolute_address


@dataclass(frozen=True)
class CInstructionModel(InstructionABC):
    comp: str
    dest: Optional[str] = None
    jump: Optional[str] = None

    def opcode(self, *args, **kwargs) -> str:
        dest_op = self.get_dest_opcode()
        comp_op = self.get_comp_opcode()
        jump_op = self.get_jump_opcode()
        return C_INST_OPCODE + comp_op + dest_op + jump_op

    @classmethod
    def parse_instruction(cls, inst: str) -> 'CInstructionModel':
        dest, comp, jump = None, inst, None
        if ';' in inst:
            comp, jump = inst.split(';')
            if '=' in comp:
                dest, comp = comp.split('=')
        else:
            if '=' in inst:
                dest, comp = inst.split('=')
        return cls(dest=dest, comp=comp, jump=jump)

    def get_comp_opcode(self) -> str:
        try:
            return COMP_SYMBOLS_TABLE[self.comp]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{self.comp}' is not valid") from exc

    def get_dest_opcode(self) -> str:
        try:
            return DEST_SYMBOLS_TABLE[self.dest]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{self.dest}' is not valid") from exc

    def get_jump_opcode(self) -> str:
        try:
            return JUMP_SYMBOLS_TABLE[self.jump]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{self.jump}' is not valid") from exc


@dataclass(frozen=True)
class AInstructionModel(InstructionABC):
    inst: str

    def opcode(self, symbol_table: dict, *args, **kwargs) -> str:  # pylint: disable=arguments-differ
        a_const = self.parse_instruction(self.inst, symbol_table)

        start_range, end_range = A_CONSTANT_RANGE
        if not start_range <= a_const <= end_range:
            raise HackyInternalError(f'Constant must be in the range {A_CONSTANT_RANGE}')

        binary = self._get_binary(a_const)
        return A_INST_OPCODE + '0' * (INSTRUCTION_SIZE - len(A_INST_OPCODE) - len(binary)) + binary

    def parse_instruction(self, inst: str, symbol_table: dict[str, int]) -> int:
        a_const = self.get_const_value()
        self._validate(a_const)
        if is_absolute_address(a_const):
            return int(a_const)

        a_const_val = symbol_table.get(a_const)
        if a_const_val is None:
            raise HackyInternalError(f'Can not resolve "{inst}" instruction')
        return a_const_val

    def get_const_value(self) -> str:
        return self.inst.removeprefix(A_INST_MARK)

    @staticmethod
    def _get_binary(val: int) -> str:
        return bin(val)[2:]

    @staticmethod
    def _validate(a_const: str) -> None:
        if not a_const:
            raise HackySyntaxError('Empty instruction')
        if a_const[0].isdigit() and not is_absolute_address(a_const):
            raise HackySyntaxError('Invalid name')
        if any(ch not in ALLOWED_SYMBOL_CHARS for ch in a_const):
            raise HackySyntaxError('Names can contain only allowed characters')
