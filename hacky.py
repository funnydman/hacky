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
import os
import string
from typing import List, Optional, TypeVar

from exceptions import HackySyntaxError, HackyFailedToProcessFileError, HackyAInstructionOutOfBoundary
from logger import logger
from symbols import PRE_DEFINED_SYMBOLS, DEST_SYMBOLS_TABLE, JUMP_SYMBOLS_TABLE, COMP_SYMBOLS_TABLE

A_INST_MARK = '@'
C_INST_OPCODE = '111'
A_INST_OPCODE = '0'
VAR_INST_START_ADDR = 16
INSTRUCTION_SIZE = 16
LABEL_INST_STARTS_WITH = '('
LABEL_INST_ENDS_WITH = ')'
COMMENT_MARK = '//'
INPUT_FILE_EXTENSION = '.asm'
OUTPUT_FILE_EXTENSION = '.hack'

ALLOWED_SYMBOL_CHARS = string.ascii_letters + string.digits + '_.$:'
A_CONSTANT_RANGE = (0, 32767)

Instruction = TypeVar('Instruction', bound=str)
Mnemonic = TypeVar('Mnemonic', bound=str)
Opcode = TypeVar('Opcode', bound=str)
SymbolTable = TypeVar('SymbolTable', bound=dict)


class HackyAssembler:
    def __init__(
            self,
            log_level=logging.INFO
    ) -> None:
        self.debug = log_level
        self.logger = logger
        self.logger.setLevel(log_level)

    @staticmethod
    def _read_file(file_path: str) -> list[str]:
        try:
            with open(file_path, 'r') as file:
                lines = file.read().splitlines()
            return lines
        except (OSError, FileNotFoundError) as exc:
            raise HackyFailedToProcessFileError(f'Unable to process the file. Reason: {str(exc)}') from exc

    @staticmethod
    def _validate_file_extension(file_path: str) -> None:
        _, file_extension = os.path.splitext(file_path)
        if file_extension != INPUT_FILE_EXTENSION:
            raise HackyFailedToProcessFileError(
                f"Invalid file extension, expected: '{INPUT_FILE_EXTENSION}', got: '{file_extension}'"
            )

    def _preprocess_file(self, file_path: str) -> List[Mnemonic]:
        """
        Remove empty lines, comments and strip
        """
        self._validate_file_extension(file_path)

        mnemonics: list[Mnemonic] = []
        content = self._read_file(file_path)
        for line in content:
            if line.startswith(COMMENT_MARK) or not line:
                continue
            if COMMENT_MARK in line:
                # in-line comment, remove
                line, _, _ = line.partition(COMMENT_MARK)
            line = line.strip()
            mnemonics.append(line)
        return mnemonics

    def assemble(self, file_path: str) -> list[Instruction]:
        content = self._preprocess_file(file_path)
        symbol_table = self._build_symbol_table(content)
        content = self._resolve_labels(symbol_table, content)
        return content

    @staticmethod
    def _write_to_file(file_name, content):
        try:
            with open(file_name, 'w') as out_file:
                out_file.writelines(content)
        except Exception as exc:
            pass

    def assembly_to_file(self, file_path: str):

        content = self.assemble(file_path)

        output_file = os.path.splitext(file_path)[0] + OUTPUT_FILE_EXTENSION
        self._write_to_file(output_file, content)

    @staticmethod
    def _build_symbol_table(content: List[str]) -> dict:
        address = 0
        _symbol_table = dict(PRE_DEFINED_SYMBOLS)
        for line in content:
            # handle labels
            if line.startswith(LABEL_INST_STARTS_WITH) and line.endswith(LABEL_INST_ENDS_WITH):
                label = line[1:-1]
                if label not in _symbol_table:
                    _symbol_table[label] = address
            else:
                address += 1
        return _symbol_table

    @staticmethod
    def _get_comp_opcode(comp: Mnemonic) -> Opcode:
        try:
            return COMP_SYMBOLS_TABLE[comp]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{comp}' is not valid")

    @staticmethod
    def _get_dest_opcode(dest: Optional[Mnemonic]) -> Opcode:
        try:
            return DEST_SYMBOLS_TABLE[dest]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{dest}' is not valid")

    @staticmethod
    def _get_jump_opcode(jump: Optional[Mnemonic]) -> Opcode:
        try:
            return JUMP_SYMBOLS_TABLE[jump]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{jump}' is not valid")

    def assemble_c_instruction(self, inst: Mnemonic) -> Opcode:
        try:
            dest, comp, jump = None, inst, None
            if ';' in inst:
                comp, jump = inst.split(';')
                if '=' in comp:
                    dest, comp = comp.split('=')
            else:
                if '=' in inst:
                    dest, comp = inst.split('=')

            self.logger.debug(
                'Assembling C instruction: %s with mnemonics dest=%s, comp=%s, jump=%s', inst, dest, comp, jump
            )

            comp_op = self._get_comp_opcode(comp)
            dest_op = self._get_dest_opcode(dest)
            jump_op = self._get_jump_opcode(jump)
        except Exception as exc:
            raise HackySyntaxError(f"Unable to assemble instruction '{inst}'. Reason: {str(exc)}") from exc

        return C_INST_OPCODE + comp_op + dest_op + jump_op

    def assemble_a_instruction(self, inst: int) -> Opcode:
        # has the format @xxx
        self.logger.debug('Assembling A instruction: %s', inst)

        s, e = A_CONSTANT_RANGE
        if not s <= inst <= e:
            raise HackyAInstructionOutOfBoundary(f'Constant must be in the range {A_CONSTANT_RANGE}')

        binary = bin(inst)[2:]
        return A_INST_OPCODE + '0' * (INSTRUCTION_SIZE - len(A_INST_OPCODE) - len(binary)) + binary

    def _resolve_labels(self, symbol_table: SymbolTable, content: List[str]):
        result = []
        curr_var_addr = VAR_INST_START_ADDR
        for line in content:
            if line.startswith(A_INST_MARK):
                line = line[1:]
                if line in symbol_table:
                    inst = symbol_table[line]
                    result.append(self.assemble_a_instruction(inst))
                elif line.isdigit():
                    result.append(self.assemble_a_instruction(int(line)))
                else:
                    # this is a new variable declaration
                    symbol_table[line] = curr_var_addr
                    result.append(self.assemble_a_instruction(symbol_table[line]))
                    curr_var_addr += 1
            elif not line.startswith(LABEL_INST_STARTS_WITH) and not line.endswith(LABEL_INST_ENDS_WITH):
                result.append(self.assemble_c_instruction(line))

        return '\n'.join(result)


if __name__ == '__main__':
    import sys

    filepath = sys.argv[1]
    print(sys.argv)
    hacky = HackyAssembler()
    out = hacky.assembly_to_file(filepath)
    print(out)
