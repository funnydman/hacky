#!/usr/bin/python3

import logging
from typing import List

from constants import VAR_INST_START_ADDR
from custom_types import SymbolTable
from exceptions import HackySyntaxError, HackyBaseException
from helper import HackyAssemblerHelper
from logger import logger
from models import CInstructionModel, AInstructionModel
from utils import is_absolute_address


class HackyAssembler(HackyAssemblerHelper):
    def __init__(
            self,
            log_level=logging.INFO
    ) -> None:
        self.debug = log_level
        self.logger = logger
        self.logger.setLevel(log_level)

    def assemble(self, file_path: str) -> str:
        content = self._preprocess_file(file_path)
        symbol_table = self._build_symbol_table(content)
        assembled = self._resolve_labels(symbol_table, content)
        return assembled

    def assembly_to_file(self, file_path: str) -> None:
        content = self.assemble(file_path)
        output_file = self._get_output_file(file_path)
        self._write_to_file(output_file, content)

    def assemble_c_instruction(self, inst: str) -> str:
        try:
            self.logger.debug('Assembling C instruction: %s', inst)
            opcode = CInstructionModel.parse_instruction(inst).opcode()
        except HackyBaseException as exc:
            raise HackySyntaxError(f"Unable to assemble instruction '{inst}'. Reason: {str(exc)}") from exc

        return opcode

    def assemble_a_instruction(self, inst: str, symbol_table: SymbolTable) -> str:
        try:
            self.logger.debug('Assembling A instruction: %s', inst)
            opcode = AInstructionModel(inst=inst).opcode(symbol_table)
        except HackyBaseException as exc:
            raise HackySyntaxError(f"Unable to assemble instruction '{inst}'. Reason: {str(exc)}") from exc

        return opcode

    def _resolve_labels(self, symbol_table: SymbolTable, content: List[str]) -> str:
        opcodes = []
        curr_var_addr = VAR_INST_START_ADDR
        for line in content:
            if self._is_label(line):
                continue

            if self._is_a_instruction(line):
                a_const = self._get_a_const_value(line)
                # in the form: @xxx there are options: @R0, @var, @0
                if a_const not in symbol_table and not is_absolute_address(a_const):
                    symbol_table[a_const] = curr_var_addr
                    curr_var_addr += 1
                assembled_inst = self.assemble_a_instruction(line, symbol_table)
            else:
                assembled_inst = self.assemble_c_instruction(line)

            opcodes.append(assembled_inst)

        return '\n'.join(opcodes)


if __name__ == '__main__':
    import sys

    hacky = HackyAssembler()
    hacky.assembly_to_file(sys.argv[1])
