import string
from typing import TypeVar

A_INST_MARK = '@'
A_INST_OPCODE = '0'
C_INST_OPCODE = '111'
VAR_INST_START_ADDR = 16
INSTRUCTION_SIZE = 16
LABEL_STARTS_WITH = '('
LABEL_ENDS_WITH = ')'
COMMENT_MARK = '//'

INPUT_FILE_EXTENSION = '.asm'
OUTPUT_FILE_EXTENSION = '.hack'

ALLOWED_SYMBOL_CHARS = string.ascii_letters + string.digits + '_.$:'
A_CONSTANT_RANGE = (0, 32767)

AInstruction = TypeVar('AInstruction', bound=str)
CInstruction = TypeVar('CInstruction', bound=str)

CCompPartInst = TypeVar('CCompPartInst', bound=str)
CJumpPartInst = TypeVar('CJumpPartInst', bound=str)
CDestPartInst = TypeVar('CDestPartInst', bound=str)

Instruction = TypeVar('Instruction', bound=str)
# must be sub-typed from Instruction somehow

Opcode = TypeVar('Opcode', bound=str)
CompOpcode = TypeVar('CompOpcode', bound=str)
JumpOpcode = TypeVar('JumpOpcode', bound=str)
DestOpcode = TypeVar('DestOpcode', bound=str)

SymbolTable = TypeVar('SymbolTable', bound=dict)
