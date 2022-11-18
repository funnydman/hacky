import os
from pathlib import Path
from typing import List

from constants import (
    A_INST_MARK,
    LABEL_STARTS_WITH,
    LABEL_ENDS_WITH,
    INPUT_FILE_EXTENSION,
    COMMENT_MARK,
    OUTPUT_FILE_EXTENSION
)
from constants import Instruction
from exceptions import (
    HackyFailedToProcessFileError,
    HackyFailedToWriteFile
)
from symbols import PRE_DEFINED_SYMBOLS

SOURCE_BASE_PATH = Path(__file__).parent
PROJECT_BASE_PATH = SOURCE_BASE_PATH.parent


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

        instructions: list[Instruction] = []
        content = self._read_file(file_path)
        for line in content:
            if line.startswith(COMMENT_MARK) or not line:
                continue
            if COMMENT_MARK in line:
                # in-line comment, remove
                line, _, _ = line.partition(COMMENT_MARK)
            line = line.strip()
            instructions.append(line)
        return instructions

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
