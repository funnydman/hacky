import re
from pathlib import Path
from unittest.mock import patch

import pytest

from constants import C_INST_OPCODE, A_INST_OPCODE
from exceptions import HackySyntaxError, HackyFailedToProcessFileError, HackyInternalError
from hacky import HackyAssembler
from helper import PROJECT_BASE_PATH
from symbols import PRE_DEFINED_SYMBOLS


class TestHackyAssembler:
    TEST_FILE_PATH = '/path/to/file.asm'
    TEST_FIXTURES_PATH = PROJECT_BASE_PATH / 'tests/fixtures/'

    def get_fixture_file(self, file_name):
        return Path(self.TEST_FIXTURES_PATH) / file_name

    @pytest.fixture
    def symbol_table(self):
        yield dict(PRE_DEFINED_SYMBOLS)

    @pytest.fixture
    def hacky(self):
        yield HackyAssembler()

    @pytest.mark.parametrize('test_file, result', (
            (
                    "empty.asm",
                    ""
            ),
            (
                    "with_labels.asm",
                    "\n".join(["0000000000000000", "1110101010000111"])
            ),
            (
                    'inc_value_on_ram.asm',
                    "\n".join(["0000000000000000", "1111110000010000", "0000000000000001", "1110011111001000"])
            ),
            (
                    'max.asm',
                    "\n".join([
                        "0000000000000000", "1111110000010000", "0000000000000001", "1111010011010000",
                        "0000000000001010", "1110001100000001", "0000000000000001", "1111110000010000",
                        "0000000000001100", "1110101010000111", "0000000000000000", "1111110000010000",
                        "0000000000000010", "1110001100001000", "0000000000001110", "1110101010000111",
                    ]
                    )
            ),
            (
                    "add.asm",
                    "\n".join([
                        "0000000000000010", "1110110000010000", "0000000000000011", "1110000010010000",
                        "0000000000000000", "1110001100001000", "0000000000000110", "1110101010000111"
                    ])
            ),
            (
                    "rect.asm",
                    "\n".join([
                        "0000000000000000", "1111110000010000", "0000000000010111", "1110001100000110",
                        "0000000000010000", "1110001100001000", "0100000000000000", "1110110000010000",
                        "0000000000010001", "1110001100001000", "0000000000010001", "1111110000100000",
                        "1110111010001000", "0000000000010001", "1111110000010000", "0000000000100000",
                        "1110000010010000", "0000000000010001", "1110001100001000", "0000000000010000",
                        "1111110010011000", "0000000000001010", "1110001100000001", "0000000000010111",
                        "1110101010000111"
                    ])
            ),
    ))
    def test_assemble(self, hacky, test_file, result):
        test_file = self.get_fixture_file(test_file)
        assert hacky.assemble(test_file) == result

    def test_assemble_file_not_found(self, hacky):
        with pytest.raises(
                HackyFailedToProcessFileError,
                match=re.escape(
                    f"Unable to process the file. Reason: [Errno 2] No such file or directory: '{self.TEST_FILE_PATH}'")
        ):
            hacky.assemble(self.TEST_FILE_PATH)

    def test_assemble_invalid_file_extension(self, hacky):
        with pytest.raises(
                HackyFailedToProcessFileError,
                match="Invalid file extension, expected: '.asm', got: '.as'"
        ):
            hacky.assemble('/some/file.as')

    @pytest.mark.parametrize('content, result', (
            (
                    [
                        "(LOOP)",
                        "@LOOP",
                        "0;JMP",
                    ],
                    "0000000000000000\n"
                    "1110101010000111"
            ),
            (
                    [
                        "@R0",
                        "D=M",
                        "@R1",
                        "M=D+1"
                    ],
                    "0000000000000000\n"
                    "1111110000010000\n"
                    "0000000000000001\n"
                    "1110011111001000"
            ),
            (
                    ["@R0", "D=M", "@R2", "M=0", "@i",
                     "M=0", "(LOOP)", "@R0", "D=M", "@i",
                     "D=D-M", "@END", "D;JEQ", "@R1",
                     "D=M", "@R2", "M=D+M", "@i", "M=M+1",
                     "@LOOP", "0;JMP", "(END)", "@END", "0;JMP"
                     ],
                    '\n'.join([
                        "0000000000000000", "1111110000010000", "0000000000000010", "1110101010001000",
                        "0000000000010000", "1110101010001000", "0000000000000000", "1111110000010000",
                        "0000000000010000", "1111010011010000", "0000000000010100", "1110001100000010",
                        "0000000000000001", "1111110000010000", "0000000000000010", "1111000010001000",
                        "0000000000010000", "1111110111001000", "0000000000000110", "1110101010000111",
                        "0000000000010100", "1110101010000111"
                    ])

            ),
    ))
    @patch('hacky.HackyAssembler._preprocess_file')
    def test_assemble_(self, mock__preprocess_file, hacky, content, result):
        mock__preprocess_file.return_value = content
        assert hacky.assemble(self.TEST_FILE_PATH) == result

    @pytest.mark.parametrize('inst, opcode', (
            # dest = comp ; jump
            # opcode + comp + dest + jump
            ("M=M+1;JGT", C_INST_OPCODE + '1' + '110111' + '001' + '001'),
            ("0;JMP", C_INST_OPCODE + '0' + '101010' + '000' + '111'),
            ("D;JGT", C_INST_OPCODE + '0' + '001100' + '000' + '001'),
            ("D;JEQ", C_INST_OPCODE + '0' + '001100' + '000' + '010'),
            ("D-M;JLE", C_INST_OPCODE + '1' + '010011' + '000' + '110'),
            ("D=M", C_INST_OPCODE + '1' + '110000' + '010' + '000'),
            ("M=D+1", C_INST_OPCODE + '0' + '011111' + '001' + '000'),
            ("M=0", C_INST_OPCODE + '0' + '101010' + '001' + '000'),
            # do nothing instructions examples
            ("D", C_INST_OPCODE + '0' + '001100' + '000' + '000'),
            ("M+1", C_INST_OPCODE + '1' + '110111' + '000' + '000'),
            ("D=D", C_INST_OPCODE + '0' + '001100' + '010' + '000'),
    ))
    def test_assemble_c_instruction(self, hacky, inst, opcode):
        assert hacky.assemble_c_instruction(inst) == opcode

    @pytest.mark.parametrize('inst, error_str', (
            (
                    "B=M+1",
                    "Unable to assemble instruction 'B=M+1'. Reason: Instruction mnemonic 'B' is not valid"
            ),
            (
                    "D=M+2",
                    "Unable to assemble instruction 'D=M+2'. Reason: Instruction mnemonic 'M+2' is not valid"
            ),
            (
                    "D=M+1;JJJ",
                    "Unable to assemble instruction 'D=M+1;JJJ'. Reason: Instruction mnemonic 'JJJ' is not valid"
            ),
    ))
    def test_assemble_c_instruction_syntax_error(self, hacky, inst, error_str):
        with pytest.raises(HackySyntaxError, match=re.escape(error_str)):
            hacky.assemble_c_instruction(inst)

    @pytest.mark.parametrize('inst, opcode', (
            # opcode[0] + value[15]
            ('@R0', A_INST_OPCODE + '000000000000000'),
            ('@R1', A_INST_OPCODE + '000000000000001'),
            ('@R2', A_INST_OPCODE + '000000000000010'),
            ('@R3', A_INST_OPCODE + '000000000000011'),
            ('@R4', A_INST_OPCODE + '000000000000100'),
            ('@R5', A_INST_OPCODE + '000000000000101'),
            ('@R6', A_INST_OPCODE + '000000000000110'),
            ('@R7', A_INST_OPCODE + '000000000000111'),
            ('@R8', A_INST_OPCODE + '000000000001000'),
            ('@R9', A_INST_OPCODE + '000000000001001'),
            ('@R10', A_INST_OPCODE + '000000000001010'),
            ('@R11', A_INST_OPCODE + '000000000001011'),
            ('@R12', A_INST_OPCODE + '000000000001100'),
            ('@R13', A_INST_OPCODE + '000000000001101'),
            ('@R14', A_INST_OPCODE + '000000000001110'),
            ('@R15', A_INST_OPCODE + '000000000001111'),
            ('@SCREEN', A_INST_OPCODE + '100000000000000'),
            ('@KBD', A_INST_OPCODE + '110000000000000'),
            ('@SP', A_INST_OPCODE + '000000000000000'),
            ('@LCL', A_INST_OPCODE + '000000000000001'),
            ('@ARG', A_INST_OPCODE + '000000000000010'),
            ('@THIS', A_INST_OPCODE + '000000000000011'),
            ('@THAT', A_INST_OPCODE + '000000000000100'),
            # testing absolute addressing mode
            ('@0', A_INST_OPCODE + '000000000000000'),
            ('@1', A_INST_OPCODE + '000000000000001'),
            ('@16384', A_INST_OPCODE + '100000000000000'),
            ('@24576', A_INST_OPCODE + '110000000000000'),

    ))
    def test_assemble_a_instruction(self, symbol_table, hacky, inst, opcode):
        assert hacky.assemble_a_instruction(inst, symbol_table) == opcode

    @pytest.mark.parametrize('inst', (
            '@-1',
            '@32768',
            '@99999'
    ))
    def test_assemble_a_instruction_out_of_boundary_error(self, symbol_table, hacky, inst):
        with pytest.raises(
                HackyInternalError,
                match=re.escape('Constant must be in the range (0, 32767)')
        ):
            assert hacky.assemble_a_instruction(inst, symbol_table)

    @pytest.mark.parametrize('inst', (
            '@label',
            '@var'
    ))
    def test_assemble_a_instruction_resolving_error(self, symbol_table, hacky, inst):
        with pytest.raises(
                HackyInternalError,
                match=re.escape(f'Can not resolve "{inst}" instruction')
        ):
            assert hacky.assemble_a_instruction(inst, symbol_table)
