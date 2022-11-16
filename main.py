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
from typing import List, Optional

from exceptions import HackySyntaxError
from symbols import PRE_DEFINED_SYMBOLS, DEST_SYMBOLS_TABLE, JUMP_SYMBOLS_TABLE, COMP_SYMBOLS_TABLE

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

A_INST_MARK = '@'
C_INST_OPCODE = '111'
A_INST_OPCODE = '0'
VAR_INST_START_ADDR = 16
INSTRUCTION_SIZE = 16
LABEL_INST_STARTS_WITH = '('
LABEL_INST_ENDS_WITH = ')'
COMMENT_MARK = '//'


class HackyAssembler:
    def __init__(self):
        self._symbol_table = dict(PRE_DEFINED_SYMBOLS)

    @staticmethod
    def _read_file(file_path: str) -> List[str]:
        _file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        with open(_file_path, 'r') as file:
            lines = file.read().splitlines()
        return lines

    def _preprocess_file(self, file_path: str) -> List[str]:
        """
        Remove empty lines, comments and strip
        """

        filtered = []
        content = self._read_file(file_path)
        for line in content:
            if line.startswith(COMMENT_MARK) or not line:
                continue
            if COMMENT_MARK in line:
                # in-line comment, remove
                line, _, _ = line.partition(COMMENT_MARK)
            line = line.strip()
            filtered.append(line)
        return filtered

    def assemble(self, file_path: str):
        content = self._preprocess_file(file_path)
        self._build_symbols_table(content)
        content = self._resolve_labels(content)
        return content

    def _build_symbols_table(self, content: List[str]) -> None:
        address = 0
        for line in content:
            # handle labels
            if line.startswith(LABEL_INST_STARTS_WITH) and line.endswith(LABEL_INST_ENDS_WITH):
                label = line[1:-1]
                if label not in self._symbol_table:
                    self._symbol_table[label] = address
            else:
                address += 1

    @staticmethod
    def _get_comp_opcode(comp: str) -> str:
        try:
            return COMP_SYMBOLS_TABLE[comp]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{comp}' is not valid")

    @staticmethod
    def _get_dest_opcode(dest: Optional[str]) -> str:
        try:
            return DEST_SYMBOLS_TABLE[dest]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{dest}' is not valid")

    @staticmethod
    def _get_jump_opcode(jump: Optional[str]) -> str:
        try:
            return JUMP_SYMBOLS_TABLE[jump]
        except KeyError:
            raise HackySyntaxError(f"Instruction mnemonic '{jump}' is not valid")

    def assemble_c_instruction(self, inst: str) -> str:
        try:
            dest, comp, jump = None, inst, None
            if ';' in inst:
                comp, jump = inst.split(';')
                if '=' in comp:
                    dest, comp = comp.split('=')
            else:
                if '=' in inst:
                    dest, comp = inst.split('=')

            logging.info(
                'Assembling C instruction: %s with mnemonics dest=%s, comp=%s, jump=%s', inst, dest, comp, jump
            )

            comp_op = self._get_comp_opcode(comp)
            dest_op = self._get_dest_opcode(dest)
            jump_op = self._get_jump_opcode(jump)
        except Exception as exc:
            raise HackySyntaxError(f"Unable to assemble instruction '{inst}'. Reason: {str(exc)}") from exc

        return C_INST_OPCODE + comp_op + dest_op + jump_op

    @staticmethod
    def assemble_a_instruction(inst: int) -> str:
        logging.info('Assembling A instruction: %s', inst)
        binary = bin(inst)[2:]
        return A_INST_OPCODE + '0' * (INSTRUCTION_SIZE - len(A_INST_OPCODE) - len(binary)) + binary

    def _resolve_labels(self, content: List[str]):
        result = []
        curr_var_addr = VAR_INST_START_ADDR
        for line in content:
            if line.startswith(A_INST_MARK):
                line = line[1:]
                if line in self._symbol_table:
                    inst = self._symbol_table[line]
                    result.append(self.assemble_a_instruction(inst))
                elif line.isdigit():
                    result.append(self.assemble_a_instruction(int(line)))
                else:
                    # this is a new variable declaration
                    self._symbol_table[line] = curr_var_addr
                    result.append(self.assemble_a_instruction(self._symbol_table[line]))
                    curr_var_addr += 1
            elif not line.startswith(LABEL_INST_STARTS_WITH) and not line.endswith(LABEL_INST_ENDS_WITH):
                result.append(self.assemble_c_instruction(line))

        return '\n'.join(result)


if __name__ == '__main__':
    import sys

    file_path = sys.argv[1]
    hacky = HackyAssembler()
    out = hacky.assemble(file_path)
    print(out)
