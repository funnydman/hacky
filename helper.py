import os
from pathlib import Path
from typing import List, Optional

from constants import (
    Instruction,
    A_INST_MARK,
    LABEL_STARTS_WITH,
    LABEL_ENDS_WITH,
    INPUT_FILE_EXTENSION,
    COMMENT_MARK,
    DestOpcode,
    JumpOpcode,
    CompOpcode,
    AInstruction,
    SymbolTable,
    OUTPUT_FILE_EXTENSION, CDestPartInst, CJumpPartInst, CCompPartInst
)
from exceptions import (
    HackySyntaxError,
    HackyFailedToProcessFileError, HackyInternalError, HackyFailedToWriteFile
)
from symbols import PRE_DEFINED_SYMBOLS, DEST_SYMBOLS_TABLE, JUMP_SYMBOLS_TABLE, COMP_SYMBOLS_TABLE

PROJECT_BASE_PATH = Path(__file__).parent


class HackyAssemblerHelper:
    @staticmethod
    def _is_a_instruction(inst: Instruction) -> bool:
        return inst.startswith(A_INST_MARK)

    @staticmethod
    def _is_label(astr: str) -> bool:
        return astr.startswith(LABEL_STARTS_WITH) and astr.endswith(LABEL_ENDS_WITH)

    @staticmethod
    def _get_constant_value(inst: Instruction) -> str:
        return inst.removeprefix(A_INST_MARK)

    @staticmethod
    def _get_binary(val: int) -> str:
        return bin(val)[2:]

    @staticmethod
    def _get_label_name(astr: str) -> str:
        astr = astr.removeprefix(LABEL_STARTS_WITH)
        return astr.removesuffix(LABEL_ENDS_WITH)

    @staticmethod
    def _validate_file_extension(file_path: str) -> None:
        _, file_extension = os.path.splitext(file_path)
        if file_extension != INPUT_FILE_EXTENSION:
            raise HackyFailedToProcessFileError(
                f"Invalid file extension, expected: '{INPUT_FILE_EXTENSION}', got: '{file_extension}'"
            )

    @staticmethod
    def _write_to_file(file_name: str, content) -> None:
        try:
            with open(file_name, 'w', encoding='utf-8') as out_file:
                out_file.writelines(content)
        except OSError as exc:
            raise HackyFailedToWriteFile(f'Unable to save file. Reason: {exc}') from exc

    @staticmethod
    def _read_file(file_path: str) -> list[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.read().splitlines()
            return lines
        except (OSError, FileNotFoundError) as exc:
            raise HackyFailedToProcessFileError(f'Unable to process the file. Reason: {str(exc)}') from exc

    def _preprocess_file(self, file_path: str) -> List[Instruction]:
        """
        Remove empty lines, comments and strip
        """
        self._validate_file_extension(file_path)

        mnemonics: list[Instruction] = []
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

    def _build_symbol_table(self, content: List[str]) -> dict:
        curr_addr = 0
        symbol_table = dict(PRE_DEFINED_SYMBOLS)
        for line in content:
            if self._is_label(line):
                label = self._get_label_name(line)
                if label not in symbol_table:
                    symbol_table[label] = curr_addr
            else:
                curr_addr += 1
        return symbol_table

    @staticmethod
    def _get_comp_opcode(comp: CCompPartInst) -> CompOpcode:
        try:
            return COMP_SYMBOLS_TABLE[comp]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{comp}' is not valid") from exc

    @staticmethod
    def _get_dest_opcode(dest: Optional[CDestPartInst]) -> DestOpcode:
        try:
            return DEST_SYMBOLS_TABLE[dest]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{dest}' is not valid") from exc

    @staticmethod
    def _get_jump_opcode(jump: Optional[CJumpPartInst]) -> JumpOpcode:
        try:
            return JUMP_SYMBOLS_TABLE[jump]
        except KeyError as exc:
            raise HackySyntaxError(f"Instruction mnemonic '{jump}' is not valid") from exc

    @staticmethod
    def _parse_c_instruction(inst: Instruction) -> tuple[
        Optional[DestOpcode],
        CompOpcode,
        Optional[JumpOpcode]
    ]:
        dest: Optional[CDestPartInst] = None
        comp: CCompPartInst = inst
        jump: Optional[CJumpPartInst] = None

        if ';' in inst:
            comp, jump = inst.split(';')
            if '=' in comp:
                dest, comp = comp.split('=')
        else:
            if '=' in inst:
                dest, comp = inst.split('=')
        return dest, comp, jump

    def _parse_a_instruction(self, inst: AInstruction, symbol_table: SymbolTable) -> int:
        a_const: str = self._get_constant_value(inst)
        if self._is_absolute_address(a_const):
            a_const = int(a_const)
        else:
            a_const = symbol_table.get(a_const)
            if a_const is None:
                raise HackyInternalError(f'Can not resolve "{inst}" instruction')
        return a_const

    def _is_c_instruction(self, inst: Instruction) -> bool:
        return not self._is_a_instruction(inst) and not self._is_label(inst)

    @staticmethod
    def _is_absolute_address(astr: str) -> bool:
        try:
            int(astr)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _get_base_filename(file_path: str) -> str:
        return os.path.splitext(file_path)[0]

    def _get_output_file(self, file_path: str) -> str:
        return self._get_base_filename(file_path) + OUTPUT_FILE_EXTENSION
