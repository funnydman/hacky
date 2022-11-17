#!/usr/bin/python3
"""
Symbols:
- variable symbols
- label symbols
- pre-defined symbols

TODO:
validate file extension, validate variable/label naming
validate address accessing, raise exception on out of boundary
add more tests (need 100%)
configure run-static analysis, add more typing, refactor some parts
"""
import logging
from typing import List

from constants import (
    Instruction,
    CInstruction,
    Opcode,
    C_INST_OPCODE,
    AInstruction,
    SymbolTable,
    A_INST_OPCODE,
    A_CONSTANT_RANGE,
    INSTRUCTION_SIZE,
    VAR_INST_START_ADDR
)
from exceptions import HackySyntaxError, HackyInternalError
from helper import HackyAssemblerHelper
from logger import logger


class HackyAssembler(HackyAssemblerHelper):
    def __init__(
            self,
            log_level=logging.INFO
    ) -> None:
        self.debug = log_level
        self.logger = logger
        self.logger.setLevel(log_level)

    def assemble(self, file_path: str) -> list[Instruction]:
        content = self._preprocess_file(file_path)
        symbol_table = self._build_symbol_table(content)
        content = self._resolve_labels(symbol_table, content)
        return content

    def assembly_to_file(self, file_path: str) -> None:
        content = self.assemble(file_path)
        output_file = self._get_output_file(file_path)
        self._write_to_file(output_file, content)

    def assemble_c_instruction(self, inst: CInstruction) -> Opcode:
        try:
            dest, comp, jump = self._parse_c_instruction(inst)

            self.logger.debug(
                'Assembling C instruction: %s with mnemonics dest=%s, comp=%s, jump=%s', inst, dest, comp, jump
            )

            dest_op = self._get_dest_opcode(dest)
            comp_op = self._get_comp_opcode(comp)
            jump_op = self._get_jump_opcode(jump)
        except Exception as exc:
            raise HackySyntaxError(f"Unable to assemble instruction '{inst}'. Reason: {str(exc)}") from exc

        return C_INST_OPCODE + comp_op + dest_op + jump_op

    def assemble_a_instruction(self, inst: AInstruction, symbol_table: SymbolTable) -> Opcode:
        # has the format @xxx
        self.logger.debug('Assembling A instruction: %s', inst)

        a_const = self._parse_a_instruction(inst, symbol_table)

        start_range, end_range = A_CONSTANT_RANGE
        if not start_range <= a_const <= end_range:
            raise HackyInternalError(f'Constant must be in the range {A_CONSTANT_RANGE}')

        binary = self._get_binary(a_const)
        return A_INST_OPCODE + '0' * (INSTRUCTION_SIZE - len(A_INST_OPCODE) - len(binary)) + binary

    def _resolve_labels(self, symbol_table: SymbolTable, content: List[str]) -> str:
        result = []
        curr_var_addr = VAR_INST_START_ADDR
        for line in content:
            if self._is_label(line):
                continue

            if self._is_a_instruction(line):
                a_const = self._get_constant_value(line)
                # in the form: @xxx there are options: @R0, @var, @0
                if a_const not in symbol_table and not self._is_absolute_address(a_const):
                    symbol_table[a_const] = curr_var_addr
                    curr_var_addr += 1
                assembled = self.assemble_a_instruction(line, symbol_table)
            elif self._is_c_instruction(line):
                assembled = self.assemble_c_instruction(line)
            else:
                raise HackySyntaxError(f'Unknown instruction {line}')

            result.append(assembled)

        return '\n'.join(result)


if __name__ == '__main__':
    import sys

    print(sys.argv)
    hacky = HackyAssembler()
    hacky.assembly_to_file(sys.argv[1])
