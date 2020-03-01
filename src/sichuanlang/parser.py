# coding: utf-8
from __future__ import absolute_import

from ast import Add
from ast import And
from ast import Assert
from ast import Assign
from ast import AsyncFor
from ast import AsyncFunctionDef
from ast import AsyncWith
from ast import Attribute
from ast import AugAssign
from ast import Await
from ast import BinOp
from ast import BitAnd
from ast import BitOr
from ast import BitXor
from ast import BoolOp
from ast import Break
from ast import Call
from ast import ClassDef
from ast import Compare
from ast import Continue
from ast import Del
from ast import Delete
from ast import Dict
from ast import Div
from ast import Eq
from ast import ExceptHandler
from ast import Expr
from ast import FloorDiv
from ast import For
from ast import FunctionDef
from ast import GeneratorExp
from ast import Global
from ast import Gt
from ast import GtE
from ast import If
from ast import IfExp
from ast import Import
from ast import ImportFrom
from ast import In
from ast import Index
from ast import Invert
from ast import Is
from ast import IsNot
from ast import List
from ast import ListComp
from ast import Load
from ast import LShift
from ast import Lt
from ast import LtE
from ast import Mod
from ast import Module
from ast import Mult
from ast import Name
from ast import NameConstant
from ast import Nonlocal
from ast import Not
from ast import NotEq
from ast import NotIn
from ast import Num
from ast import Or
from ast import Pass
from ast import Pow
from ast import Raise
from ast import Return
from ast import RShift
from ast import Set
from ast import Slice
from ast import Starred
from ast import Store
from ast import Str
from ast import Sub
from ast import Subscript
from ast import Try
from ast import Tuple
from ast import UnaryOp
from ast import USub
from ast import While
from ast import With
from ast import Yield
from ast import YieldFrom
from ast import alias
from ast import arg
from ast import arguments
from ast import comprehension
from ast import expr as ExprBase
from ast import keyword
from ast import withitem
import re
import sys
from traceback import format_exception

from .hanzi_util import HANZI_DIGITS_AND_UNITS
from .hanzi_util import hanzi_digits_to_value


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class ParsingError(Exception):
    pass


class LexError(ParsingError):

    def __init__(
        self,
        txt,
        pos,
        row,
        col,
        msg=None,
    ):
        # Input string.
        self.txt = txt

        # Input string length.
        self.txt_len = len(txt)

        # Input lines.
        self.lines = txt.split('\n')

        # Current line.
        self.line = self.lines[row]

        # Current position index.
        self.pos = pos

        # Current row index.
        self.row = row

        # Current column index.
        self.col = col

        # Error message.
        self.msg = msg

    def __str__(self):
        narrow_column_index = get_narrow_column_index(self.line, self.col)

        col_mark = ' ' * narrow_column_index + '|'

        source_text = (
            '```\n'
            '{0}\n'
            '{1}\n'
            '```'
        ).format(self.line, col_mark)

        text = (
            '词法解析无法处理：第{row}行，第{col}列，全文第{pos}个字符。\n'
            '{msg}'
            '{source_text}'
        ).format(
            row=self.row + 1,
            col=self.col + 1,
            pos=self.pos + 1,
            msg='' if self.msg is None else self.msg + '\n',
            source_text=source_text,
        )

        current_char = self.txt[self.pos]

        if self.pos + 1 < self.txt_len:
            next_char = self.txt[self.pos + 1]
        else:
            next_char = None

        if current_char == ',':
            text += '\n请用中文逗号`，`。'
        elif current_char == ':':
            text += '\n请用中文冒号`：`。'
        elif current_char == ';':
            text += '\n请用中文分号`；`。'
        elif current_char == '#':
            text += '\n请用中文井号`＃`。'
        elif current_char == '\'':
            text += '\n请用中文单引号`‘’`。'
        elif current_char == '"':
            text += '\n请用中文双引号`“”`。'
        elif current_char == '(':
            text += '\n请用中文括号`（`。'
        elif current_char == ')':
            text += '\n请用中文括号`）`。'
        elif current_char == '[':
            text += '\n列表常量请用`箱箱`。索引访问请用`第某项`。'
        elif current_char == ']':
            text += '\n列表常量请用`箱箱`。索引访问请用`第某项`。'
        elif current_char == '{':
            text += '\n字典常量请用`盒盒`。集合常量请用`袋袋`。'
        elif current_char == '}':
            text += '\n字典常量请用`盒盒`。集合常量请用`袋袋`。'
        elif current_char == '.':
            text += '\n访问属性请用`咧`。'
        elif current_char == '+':
            if next_char == '+':
                text += '\n自增运算请用`加滴点儿`。'
            else:
                text += '\n加法运算请用`加`。'
        elif current_char == '-':
            if next_char == '-':
                text += '\n自减运算请用`减滴点儿`。'
            else:
                text += '\n减法运算请用`减`。'
        elif current_char == '*':
            if next_char == '*':
                text += '\n指数运算请用`算指数`。'
            else:
                text += '\n乘法运算请用`乘`。'
        elif current_char == '/':
            if next_char == '/':
                text += '\n整数除法运算请用`整除`。'
            else:
                text += '\n除法运算请用`除`。'
        elif current_char == '%':
            text += '\n余数运算请用`算余数`。'
        elif current_char == '~':
            text += '\n比特反转运算请用`比特反转`。'
        elif current_char == '&':
            if next_char == '&':
                text += '\n逻辑与运算请用`并且`。'
            else:
                text += '\n比特与运算请用`比特与`。'
        elif current_char == '|':
            if next_char == '|':
                text += '\n逻辑或运算请用`或者`。'
            else:
                text += '\n比特或运算请用`比特与`。'
        elif current_char == '!':
            if next_char == '=':
                text += '\n不等于运算请用`不等于`。'
            else:
                text += '\n逻辑非运算请用`并非`。'
        elif current_char == '=':
            if next_char == '=':
                text += '\n等于运算请用`等于`。'
            else:
                text += '\n赋值请用`搁`。'
        elif current_char == '<':
            if next_char == '<':
                text += '\n比特左移运算请用`比特左移`。'
            elif next_char == '=':
                text += '\n小于等于运算请用`小于等于`。'
            else:
                text += '\n小于运算请用`小于`。'
        elif current_char == '>':
            if next_char == '>':
                text += '\n比特比特运算请用`比特右移`。'
            elif next_char == '=':
                text += '\n大于等于运算请用`大于等于`。'
            else:
                text += '\n大于运算请用`大于`。'

        return text


class SyntaxError(ParsingError):

    def __init__(
        self,
        ctx,
        txt,
        pos,
        row,
        col,
        token_name=None,
        token_names=[],
        eis=None,
        eisp=None,
        msg=None,
    ):
        # Current context.
        self.ctx = ctx

        # Input string.
        self.txt = txt

        # Input lines.
        self.lines = txt.split('\n')

        # Current line.
        self.line = self.lines[row]

        # Current position index.
        self.pos = pos

        # Current row index.
        self.row = row

        # Current column index.
        self.col = col

        # Current token name.
        self.current_token_name = token_name

        # Wanted token names.
        self.wanted_token_names = token_names

        # Scanning exception infos of current branch.
        self.eis = eis

        # Scanning exception infos of previous branch.
        self.eisp = eisp

        # Error message.
        self.msg = msg

    def __str__(self):
        ctx_names = get_ctx_names(self.ctx)

        ctx_msg = ' '.join(ctx_names) if ctx_names else ''

        msg = self.msg

        if msg is None:
            msg = ''

            if self.wanted_token_names:
                msg += '期待符号：`{0}`。\n'.format(
                    ' | '.join(self.wanted_token_names)
                )

            msg += (
                '遇到符号：`{0}`。\n'.format(self.current_token_name)
                if self.current_token_name is not None
                else '遇到输入结束。\n'
            )

        narrow_column_index = get_narrow_column_index(self.line, self.col)

        col_mark = ' ' * narrow_column_index + '|'

        source_text = (
            '```\n'
            '{0}\n'
            '{1}\n'
            '```'
        ).format(self.line, col_mark)

        text = (
            '语法解析无法处理：规则`{rule_name}`，第{row}行，第{col}列，全文第' +
            '{pos}个字符。\n上下文：{ctx_msg}。\n' +
            msg +
            '{source_text}'
        ).format(
            rule_name=self.ctx.name,
            ctx_msg=ctx_msg,
            row=self.row + 1,
            col=self.col + 1,
            pos=self.pos + 1,
            source_text=source_text,
        )

        return text


class Parser(object):

    _RULE_FUNC_PRF = ''

    _RULE_FUNC_POF = ''

    # `DK` means debug dict key
    #
    # Rule name.
    _DK_NAME = 'name'

    # Input text.
    _DK_TXT = 'txt'

    # Position index.
    _DK_POS = 'pos'

    # Row index.
    _DK_ROW = 'row'

    # Column index.
    _DK_COL = 'col'

    # Scanning level.
    _DK_SLV = 'slv'

    # Scanning is successful.
    _DK_SSS = 'sss'

    WHITESPACE_TOKEN_NAME = ''

    NUMBER_REO = re.compile(r"""
# Binary.
([-+])?0[Bb][01_]+(?<!_)
|
# Octal.
([-+])?0[Oo][0-7_]+(?<!_)
|
# Hexadecimal.
([-+])?0[Xx][0-9a-fA-F_]+(?<!_)
|
# Decimal.
([-+])?                         # Sign.
(?=[\d_]|[.][\d_])              # An integer part or a fraction part follows.
(?!_)([\d_]*)(?<!_)             # Integer part.
([.](?!_)[\d_]*(?<!_))?         # Fraction part.
([Ee][-+]?(?!_)[\d_]+(?<!_))?   # Exponent part.
""", re.VERBOSE)

    NAME_FIRST_CHAR_REO = re.compile(r'[a-zA-Z_\u4e00-\u9fa5]')

    NAME_FOLLOW_CHAR_REO = re.compile(r'[a-zA-Z0-9_\u4e00-\u9fa5]')

    KEYWORD_INFOS = (
        ('comma_hz', '，'),
        ('pause_hz', '、'),
        ('colon_hz', '：'),
        ('semicolon_hz', '；'),
        ('period_hz', '。'),
        ('question_mark_hz', '？'),
        ('left_parenthesis_hz', '（'),
        ('right_parenthesis_hz', '）'),
        ('none_kw', '虚嘞'),
        ('bool_true_kw', '真嘞'),
        ('bool_false_kw', '假嘞'),
        ('list_kw', '箱箱'),
        ('list_with_kw', '箱箱装'),
        ('tuple_kw', '包包'),
        ('tuple_with_kw', '包包装'),
        ('dict_kw', '盒盒'),
        ('dict_with_kw', '盒盒装'),
        ('set_kw', '袋袋'),
        ('set_with_kw', '袋袋装'),
        ('assign_op', '搁'),
        ('global_kw', '在外头'),
        ('nonlocal_kw', '在上头'),
        ('not_op', '并非'),
        ('or_op', '或者'),
        ('and_op', '并且'),
        ('is_op', '就是'),
        ('isnot_op', '不是'),
        ('equal_op', '等于'),
        ('not_equal_op', '不等于'),
        ('lt_op', '小于'),
        ('le_op', '小于等于'),
        ('gt_op', '大于'),
        ('ge_op', '大于等于'),
        ('in_op', '存在于'),
        ('not_in_op', '不存在于'),
        ('arrow_op', '接倒起'),
        ('bit_and_op', '比特与'),
        ('bit_and_assign_op', '比特与搁'),
        ('bit_or_op', '比特或'),
        ('bit_or_assign_op', '比特或搁'),
        ('bit_xor_op', '比特异或'),
        ('bit_xor_assign_op', '比特异或搁'),
        ('bit_left_shift_op', '比特左移'),
        ('bit_left_shift_assign_op', '比特左移搁'),
        ('bit_right_shift_op', '比特右移'),
        ('bit_right_shift_assign_op', '比特右移搁'),
        ('bit_invert_op', '比特反转'),
        ('bit_invert_assign_op', '比特反转搁'),
        ('increment_op', '加滴点儿'),
        ('decrement_op', '减滴点儿'),
        ('add_op', '加'),
        ('add_assign_op', '加搁'),
        ('subtract_op', '减'),
        ('subtract_assign_op', '减搁'),
        ('multiply_op', '乘'),
        ('multiply_assign_op', '乘搁'),
        ('divide_op', '除'),
        ('divide_assign_op', '除搁'),
        ('floor_divide_op', '整除'),
        ('floor_divide_assign_op', '整除搁'),
        ('modulo_op', '算余数'),
        ('modulo_assign_op', '算余数搁'),
        ('power_op', '算指数'),
        ('power_assign_op', '算指数搁'),
        ('unary_subtract_op', '负'),
        ('dot_kw', '咧'),
        ('subscript_start_kw', '第'),
        ('subscript_end_kw', '项'),
        ('comp_item_as_name_kw', '每项交给'),
        ('async_comp_item_as_name_kw', '每项慢慢交给'),
        ('comp_if_kw', '要是'),
        ('comp_then_kw', '然后'),
        ('listcomp_generate_kw', '生成'),
        ('generator_generate_kw', '慢慢生成'),
        ('if_kw', '如果'),
        ('elif_kw', '又如果'),
        ('else_kw', '要不然'),
        ('block_start_kw', '弄个整'),
        ('block_end_kw', '就弄个'),
        ('loop_always_kw', '莽起整'),
        ('loop_if_kw', '莽起整要是'),
        ('loop_until_kw', '莽起整直到'),
        ('loop_iterator_kw', '挨倒把'),
        ('async_loop_iterator_kw', '挨倒慢慢把'),
        ('loop_iterator_item_as_name_kw', '每项给'),
        ('continue_kw', '接倒整'),
        ('break_kw', '不整了'),
        ('try_kw', '试一哈'),
        ('except_kw', '抓一哈'),
        ('finally_kw', '最后才'),
        ('raise_kw', '放飞'),
        ('raise_from_kw', '带起'),
        ('with_kw', '用一哈'),
        ('async_with_kw', '慢慢用一哈'),
        ('yield_kw', '让一哈'),
        ('yield_from_kw', '让一哈哈儿'),
        ('await_kw', '等一哈'),
        ('func_start_kw', '过场'),
        ('async_func_start_kw', '过场慢'),
        ('func_end_kw', '过场多'),
        ('collect_args_kw', '收拢'),
        ('collect_kwargs_kw', '收拢来'),
        ('expand_args_kw', '展开'),
        ('expand_kwargs_kw', '展开来'),
        ('class_start_kw', '名堂'),
        ('class_end_kw', '名堂多'),
        ('decorate_kw', '打整一哈'),
        ('pass_kw', '搞空名堂'),
        ('del_kw', '丢翻'),
        ('return_kw', '爬开'),
        ('assert_kw', '硬是要'),
        ('exit_kw', '哦嚯'),
        ('print_kw', '开腔'),
        ('import_kw', '来给我扎起'),
        ('from_import_kw', '出来给我扎起'),
        ('as_kw', '叫做'),
        ('trailer_prefix', '嘞'),
        ('type_trailer', '嘞名堂'),
        ('bool_trailer', '嘞真假'),
        ('int_trailer', '嘞整数'),
        ('float_trailer', '嘞浮点数'),
        ('str_trailer', '嘞字符串'),
        ('repr_trailer', '嘞表示'),
        ('bytes_trailer', '嘞字节串'),
        ('bytearray_trailer', '嘞字节数组'),
        ('chr_trailer', '嘞字符'),
        ('ord_trailer', '嘞字符序数'),
        ('hex_trailer', '嘞十六进制'),
        ('oct_trailer', '嘞八进制'),
        ('bin_trailer', '嘞二进制'),
        ('list_trailer', '嘞箱箱'),
        ('tuple_trailer', '嘞包包'),
        ('dict_trailer', '嘞盒盒'),
        ('set_trailer', '嘞袋袋'),
        ('len_trailer', '嘞长度'),
        ('count_trailer', '嘞总数'),
        ('abs_trailer', '嘞绝对值'),
        ('min_trailer', '嘞最小值'),
        ('max_trailer', '嘞最大值'),
        ('opposite_trailer', '嘞相反数'),
        ('reciprocal_trailer', '嘞倒数'),
        ('sum_trailer', '嘞和'),
        ('any_trailer', '嘞任意为真'),
        ('all_trailer', '嘞全部为真'),
        ('range_trailer', '嘞范围内'),
        ('name_trailer', '嘞名字'),
        ('format_trailer', '嘞格式化'),
        ('add_trailer', '嘞添加'),
        ('append_trailer', '嘞后加'),
        ('extend_trailer', '嘞后加每项'),
        ('clear_trailer', '嘞清空'),
        ('sort_trailer', '嘞排序'),
    )

    KEYWORD_INFOS = list(sorted(
        KEYWORD_INFOS,
        key=lambda x: len(x[1]),
        reverse=True,
    ))

    KEYWORDS = set(x[1] for x in KEYWORD_INFOS)

    def __init__(self, txt, debug=False):
        # Input string.
        self._txt = txt

        # Input string length.
        self._txt_len = len(txt)

        # Current position index.
        self._pos = 0

        # Current row index.
        self._row = 0

        # Current column index.
        self._col = 0

        # Debug flag.
        self._debug = debug

        if self._debug:
            self._debug_infos = []
        else:
            self._debug_infos = None

        # Whitespace regex pattern.
        self._ws_rep = r'([ \t]*(＃[^\n]*)?[\n]?)*'

        # Whitespace regex object.
        self._ws_reo = re.compile(self._ws_rep)\
            if self._ws_rep is not None else None

        # Current context dict.
        self._ctx = None

        # Input tokens.
        self._tokens = []

        # Input tokens count.
        self._tokens_count = 0

        # Current token index.
        self._token_index = 0

        # Scanning level.
        self._scan_lv = -1

        # Scanning exception info.
        self._scan_ei = None

        # Scanning exception infos of current branch.
        self._scan_eis = []

        # Scanning exception infos of previous branch.
        self._scan_eis_prev = []

    def _make_tokens(self):
        self._pos = 0
        self._row = 0
        self._col = 0

        name = None

        while self._pos < self._txt_len:
            self._make_whitespace_token()

            if self._pos >= self._txt_len:
                break

            if self._txt[self._pos] == '『':
                markers_count = 1

                pos = self._pos

                while True:
                    pos += 1

                    if pos >= self._txt_len:
                        raise LexError(
                            txt=self._txt,
                            pos=self._pos,
                            row=self._row,
                            col=self._col,
                            msg='在解析注释时遇到输入终结。',
                        )

                    if self._txt[pos] != '『':
                        break

                    markers_count += 1

                while True:
                    if pos >= self._txt_len:
                        raise LexError(
                            txt=self._txt,
                            pos=self._pos,
                            row=self._row,
                            col=self._col,
                            msg='在解析注释时遇到输入终结。',
                        )

                    if self._txt[pos] != '』':
                        pos += 1

                        continue

                    remaining_markers_count = markers_count - 1

                    while remaining_markers_count:
                        pos += 1

                        if pos >= self._txt_len:
                            raise LexError(
                                txt=self._txt,
                                pos=self._pos,
                                row=self._row,
                                col=self._col,
                                msg='在解析字符串字面量时遇到输入终结。',
                            )

                        if self._txt[pos] != '』':
                            break

                        remaining_markers_count -= 1

                    pos += 1

                    if remaining_markers_count == 0:
                        break

                self._add_token(
                    self.WHITESPACE_TOKEN_NAME,
                    self._txt[self._pos:pos],
                )

                continue

            if self._txt[self._pos] == '《':
                name = ''

                pos = self._pos + 1

                while True:
                    if pos >= self._txt_len:
                        break

                    char = self._txt[pos]

                    if char == '》':
                        break

                    name += char

                    pos += 1

                if not name:
                    raise LexError(
                        txt=self._txt,
                        pos=self._pos,
                        row=self._row,
                        col=self._col,
                        msg='标识符不能为空。'.format(name),
                    )

                if name in self.KEYWORDS:
                    raise LexError(
                        txt=self._txt,
                        pos=self._pos,
                        row=self._row,
                        col=self._col,
                        msg='关键字`{0}`不能做为标识符。'.format(name),
                    )

                is_invalid_name = False

                if not self.NAME_FIRST_CHAR_REO.match(name[0]):
                    is_invalid_name = True
                else:
                    for name_char_index in range(1, len(name)):
                        name_char = name[name_char_index]

                        if not self.NAME_FOLLOW_CHAR_REO.match(name_char):
                            is_invalid_name = True

                            break

                if is_invalid_name:
                    raise LexError(
                        txt=self._txt,
                        pos=self._pos,
                        row=self._row,
                        col=self._col,
                        msg='`{0}`不是合规的标识符。'.format(name),
                    )

                self._pos += 1

                self._add_token('name', name)

                name = None

                self._pos += 1

                self._col += 1

                continue

            keyword_info = self._find_keyword(self._pos)

            if keyword_info is not None:
                if name is not None:
                    self._add_token('name', name)

                    name = None

                token_name, keyword = keyword_info

                self._add_token(token_name, keyword)

                continue

            current_char = self._txt[self._pos]

            if current_char in HANZI_DIGITS_AND_UNITS:
                digits = current_char

                pos = self._pos + 1

                while True and pos < self._txt_len:
                    current_char = self._txt[pos]

                    if current_char not in HANZI_DIGITS_AND_UNITS:
                        break

                    digits += current_char

                    pos += 1

                self._add_token('number', digits)

                continue

            match_obj = self.NUMBER_REO.match(self._txt, self._pos)

            if match_obj:
                self._add_token('number', match_obj.group())

                continue

            pos = self._pos

            if current_char == '‘' or current_char == '“':
                start_quote = current_char

                if current_char == '‘':
                    is_double_quote = False
                    end_quote = '’'
                else:
                    is_double_quote = True
                    end_quote = '”'

                quotes_count = 1

                while True:
                    pos += 1

                    if pos >= self._txt_len:
                        raise LexError(
                            txt=self._txt,
                            pos=self._pos,
                            row=self._row,
                            col=self._col,
                            msg='在解析字符串字面量时遇到输入终结。',
                        )

                    current_char = self._txt[pos]

                    if current_char != start_quote:
                        break

                    quotes_count += 1

                chars = []

                while True:
                    if current_char == end_quote:
                        remaining_quotes_count = quotes_count - 1

                        while remaining_quotes_count:
                            pos += 1

                            if pos >= self._txt_len:
                                raise LexError(
                                    txt=self._txt,
                                    pos=self._pos,
                                    row=self._row,
                                    col=self._col,
                                    msg='在解析字符串字面量时遇到输入终结。',
                                )

                            current_char = self._txt[pos]

                            if current_char != end_quote:
                                break

                            remaining_quotes_count -= 1

                        if remaining_quotes_count == 0:
                            pos += 1

                            break

                        chars.append(
                            end_quote * (quotes_count - remaining_quotes_count)
                        )

                        chars.append(current_char)
                    elif is_double_quote and current_char == '\\':
                        pos += 1

                        if pos >= self._txt_len:
                            raise LexError(
                                txt=self._txt,
                                pos=self._pos,
                                row=self._row,
                                col=self._col,
                                msg='在解析字符串字面量时遇到输入终结。',
                            )

                        current_char = self._txt[pos]

                        if current_char == '“' or current_char == '”':
                            chars.append(current_char)
                        else:
                            chars.append('\\')
                            chars.append(current_char)
                    else:
                        chars.append(current_char)

                    pos += 1

                    if pos >= self._txt_len:
                        raise LexError(
                            txt=self._txt,
                            pos=self._pos,
                            row=self._row,
                            col=self._col,
                            msg='在解析字符串字面量时遇到输入终结。',
                        )

                    current_char = self._txt[pos]

                string_value = ''.join(chars)

                if is_double_quote:
                    string_value = string_value.replace('\n', '\\n')
                    string_value = string_value.replace('\'', '\\\'')
                    string_value = '\'{0}\''.format(string_value)
                    string_value = eval(string_value)

                self._add_token('string', self._txt[self._pos:pos])

                self._tokens[-1][1].value = string_value

                continue

            if self._txt[self._pos] == '…':
                self._add_token('name', '…')

                continue

            if self.NAME_FIRST_CHAR_REO.match(self._txt, self._pos):
                pos = self._pos

                name = self._txt[pos]

                pos += 1

                while self.NAME_FOLLOW_CHAR_REO.match(
                    self._txt, pos
                ):
                    keyword_info = self._find_keyword(pos)

                    if keyword_info is not None:
                        self._add_token('name', name)

                        name = None

                        token_name, keyword = keyword_info

                        self._add_token(token_name, keyword)

                        break

                    name += self._txt[pos]

                    pos += 1

                if name is not None:
                    self._add_token('name', name)

                    name = None

                continue

            raise LexError(
                txt=self._txt,
                pos=self._pos,
                row=self._row,
                col=self._col,
            )

        if name is not None:
            self._add_token('name', name)

            name = None

        self._add_token('end', '')

        self._tokens_count = len(self._tokens)

    def _make_whitespace_token(self):
        match_obj = self._ws_reo.match(self._txt, self._pos)

        if match_obj:
            matched_txt = match_obj.group()

            if not matched_txt:
                return

            self._add_token(self.WHITESPACE_TOKEN_NAME, matched_txt)

    def _find_keyword(self, pos):
        for keyword_info in self.KEYWORD_INFOS:
            token_name, keyword = keyword_info

            for char_index, char in enumerate(keyword):
                if self._txt[pos + char_index] != char:
                    break
            else:
                return keyword_info

        return None

    def _add_token(self, token_name, matched_txt):
        token_info = AttrDict()

        token_info.pos = self._pos

        token_info.row = self._row

        token_info.col = self._col

        token_info.txt = matched_txt

        token_info.len = len(matched_txt)

        token_info.rows_count = matched_txt.count('\n') + 1

        token_info.end_row = token_info.row + token_info.rows_count - 1

        if token_info.rows_count == 1:
            token_info.end_col = token_info.col + len(matched_txt)
        else:
            last_row_txt = matched_txt[matched_txt.rfind('\n') + 1:]

            token_info.end_col = len(last_row_txt)

        self._tokens.append((token_name, token_info))

        self._update_pos_row_col(token_info)

    def _update_pos_row_col(self, token_info):
        self._pos = token_info.pos + token_info.len

        matched_txt = token_info.txt

        row_cnt = matched_txt.count('\n')

        if row_cnt == 0:
            self._row = token_info.row

            self._col = token_info.col + len(matched_txt)
        else:
            last_row_txt = matched_txt[matched_txt.rfind('\n') + 1:]

            self._row = token_info.row + row_cnt

            self._col = len(last_row_txt)

    def _get_row_col(self, token_index=None, skip_whitespace=False):
        if self._tokens_count == 0:
            raise ValueError(self._tokens_count)

        if token_index is None:
            token_index = self._token_index

        if token_index > self._tokens_count:
            raise ValueError(token_index)

        if skip_whitespace:
            while True:
                if token_index > self._tokens_count:
                    raise ValueError(token_index)

                if token_index == self._tokens_count:
                    _, last_token_info = self._tokens[-1]

                    return (
                        last_token_info.end_row,
                        last_token_info.end_col
                    )

                token_name, token_info = self._tokens[token_index]

                if token_name == self.WHITESPACE_TOKEN_NAME:
                    token_index += 1

                    continue

                break

            return (token_info.row, token_info.col)
        else:
            if token_index == self._tokens_count:
                _, last_token_info = self._tokens[-1]

                return (
                    last_token_info.end_row,
                    last_token_info.end_col
                )

            _, token_info = self._tokens[token_index]

            return (token_info.row, token_info.col)

    def _get_start_row_col(self):
        row, col = self._get_row_col(skip_whitespace=True)

        return (row + 1, col + 1)

    def _get_end_row_col(self):
        row, col = self._get_row_col(skip_whitespace=False)

        return (row + 1, col + 1)

    def _get_token_index(self, skip_whitespace=True):
        token_index = self._token_index

        if skip_whitespace:
            while True:
                if token_index >= self._tokens_count:
                    return None

                current_token_name, _ = self._tokens[token_index]

                if current_token_name == self.WHITESPACE_TOKEN_NAME:
                    token_index += 1

                    continue

                break
        else:
            if token_index >= self._tokens_count:
                return None

        return token_index

    def _get_ctx_attr(self, ctx, attr_name, default=None):
        try:
            return ctx[attr_name]
        except KeyError:
            return default

    def _set_store_ctx(self, node):
        if isinstance(node, (Name, Attribute, Subscript, Tuple)):
            node.ctx = Store()

            if isinstance(node, Tuple):
                for child_node in node.elts:
                    self._set_store_ctx(child_node)
        else:
            raise ValueError(node)

    def _seek(self, token_index):
        if token_index < 0 or token_index >= self._txt_len:
            raise ValueError(token_index)

        self._token_index = token_index

        _, token_info = self._tokens[token_index]

        self._pos = token_info.pos
        self._row = token_info.row
        self._col = token_info.col

    def _retract(self, token_index=None):
        if token_index is None:
            token_index = self._token_index

        while True:
            if token_index == 0:
                break

            token_index -= 1

            if token_index < 0:
                raise ValueError(token_index)

            token_name, _ = self._tokens[
                token_index
            ]

            if token_name != self.WHITESPACE_TOKEN_NAME:
                break

        self._seek(token_index)

    def _peek(self, token_names, is_required=False, is_branch=False):
        token_index = self._token_index

        while True:
            if token_index >= self._tokens_count:
                return None

            current_token_name, token_info = self._tokens[token_index]

            if current_token_name == self.WHITESPACE_TOKEN_NAME:
                token_index += 1

                continue

            break

        if current_token_name in token_names:
            return current_token_name

        if is_required:
            self._error(token_names=token_names)
        else:
            return None

    def _scan_token(self, token_name, new_ctx=False):
        while True:
            if self._token_index >= self._tokens_count:
                self._error(token_names=[token_name])

            current_token_name, token_info = self._tokens[
                self._token_index
            ]

            if current_token_name == self.WHITESPACE_TOKEN_NAME:
                self._token_index += 1

                self._update_pos_row_col(token_info)

                continue

            break

        if current_token_name != token_name:
            self._error(token_names=[token_name])

        self._token_index += 1

        self._update_pos_row_col(token_info)

        if new_ctx:
            ctx = AttrDict()

            ctx.name = ''

            ctx.par = self._ctx
        else:
            ctx = self._ctx

        ctx.res = token_info

        return ctx

    def _scan_rule(self, name):
        ctx_par = self._ctx

        self._scan_lv += 1

        ctx_new = AttrDict()

        ctx_new.name = name

        ctx_new.par = ctx_par

        self._ctx = ctx_new

        rule_func = self._rule_func_get(name)

        self._scan_ei = None

        if self._debug:
            debug_info = AttrDict()
            debug_info[self._DK_NAME] = name
            debug_info[self._DK_TXT] = self._txt
            debug_info[self._DK_POS] = self._pos
            debug_info[self._DK_ROW] = self._row
            debug_info[self._DK_COL] = self._col
            debug_info[self._DK_SLV] = self._scan_lv
            debug_info[self._DK_SSS] = False

            self._debug_infos.append(debug_info)

        try:
            rule_func(ctx_new)
        except SyntaxError:
            exc_info = sys.exc_info()

            if self._scan_ei is None or self._scan_ei[1] is not exc_info[1]:
                self._scan_ei = exc_info

                self._scan_eis.append(exc_info)

            raise
        else:
            if self._debug:
                debug_info[self._DK_SSS] = True
        finally:
            self._scan_lv -= 1

            self._ctx = ctx_par

        return ctx_new

    def _rule_func_get(self, name):
        rule_func_name = self._RULE_FUNC_PRF + name + self._RULE_FUNC_POF

        rule_func = getattr(self, rule_func_name)

        return rule_func

    def _error(self, msg=None, token_names=None):
        token_index = self._get_token_index(skip_whitespace=True)

        if token_index is None:
            token_name = None
        else:
            token_name, info = self._tokens[token_index]

            self._pos = info.pos
            self._row = info.row
            self._col = info.col

        raise SyntaxError(
            ctx=self._ctx,
            txt=self._txt,
            pos=self._pos,
            row=self._row,
            col=self._col,
            token_name=token_name,
            token_names=token_names,
            eis=self._scan_eis,
            eisp=self._scan_eis_prev,
            msg=msg,
        )

    def source_code(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Module(
            stmts.res,
            type_ignores=[],
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```
        end = self._scan_rule('end')  # noqa

    def end(self, ctx):
        end = self._scan_token('end')  # noqa

    def comma_hz(self, ctx):
        comma_hz = self._scan_token('comma_hz')  # noqa

    def pause_hz(self, ctx):
        pause_hz = self._scan_token('pause_hz')  # noqa

    def colon_hz(self, ctx):
        colon_hz = self._scan_token('colon_hz')  # noqa

    def semicolon_hz(self, ctx):
        semicolon_hz = self._scan_token('semicolon_hz')  # noqa

    def period_hz(self, ctx):
        period_hz = self._scan_token('period_hz')  # noqa

    def question_mark_hz(self, ctx):
        question_mark_hz = self._scan_token('question_mark_hz')  # noqa

    def left_parenthesis_hz(self, ctx):
        left_parenthesis_hz = self._scan_token('left_parenthesis_hz')  # noqa

    def right_parenthesis_hz(self, ctx):
        right_parenthesis_hz = self._scan_token('right_parenthesis_hz')  # noqa

    def none_kw(self, ctx):
        none_kw = self._scan_token('none_kw')  # noqa

    def bool_true_kw(self, ctx):
        bool_true_kw = self._scan_token('bool_true_kw')  # noqa

    def bool_false_kw(self, ctx):
        bool_false_kw = self._scan_token('bool_false_kw')  # noqa

    def list_kw(self, ctx):
        list_kw = self._scan_token('list_kw')  # noqa

    def list_with_kw(self, ctx):
        list_with_kw = self._scan_token('list_with_kw')  # noqa

    def tuple_kw(self, ctx):
        tuple_kw = self._scan_token('tuple_kw')  # noqa

    def tuple_with_kw(self, ctx):
        tuple_with_kw = self._scan_token('tuple_with_kw')  # noqa

    def dict_kw(self, ctx):
        dict_kw = self._scan_token('dict_kw')  # noqa

    def dict_with_kw(self, ctx):
        dict_with_kw = self._scan_token('dict_with_kw')  # noqa

    def set_kw(self, ctx):
        set_kw = self._scan_token('set_kw')  # noqa

    def set_with_kw(self, ctx):
        set_with_kw = self._scan_token('set_with_kw')  # noqa

    def assign_op(self, ctx):
        assign_op = self._scan_token('assign_op')  # noqa

    def global_kw(self, ctx):
        global_kw = self._scan_token('global_kw')  # noqa

    def nonlocal_kw(self, ctx):
        nonlocal_kw = self._scan_token('nonlocal_kw')  # noqa

    def not_op(self, ctx):
        not_op = self._scan_token('not_op')  # noqa

    def or_op(self, ctx):
        or_op = self._scan_token('or_op')  # noqa

    def and_op(self, ctx):
        and_op = self._scan_token('and_op')  # noqa

    def is_op(self, ctx):
        is_op = self._scan_token('is_op')  # noqa

    def isnot_op(self, ctx):
        isnot_op = self._scan_token('isnot_op')  # noqa

    def equal_op(self, ctx):
        equal_op = self._scan_token('equal_op')  # noqa

    def not_equal_op(self, ctx):
        not_equal_op = self._scan_token('not_equal_op')  # noqa

    def lt_op(self, ctx):
        lt_op = self._scan_token('lt_op')  # noqa

    def le_op(self, ctx):
        le_op = self._scan_token('le_op')  # noqa

    def gt_op(self, ctx):
        gt_op = self._scan_token('gt_op')  # noqa

    def ge_op(self, ctx):
        ge_op = self._scan_token('ge_op')  # noqa

    def in_op(self, ctx):
        in_op = self._scan_token('in_op')  # noqa

    def not_in_op(self, ctx):
        not_in_op = self._scan_token('not_in_op')  # noqa

    def arrow_op(self, ctx):
        arrow_op = self._scan_token('arrow_op')  # noqa

    def bit_and_op(self, ctx):
        bit_and_op = self._scan_token('bit_and_op')  # noqa

    def bit_and_assign_op(self, ctx):
        bit_and_assign_op = self._scan_token('bit_and_assign_op')  # noqa

    def bit_or_op(self, ctx):
        bit_or_op = self._scan_token('bit_or_op')  # noqa

    def bit_or_assign_op(self, ctx):
        bit_or_assign_op = self._scan_token('bit_or_assign_op')  # noqa

    def bit_xor_op(self, ctx):
        bit_xor_op = self._scan_token('bit_xor_op')  # noqa

    def bit_xor_assign_op(self, ctx):
        bit_xor_assign_op = self._scan_token('bit_xor_assign_op')  # noqa

    def bit_left_shift_op(self, ctx):
        bit_left_shift_op = self._scan_token('bit_left_shift_op')  # noqa

    def bit_left_shift_assign_op(self, ctx):
        bit_left_shift_assign_op = self._scan_token('bit_left_shift_assign_op')  # noqa

    def bit_right_shift_op(self, ctx):
        bit_right_shift_op = self._scan_token('bit_right_shift_op')  # noqa

    def bit_right_shift_assign_op(self, ctx):
        bit_right_shift_assign_op = self._scan_token('bit_right_shift_assign_op')  # noqa

    def bit_invert_op(self, ctx):
        bit_invert_op = self._scan_token('bit_invert_op')  # noqa

    def bit_invert_assign_op(self, ctx):
        bit_invert_assign_op = self._scan_token('bit_invert_assign_op')  # noqa

    def increment_op(self, ctx):
        increment_op = self._scan_token('increment_op')  # noqa

    def decrement_op(self, ctx):
        decrement_op = self._scan_token('decrement_op')  # noqa

    def add_op(self, ctx):
        add_op = self._scan_token('add_op')  # noqa

    def add_assign_op(self, ctx):
        add_assign_op = self._scan_token('add_assign_op')  # noqa

    def subtract_op(self, ctx):
        subtract_op = self._scan_token('subtract_op')  # noqa

    def subtract_assign_op(self, ctx):
        subtract_assign_op = self._scan_token('subtract_assign_op')  # noqa

    def multiply_op(self, ctx):
        multiply_op = self._scan_token('multiply_op')  # noqa

    def multiply_assign_op(self, ctx):
        multiply_assign_op = self._scan_token('multiply_assign_op')  # noqa

    def divide_op(self, ctx):
        divide_op = self._scan_token('divide_op')  # noqa

    def divide_assign_op(self, ctx):
        divide_assign_op = self._scan_token('divide_assign_op')  # noqa

    def floor_divide_op(self, ctx):
        floor_divide_op = self._scan_token('floor_divide_op')  # noqa

    def floor_divide_assign_op(self, ctx):
        floor_divide_assign_op = self._scan_token('floor_divide_assign_op')  # noqa

    def modulo_op(self, ctx):
        modulo_op = self._scan_token('modulo_op')  # noqa

    def modulo_assign_op(self, ctx):
        modulo_assign_op = self._scan_token('modulo_assign_op')  # noqa

    def power_op(self, ctx):
        power_op = self._scan_token('power_op')  # noqa

    def power_assign_op(self, ctx):
        power_assign_op = self._scan_token('power_assign_op')  # noqa

    def unary_subtract_op(self, ctx):
        unary_subtract_op = self._scan_token('unary_subtract_op')  # noqa

    def dot_kw(self, ctx):
        dot_kw = self._scan_token('dot_kw')  # noqa

    def subscript_start_kw(self, ctx):
        subscript_start_kw = self._scan_token('subscript_start_kw')  # noqa

    def subscript_end_kw(self, ctx):
        subscript_end_kw = self._scan_token('subscript_end_kw')  # noqa

    def comp_item_as_name_kw(self, ctx):
        comp_item_as_name_kw = self._scan_token('comp_item_as_name_kw')  # noqa

    def async_comp_item_as_name_kw(self, ctx):
        async_comp_item_as_name_kw = self._scan_token('async_comp_item_as_name_kw')  # noqa

    def comp_if_kw(self, ctx):
        comp_if_kw = self._scan_token('comp_if_kw')  # noqa

    def comp_then_kw(self, ctx):
        comp_then_kw = self._scan_token('comp_then_kw')  # noqa

    def listcomp_generate_kw(self, ctx):
        listcomp_generate_kw = self._scan_token('listcomp_generate_kw')  # noqa

    def generator_generate_kw(self, ctx):
        generator_generate_kw = self._scan_token('generator_generate_kw')  # noqa

    def if_kw(self, ctx):
        if_kw = self._scan_token('if_kw')  # noqa

    def elif_kw(self, ctx):
        elif_kw = self._scan_token('elif_kw')  # noqa

    def else_kw(self, ctx):
        else_kw = self._scan_token('else_kw')  # noqa

    def block_start_kw(self, ctx):
        block_start_kw = self._scan_token('block_start_kw')  # noqa

    def block_end_kw(self, ctx):
        block_end_kw = self._scan_token('block_end_kw')  # noqa

    def loop_always_kw(self, ctx):
        loop_always_kw = self._scan_token('loop_always_kw')  # noqa

    def loop_if_kw(self, ctx):
        loop_if_kw = self._scan_token('loop_if_kw')  # noqa

    def loop_until_kw(self, ctx):
        loop_until_kw = self._scan_token('loop_until_kw')  # noqa

    def loop_iterator_kw(self, ctx):
        loop_iterator_kw = self._scan_token('loop_iterator_kw')  # noqa

    def async_loop_iterator_kw(self, ctx):
        async_loop_iterator_kw = self._scan_token('async_loop_iterator_kw')  # noqa

    def loop_iterator_item_as_name_kw(self, ctx):
        loop_iterator_item_as_name_kw = self._scan_token('loop_iterator_item_as_name_kw')  # noqa

    def continue_kw(self, ctx):
        continue_kw = self._scan_token('continue_kw')  # noqa

    def break_kw(self, ctx):
        break_kw = self._scan_token('break_kw')  # noqa

    def try_kw(self, ctx):
        try_kw = self._scan_token('try_kw')  # noqa

    def except_kw(self, ctx):
        except_kw = self._scan_token('except_kw')  # noqa

    def finally_kw(self, ctx):
        finally_kw = self._scan_token('finally_kw')  # noqa

    def raise_kw(self, ctx):
        raise_kw = self._scan_token('raise_kw')  # noqa

    def raise_from_kw(self, ctx):
        raise_from_kw = self._scan_token('raise_from_kw')  # noqa

    def with_kw(self, ctx):
        with_kw = self._scan_token('with_kw')  # noqa

    def async_with_kw(self, ctx):
        async_with_kw = self._scan_token('async_with_kw')  # noqa

    def yield_kw(self, ctx):
        yield_kw = self._scan_token('yield_kw')  # noqa

    def yield_from_kw(self, ctx):
        yield_from_kw = self._scan_token('yield_from_kw')  # noqa

    def await_kw(self, ctx):
        await_kw = self._scan_token('await_kw')  # noqa

    def func_start_kw(self, ctx):
        func_start_kw = self._scan_token('func_start_kw')  # noqa

    def async_func_start_kw(self, ctx):
        async_func_start_kw = self._scan_token('async_func_start_kw')  # noqa

    def func_end_kw(self, ctx):
        func_end_kw = self._scan_token('func_end_kw')  # noqa

    def collect_args_kw(self, ctx):
        collect_args_kw = self._scan_token('collect_args_kw')  # noqa

    def collect_kwargs_kw(self, ctx):
        collect_kwargs_kw = self._scan_token('collect_kwargs_kw')  # noqa

    def expand_args_kw(self, ctx):
        expand_args_kw = self._scan_token('expand_args_kw')  # noqa

    def expand_kwargs_kw(self, ctx):
        expand_kwargs_kw = self._scan_token('expand_kwargs_kw')  # noqa

    def class_start_kw(self, ctx):
        class_start_kw = self._scan_token('class_start_kw')  # noqa

    def class_end_kw(self, ctx):
        class_end_kw = self._scan_token('class_end_kw')  # noqa

    def decorate_kw(self, ctx):
        decorate_kw = self._scan_token('decorate_kw')  # noqa

    def pass_kw(self, ctx):
        pass_kw = self._scan_token('pass_kw')  # noqa

    def del_kw(self, ctx):
        del_kw = self._scan_token('del_kw')  # noqa

    def return_kw(self, ctx):
        return_kw = self._scan_token('return_kw')  # noqa

    def assert_kw(self, ctx):
        assert_kw = self._scan_token('assert_kw')  # noqa

    def print_kw(self, ctx):
        print_kw = self._scan_token('print_kw')  # noqa

    def exit_kw(self, ctx):
        exit_kw = self._scan_token('exit_kw')  # noqa

    def import_kw(self, ctx):
        import_kw = self._scan_token('import_kw')  # noqa

    def from_import_kw(self, ctx):
        from_import_kw = self._scan_token('from_import_kw')  # noqa

    def as_kw(self, ctx):
        as_kw = self._scan_token('as_kw')  # noqa

    def trailer_prefix(self, ctx):
        trailer_prefix = self._scan_token('trailer_prefix')  # noqa

    def type_trailer(self, ctx):
        type_trailer = self._scan_token('type_trailer')  # noqa

    def bool_trailer(self, ctx):
        bool_trailer = self._scan_token('bool_trailer')  # noqa

    def int_trailer(self, ctx):
        int_trailer = self._scan_token('int_trailer')  # noqa

    def float_trailer(self, ctx):
        float_trailer = self._scan_token('float_trailer')  # noqa

    def str_trailer(self, ctx):
        str_trailer = self._scan_token('str_trailer')  # noqa

    def repr_trailer(self, ctx):
        repr_trailer = self._scan_token('repr_trailer')  # noqa

    def bytes_trailer(self, ctx):
        bytes_trailer = self._scan_token('bytes_trailer')  # noqa

    def bytearray_trailer(self, ctx):
        bytearray_trailer = self._scan_token('bytearray_trailer')  # noqa

    def chr_trailer(self, ctx):
        chr_trailer = self._scan_token('chr_trailer')  # noqa

    def ord_trailer(self, ctx):
        ord_trailer = self._scan_token('ord_trailer')  # noqa

    def hex_trailer(self, ctx):
        hex_trailer = self._scan_token('hex_trailer')  # noqa

    def oct_trailer(self, ctx):
        oct_trailer = self._scan_token('oct_trailer')  # noqa

    def bin_trailer(self, ctx):
        bin_trailer = self._scan_token('bin_trailer')  # noqa

    def list_trailer(self, ctx):
        list_trailer = self._scan_token('list_trailer')  # noqa

    def tuple_trailer(self, ctx):
        tuple_trailer = self._scan_token('tuple_trailer')  # noqa

    def dict_trailer(self, ctx):
        dict_trailer = self._scan_token('dict_trailer')  # noqa

    def set_trailer(self, ctx):
        set_trailer = self._scan_token('set_trailer')  # noqa

    def len_trailer(self, ctx):
        len_trailer = self._scan_token('len_trailer')  # noqa

    def count_trailer(self, ctx):
        count_trailer = self._scan_token('count_trailer')  # noqa

    def abs_trailer(self, ctx):
        abs_trailer = self._scan_token('abs_trailer')  # noqa

    def min_trailer(self, ctx):
        min_trailer = self._scan_token('min_trailer')  # noqa

    def max_trailer(self, ctx):
        max_trailer = self._scan_token('max_trailer')  # noqa

    def opposite_trailer(self, ctx):
        opposite_trailer = self._scan_token('opposite_trailer')  # noqa

    def reciprocal_trailer(self, ctx):
        reciprocal_trailer = self._scan_token('reciprocal_trailer')  # noqa

    def sum_trailer(self, ctx):
        sum_trailer = self._scan_token('sum_trailer')  # noqa

    def any_trailer(self, ctx):
        any_trailer = self._scan_token('any_trailer')  # noqa

    def all_trailer(self, ctx):
        all_trailer = self._scan_token('all_trailer')  # noqa

    def range_trailer(self, ctx):
        range_trailer = self._scan_token('range_trailer')  # noqa

    def name_trailer(self, ctx):
        name_trailer = self._scan_token('name_trailer')  # noqa

    def format_trailer(self, ctx):
        format_trailer = self._scan_token('format_trailer')  # noqa

    def add_trailer(self, ctx):
        add_trailer = self._scan_token('add_trailer')  # noqa

    def append_trailer(self, ctx):
        append_trailer = self._scan_token('append_trailer')  # noqa

    def extend_trailer(self, ctx):
        extend_trailer = self._scan_token('extend_trailer')  # noqa

    def clear_trailer(self, ctx):
        clear_trailer = self._scan_token('clear_trailer')  # noqa

    def sort_trailer(self, ctx):
        sort_trailer = self._scan_token('sort_trailer')  # noqa

    def none(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        none_kw = self._scan_rule('none_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = NameConstant(
            None,
            kind=None,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        ctx.res.token_index = token_index
        # ```

    def boolean(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['bool_true_kw']):
            bool_true_kw = self._scan_rule('bool_true_kw')  # noqa
            # ```
            value = True
            # ```
        elif self._peek(['bool_false_kw'], is_branch=True):
            bool_false_kw = self._scan_rule('bool_false_kw')  # noqa
            # ```
            value = False
            # ```
        else:
            self._error(token_names=[
            'bool_false_kw',
            'bool_true_kw'])
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = NameConstant(
            value,
            kind=None,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        ctx.res.token_index = token_index
        # ```

    def number(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        number = self._scan_token('number')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()

        if number.res.txt[0] in HANZI_DIGITS_AND_UNITS:
            value = hanzi_digits_to_value(number.res.txt)
        else:
            number_text = number.res.txt.replace('_', '')

            value = eval(number_text)

        ctx.res = Num(
            value,
            kind=None,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        ctx.res.token_index = token_index
        # ```

    def string(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        string = self._scan_token('string')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Str(
            string.res.value,
            kind=None,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        ctx.res.token_index = token_index
        # ```

    def name(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        name = self._scan_token('name')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Name(
            id=name.res.txt,
            ctx=Load(),
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        ctx.res.token_index = token_index
        # ```

    def stmts(self, ctx):
        # ```
        stmts = []
        # ```
        while self._peek([
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'finally_kw',
            'else_kw',
            'func_end_kw',
            'end'],
            is_required=True) in [
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz']:
            stmt = self._scan_rule('stmt')  # noqa
            # ```
            stmts.append(stmt.res)
            # ```
            if self._peek([
                'period_hz',
                'semicolon_hz',
                'number',
                'string',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'pass_kw',
                'bit_invert_op',
                'break_kw',
                'tuple_with_kw',
                'elif_kw',
                'class_end_kw',
                'block_end_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'finally_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'func_end_kw',
                'async_func_start_kw',
                'del_kw',
                'bool_false_kw',
                'tuple_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'return_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'end',
                'unary_subtract_op',
                'left_parenthesis_hz'],
                is_required=True) in [
                'period_hz',
                'semicolon_hz']:
                if self._peek(['semicolon_hz']):
                    semicolon_hz = self._scan_rule('semicolon_hz')  # noqa
                elif self._peek(['period_hz'], is_branch=True):
                    period_hz = self._scan_rule('period_hz')  # noqa
                else:
                    self._error(token_names=[
                    'period_hz',
                    'semicolon_hz'])
        # ```
        ctx.res = stmts
        # ```

    def stmt(self, ctx):
        if self._peek([
            'number',
            'string',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'continue_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'set_with_kw',
            'yield_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'exit_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz']):
            simple_stmt = self._scan_rule('simple_stmt')  # noqa
            # ```
            ctx.res = simple_stmt.res
            # ```
        elif self._peek([
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'loop_iterator_kw',
            'with_kw',
            'loop_always_kw',
            'try_kw',
            'async_func_start_kw',
            'class_start_kw',
            'if_kw',
            'func_start_kw'], is_branch=True):
            compound_stmt = self._scan_rule('compound_stmt')  # noqa
            # ```
            ctx.res = compound_stmt.res
            # ```
        else:
            self._error(token_names=[
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'])

    def simple_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['pass_kw']):
            pass_stmt = self._scan_rule('pass_stmt')  # noqa
            # ```
            node = pass_stmt.res
            # ```
        elif self._peek(['del_kw'], is_branch=True):
            del_stmt = self._scan_rule('del_stmt')  # noqa
            # ```
            node = del_stmt.res
            # ```
        elif self._peek(['continue_kw'], is_branch=True):
            continue_stmt = self._scan_rule('continue_stmt')  # noqa
            # ```
            node = continue_stmt.res
            # ```
        elif self._peek(['break_kw'], is_branch=True):
            break_stmt = self._scan_rule('break_stmt')  # noqa
            # ```
            node = break_stmt.res
            # ```
        elif self._peek(['return_kw'], is_branch=True):
            return_stmt = self._scan_rule('return_stmt')  # noqa
            # ```
            node = return_stmt.res
            # ```
        elif self._peek(['raise_kw'], is_branch=True):
            raise_stmt = self._scan_rule('raise_stmt')  # noqa
            # ```
            node = raise_stmt.res
            # ```
        elif self._peek(['assert_kw'], is_branch=True):
            assert_stmt = self._scan_rule('assert_stmt')  # noqa
            # ```
            node = assert_stmt.res
            # ```
        elif self._peek(['exit_kw'], is_branch=True):
            exit_stmt = self._scan_rule('exit_stmt')  # noqa
            # ```
            node = exit_stmt.res
            # ```
        elif self._peek([
            'await_kw',
            'print_kw'], is_branch=True):
            print_stmt = self._scan_rule('print_stmt')  # noqa
            # ```
            node = print_stmt.res
            # ```
        elif self._peek([
            'yield_from_kw',
            'yield_kw'], is_branch=True):
            yield_expr = self._scan_rule('yield_expr')  # noqa
            # ```
            node = yield_expr.res
            # ```
        elif self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'], is_branch=True):
            expr_or_assign_stmt = self._scan_rule('expr_or_assign_stmt')  # noqa
            # ```
            node = expr_or_assign_stmt.res
            # ```
        else:
            self._error(token_names=[
            'number',
            'string',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'continue_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'set_with_kw',
            'yield_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'exit_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'])
        # ```
        if isinstance(node, ExprBase)\
        and node.__class__ is not Expr:
            end_row, end_col = self._get_end_row_col()

            node = Expr(
                node,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res = node
        # ```

    def pass_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        pass_kw = self._scan_rule('pass_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Pass(
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def del_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        del_kw = self._scan_rule('del_kw')  # noqa
        name = self._scan_rule('name')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        name_node = name.res
        name_node.ctx = Del()
        ctx.res = Delete(
            targets=[name_node],
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def continue_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        continue_kw = self._scan_rule('continue_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Continue(
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def break_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        break_kw = self._scan_rule('break_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Break(
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def return_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        return_kw = self._scan_rule('return_kw')  # noqa
        # ```
        value = None
        # ```
        if self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'pass_kw',
            'break_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'finally_kw',
            'with_kw',
            'assert_kw',
            'await_kw',
            'loop_always_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'print_kw',
            'raise_kw',
            'return_kw',
            'func_start_kw',
            'end',
            'period_hz',
            'semicolon_hz'],
            is_required=True) in [
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz']:
            expr = self._scan_rule('expr')  # noqa
            # ```
            value = expr.res
            # ```
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Return(
            value=value,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def raise_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        raise_kw = self._scan_rule('raise_kw')  # noqa
        # ```
        exc_expr = None
        cause_expr = None
        # ```
        if self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'pass_kw',
            'break_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'finally_kw',
            'with_kw',
            'assert_kw',
            'await_kw',
            'loop_always_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'print_kw',
            'raise_kw',
            'return_kw',
            'func_start_kw',
            'end',
            'period_hz',
            'semicolon_hz'],
            is_required=True) in [
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz']:
            expr = self._scan_rule('expr')  # noqa
            # ```
            exc_expr = expr.res
            # ```
            if self._peek([
                'raise_from_kw',
                'number',
                'string',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'pass_kw',
                'bit_invert_op',
                'break_kw',
                'tuple_with_kw',
                'elif_kw',
                'class_end_kw',
                'block_end_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'finally_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'func_end_kw',
                'async_func_start_kw',
                'del_kw',
                'bool_false_kw',
                'tuple_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'return_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'end',
                'period_hz',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'semicolon_hz'],
                is_required=True) == 'raise_from_kw':
                raise_from_kw = self._scan_rule('raise_from_kw')  # noqa
                expr = self._scan_rule('expr')  # noqa
                # ```
                cause_expr = expr.res
                # ```
        # ```
        end_row, end_col = self._get_end_row_col()

        ctx.res = Raise(
            exc=exc_expr,
            cause=cause_expr,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def assert_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        assert_kw = self._scan_rule('assert_kw')  # noqa
        expr = self._scan_rule('expr')  # noqa
        # ```
        test_expr = expr.res
        msg_expr = None
        # ```
        if self._peek([
            'comma_hz',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'finally_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'end',
            'period_hz',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'semicolon_hz'],
            is_required=True) == 'comma_hz':
            comma_hz = self._scan_rule('comma_hz')  # noqa
            expr = self._scan_rule('expr')  # noqa
            # ```
            msg_expr = expr.res
            # ```
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = Assert(
            test=test_expr,
            msg=msg_expr,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def exit_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        exit_kw = self._scan_rule('exit_kw')  # noqa
        # ```
        kw_end_row, kw_end_col = self._get_end_row_col()
        expr_node = None
        # ```
        if self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'pass_kw',
            'break_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'finally_kw',
            'with_kw',
            'assert_kw',
            'await_kw',
            'loop_always_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'print_kw',
            'raise_kw',
            'return_kw',
            'func_start_kw',
            'end',
            'period_hz',
            'semicolon_hz'],
            is_required=True) in [
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz']:
            expr = self._scan_rule('expr')  # noqa
            # ```
            expr_node = expr.res
            # ```
        # ```
        end_row, end_col = self._get_end_row_col()

        if expr_node is None:
            expr_node = NameConstant(
                value=None,
                kind=None,
                lineno=end_row,
                col_offset=end_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res = Expr(
            value=Call(
                func=Name(
                    id='exit',
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=kw_end_row,
                    end_col_offset=kw_end_col,
                ),
                args=[expr_node],
                keywords=[],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            ),
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def print_stmt(self, ctx):
        if self._peek(['print_kw']):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            print_kw = self._scan_rule('print_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            func_name_node = Name(
                id='print',
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Expr(
                value=Call(
                    func=func_name_node,
                    args=args_list.res.args,
                    keywords=args_list.res.kwargs,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                ),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['await_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            await_kw = self._scan_rule('await_kw')  # noqa
            expr = self._scan_rule('expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Await(expr.res)
            # ```
        else:
            self._error(token_names=[
            'await_kw',
            'print_kw'])

    def args_list(self, ctx):
        # ```
        # Used in child `args_list_item`.
        ctx.res = AttrDict()
        ctx.res.args = []
        ctx.res.kwargs = []
        ctx.res.expand_args_node = None
        ctx.res.expand_kwargs_node = None
        # ```
        left_parenthesis_hz = self._scan_rule('left_parenthesis_hz')  # noqa
        if self._peek(['right_parenthesis_hz']):
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
        elif self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'expand_kwargs_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'expand_args_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'], is_branch=True):
            args_list_item = self._scan_rule('args_list_item')  # noqa
        else:
            self._error(token_names=[
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'expand_kwargs_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'expand_args_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'right_parenthesis_hz'])

    def args_list_item(self, ctx):
        # ```
        # Used in child `args_list_item`.
        ctx.res = ctx.par.res
        expand_mode = None
        start_row, start_col =\
            self._get_start_row_col()
        # ```
        if self._peek([
            'expand_kwargs_kw',
            'expand_args_kw',
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) in [
            'expand_kwargs_kw',
            'expand_args_kw']:
            if self._peek(['expand_args_kw']):
                expand_args_kw = self._scan_rule('expand_args_kw')  # noqa
                # ```
                if ctx.res.expand_args_node is not None:
                    self._retract()
                    self._error(msg='`展开`不能用第二次。')

                if ctx.res.expand_kwargs_node is not None:
                    self._retract()
                    self._error(msg='`展开`不能在`展开来`之后。')

                expand_mode = 1
                # ```
            elif self._peek(['expand_kwargs_kw'], is_branch=True):
                expand_kwargs_kw = self._scan_rule('expand_kwargs_kw')  # noqa
                # ```
                if ctx.res.expand_kwargs_node is not None:
                    self._retract()
                    self._error(msg='`展开来`不能用第二次。')

                expand_mode = 2
                # ```
            else:
                self._error(token_names=[
                'expand_kwargs_kw',
                'expand_args_kw'])
        # ```
        lhs_expr_token_index = self._get_token_index()
        # ```
        cond_expr = self._scan_rule('cond_expr')  # noqa
        # ```
        lhs_expr = cond_expr.res
        rhs_expr = None
        # ```
        if self._peek([
            'assign_op',
            'right_parenthesis_hz',
            'comma_hz'],
            is_required=True) == 'assign_op':
            assign_op = self._scan_rule('assign_op')  # noqa
            # ```
            if expand_mode == 1:
                self._retract()
                self._error(msg='`展开`参数不能有默认值。')
            elif expand_mode == 2:
                self._retract()
                self._error(msg='`展开来`参数不能有默认值。')
            elif not isinstance(lhs_expr, Name):
                self._retract(lhs_expr_token_index)
                self._error(msg='不是合格的参数名。')
            # ```
            cond_expr = self._scan_rule('cond_expr')  # noqa
            # ```
            rhs_expr = cond_expr.res
            # ```
        # ```
        end_row, end_col = self._get_end_row_col()
        if expand_mode == 1:
            node = Starred(
                value=cond_expr.res,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.res.expand_args_node = node
            ctx.res.args.append(node)
        elif expand_mode == 2:
            node = keyword(
                arg=None,
                value=cond_expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.res.expand_kwargs_node = node
            ctx.res.kwargs.append(node)
        elif rhs_expr is not None:
            node = keyword(
                arg=lhs_expr.id,
                value=rhs_expr,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.res.kwargs.append(node)
        else:
            if ctx.res.kwargs:
                self._retract(lhs_expr_token_index)
                self._error(msg='排位参数不能出现在关键字参数之后。')
            node = cond_expr.res
            ctx.res.args.append(node)
        # ```
        if self._peek(['right_parenthesis_hz']):
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
        elif self._peek(['comma_hz'], is_branch=True):
            comma_hz = self._scan_rule('comma_hz')  # noqa
            if self._peek(['right_parenthesis_hz']):
                right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
            elif self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'expand_kwargs_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'expand_args_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'], is_branch=True):
                args_list_item = self._scan_rule('args_list_item')  # noqa
            else:
                self._error(token_names=[
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'expand_kwargs_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'expand_args_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'right_parenthesis_hz'])
        else:
            self._error(token_names=[
            'right_parenthesis_hz',
            'comma_hz'])

    def yield_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['yield_kw']):
            yield_kw = self._scan_rule('yield_kw')  # noqa
            # ```
            expr_node = None
            # ```
            if self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'pass_kw',
                'break_kw',
                'elif_kw',
                'class_end_kw',
                'block_end_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'finally_kw',
                'with_kw',
                'assert_kw',
                'await_kw',
                'loop_always_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'func_end_kw',
                'async_func_start_kw',
                'del_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'print_kw',
                'raise_kw',
                'return_kw',
                'func_start_kw',
                'end',
                'period_hz',
                'right_parenthesis_hz',
                'semicolon_hz'],
                is_required=True) in [
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz']:
                expr = self._scan_rule('expr')  # noqa
                # ```
                expr_node = expr.res
                # ```
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Yield(
                expr_node,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['yield_from_kw'], is_branch=True):
            yield_from_kw = self._scan_rule('yield_from_kw')  # noqa
            expr = self._scan_rule('expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = YieldFrom(
                expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        else:
            self._error(token_names=[
            'yield_from_kw',
            'yield_kw'])
        # ```
        ctx.res.token_index = token_index
        # ```

    def expr_or_assign_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        expr = self._scan_rule('expr')  # noqa
        # ```
        res_node = expr.res
        # ```
        if self._peek([
            'from_import_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'decrement_op',
            'increment_op',
            'bit_and_assign_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'floor_divide_assign_op',
            'multiply_assign_op',
            'subtract_assign_op',
            'add_assign_op',
            'divide_assign_op',
            'assign_op',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'finally_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'end',
            'period_hz',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'semicolon_hz'],
            is_required=True) in [
            'from_import_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'decrement_op',
            'increment_op',
            'bit_and_assign_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'floor_divide_assign_op',
            'multiply_assign_op',
            'subtract_assign_op',
            'add_assign_op',
            'divide_assign_op',
            'assign_op']:
            if self._peek(['assign_op']):
                assign_op = self._scan_rule('assign_op')  # noqa
                expr = self._scan_rule('expr')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                self._set_store_ctx(res_node)
                res_node = Assign(
                    targets=[res_node],
                    value=expr.res,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek([
                'decrement_op',
                'increment_op'], is_branch=True):
                if self._peek(['increment_op']):
                    increment_op = self._scan_rule('increment_op')  # noqa
                    # ```
                    add_value = 1
                    # ```
                elif self._peek(['decrement_op'], is_branch=True):
                    decrement_op = self._scan_rule('decrement_op')  # noqa
                    # ```
                    add_value = -1
                    # ```
                else:
                    self._error(token_names=[
                    'decrement_op',
                    'increment_op'])
                # ```
                end_row, end_col = self._get_end_row_col()
                self._set_store_ctx(res_node)
                res_node = AugAssign(
                    target=res_node,
                    op=Add(),
                    value=Num(
                        add_value,
                        kind=None,
                        lineno=start_row,
                        col_offset=start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    ),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek([
                'from_import_kw',
                'import_kw'], is_branch=True):
                if self._peek(['import_kw']):
                    import_kw = self._scan_rule('import_kw')  # noqa
                    # ```
                    is_from_import = False
                    # ```
                elif self._peek(['from_import_kw'], is_branch=True):
                    # ```
                    from_import_token_index = self._get_token_index()
                    # ```
                    from_import_kw = self._scan_rule('from_import_kw')  # noqa
                    # ```
                    is_from_import = True
                    # ```
                else:
                    self._error(token_names=[
                    'from_import_kw',
                    'import_kw'])
                # ```
                end_row, end_col = self._get_end_row_col()

                if isinstance(res_node, Name):
                    module_name = res_node.id
                elif isinstance(res_node, Attribute):
                    stack = []

                    attr_node = res_node

                    while isinstance(attr_node, Attribute):
                        name_part = attr_node.attr
                        stack.append(name_part)
                        attr_node = attr_node.value

                    token_index = getattr(attr_node, 'token_index', None)

                    if not isinstance(attr_node, Name):
                        if token_index is not None:
                            self._retract(token_index)

                        self._error(msg='不是合规的模块名。')

                    module_name = attr_node.id

                    if ' ' in module_name\
                    or ' ' in module_name\
                    or '　' in module_name:
                        if token_index is not None:
                            self._retract(token_index)

                        self._error(msg='模块名不能含有空格。')

                    module_name = module_name.replace('屋头', '.')

                    while stack:
                        name_part = stack.pop()
                        if name_part == '屋头':
                            module_name += '.'
                        elif module_name.endswith('.'):
                            module_name += name_part
                        else:
                            module_name += '.' + name_part
                else:
                    token_index = getattr(res_node, 'token_index', None)

                    if token_index is not None:
                        self._retract(token_index)

                    self._error(msg='不是合规的模块名。')

                asname = None
                asname_start_row, asname_start_col = self._get_start_row_col()
                # ```
                if self._peek([
                    'as_kw',
                    'number',
                    'string',
                    'async_with_kw',
                    'async_loop_iterator_kw',
                    'loop_until_kw',
                    'loop_if_kw',
                    'yield_from_kw',
                    'name',
                    'pass_kw',
                    'bit_invert_op',
                    'break_kw',
                    'tuple_with_kw',
                    'elif_kw',
                    'class_end_kw',
                    'block_end_kw',
                    'except_kw',
                    'loop_iterator_kw',
                    'continue_kw',
                    'finally_kw',
                    'with_kw',
                    'dict_with_kw',
                    'assert_kw',
                    'await_kw',
                    'list_with_kw',
                    'loop_always_kw',
                    'set_with_kw',
                    'else_kw',
                    'yield_kw',
                    'try_kw',
                    'func_end_kw',
                    'async_func_start_kw',
                    'del_kw',
                    'bool_false_kw',
                    'tuple_kw',
                    'class_start_kw',
                    'exit_kw',
                    'if_kw',
                    'not_op',
                    'print_kw',
                    'raise_kw',
                    'return_kw',
                    'dict_kw',
                    'bool_true_kw',
                    'list_kw',
                    'none_kw',
                    'set_kw',
                    'func_start_kw',
                    'end',
                    'period_hz',
                    'unary_subtract_op',
                    'left_parenthesis_hz',
                    'semicolon_hz'],
                    is_required=True) == 'as_kw':
                    as_kw = self._scan_rule('as_kw')  # noqa
                    # ```
                    asname_start_row, asname_start_col = self._get_start_row_col()
                    # ```
                    name = self._scan_rule('name')  # noqa
                    # ```
                    asname_end_row, asname_end_col = self._get_end_row_col()
                    asname = name.res.id
                    # ```
                # ```
                if asname is None:
                    asname_end_row, asname_end_col = asname_start_row, asname_start_col

                if is_from_import:
                    last_dot_pos = module_name.rfind('.')

                    if last_dot_pos == -1:
                        self._retract(from_import_token_index)

                        self._error(msg='`出来给我扎起`的模块名缺少`咧`。')

                    last_part_name = module_name[last_dot_pos + 1:]

                    module_name = module_name[:last_dot_pos]

                    if not module_name or module_name.endswith('.'):
                        module_name += '.'

                    res_node = ImportFrom(
                        module=module_name,
                        names=[
                            alias(
                                name=last_part_name,
                                asname=asname,
                                lineno=asname_start_row,
                                col_offset=asname_start_col,
                                end_lineno=asname_end_row,
                                end_col_offset=asname_end_col,
                            )
                        ],
                        level=0,
                        lineno=start_row,
                        col_offset=start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    )
                else:
                    res_node = Import(
                        names=[
                            alias(
                                name=module_name,
                                asname=asname,
                                lineno=asname_start_row,
                                col_offset=asname_start_col,
                                end_lineno=asname_end_row,
                                end_col_offset=asname_end_col,
                            )
                        ],
                        lineno=start_row,
                        col_offset=start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    )
                # ```
            elif self._peek([
                'bit_invert_assign_op',
                'bit_right_shift_assign_op',
                'bit_left_shift_assign_op',
                'bit_xor_assign_op',
                'bit_and_assign_op',
                'bit_or_assign_op',
                'modulo_assign_op',
                'power_assign_op',
                'floor_divide_assign_op',
                'multiply_assign_op',
                'subtract_assign_op',
                'add_assign_op',
                'divide_assign_op'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                if self._peek(['add_assign_op']):
                    add_assign_op = self._scan_rule('add_assign_op')  # noqa
                    # ```
                    op_class = Add
                    # ```
                elif self._peek(['subtract_assign_op'], is_branch=True):
                    subtract_assign_op = self._scan_rule('subtract_assign_op')  # noqa
                    # ```
                    op_class = Sub
                    # ```
                elif self._peek(['multiply_assign_op'], is_branch=True):
                    multiply_assign_op = self._scan_rule('multiply_assign_op')  # noqa
                    # ```
                    op_class = Mult
                    # ```
                elif self._peek(['divide_assign_op'], is_branch=True):
                    divide_assign_op = self._scan_rule('divide_assign_op')  # noqa
                    # ```
                    op_class = Div
                    # ```
                elif self._peek(['floor_divide_assign_op'], is_branch=True):
                    floor_divide_assign_op = self._scan_rule('floor_divide_assign_op')  # noqa
                    # ```
                    op_class = FloorDiv
                    # ```
                elif self._peek(['modulo_assign_op'], is_branch=True):
                    modulo_assign_op = self._scan_rule('modulo_assign_op')  # noqa
                    # ```
                    op_class = Mod
                    # ```
                elif self._peek(['power_assign_op'], is_branch=True):
                    power_assign_op = self._scan_rule('power_assign_op')  # noqa
                    # ```
                    op_class = Pow
                    # ```
                elif self._peek(['bit_and_assign_op'], is_branch=True):
                    bit_and_assign_op = self._scan_rule('bit_and_assign_op')  # noqa
                    # ```
                    op_class = BitAnd
                    # ```
                elif self._peek(['bit_or_assign_op'], is_branch=True):
                    bit_or_assign_op = self._scan_rule('bit_or_assign_op')  # noqa
                    # ```
                    op_class = BitOr
                    # ```
                elif self._peek(['bit_xor_assign_op'], is_branch=True):
                    bit_xor_assign_op = self._scan_rule('bit_xor_assign_op')  # noqa
                    # ```
                    op_class = BitXor
                    # ```
                elif self._peek(['bit_invert_assign_op'], is_branch=True):
                    bit_invert_assign_op = self._scan_rule('bit_invert_assign_op')  # noqa
                    # ```
                    op_class = Invert
                    # ```
                elif self._peek(['bit_left_shift_assign_op'], is_branch=True):
                    bit_left_shift_assign_op = self._scan_rule('bit_left_shift_assign_op')  # noqa
                    # ```
                    op_class = LShift
                    # ```
                elif self._peek(['bit_right_shift_assign_op'], is_branch=True):
                    bit_right_shift_assign_op = self._scan_rule('bit_right_shift_assign_op')  # noqa
                    # ```
                    op_class = RShift
                    # ```
                else:
                    self._error(token_names=[
                    'bit_invert_assign_op',
                    'bit_right_shift_assign_op',
                    'bit_left_shift_assign_op',
                    'bit_xor_assign_op',
                    'bit_and_assign_op',
                    'bit_or_assign_op',
                    'modulo_assign_op',
                    'power_assign_op',
                    'floor_divide_assign_op',
                    'multiply_assign_op',
                    'subtract_assign_op',
                    'add_assign_op',
                    'divide_assign_op'])
                # ```
                op_end_row, op_end_col = self._get_end_row_col()
                # ```
                expr = self._scan_rule('expr')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                op_node = op_class(
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                )
                self._set_store_ctx(res_node)
                res_node = AugAssign(
                    target=res_node,
                    op=op_node,
                    value=expr.res,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            else:
                self._error(token_names=[
                'from_import_kw',
                'import_kw',
                'bit_invert_assign_op',
                'bit_right_shift_assign_op',
                'bit_left_shift_assign_op',
                'bit_xor_assign_op',
                'decrement_op',
                'increment_op',
                'bit_and_assign_op',
                'bit_or_assign_op',
                'modulo_assign_op',
                'power_assign_op',
                'floor_divide_assign_op',
                'multiply_assign_op',
                'subtract_assign_op',
                'add_assign_op',
                'divide_assign_op',
                'assign_op'])
        # ```
        ctx.res = res_node
        # ```

    def expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        cond_exprs_list = self._scan_rule('cond_exprs_list')  # noqa
        # ```
        nodes = cond_exprs_list.res.nodes
        if len(nodes) == 1 and not cond_exprs_list.res.has_comma:
            ctx.res = nodes[0]
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = Tuple(
                elts=nodes,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res.token_index = token_index
        # ```

    def cond_exprs_list(self, ctx):
        # ```
        # Used in child `cond_exprs_list_item`.
        ctx.res = AttrDict()
        ctx.res.nodes = []
        ctx.res.has_comma = False
        # ```
        cond_exprs_list_item = self._scan_rule('cond_exprs_list_item')  # noqa

    def cond_exprs_list_item(self, ctx):
        # ```
        # Used in child `cond_exprs_list_item`.
        ctx.res = ctx.par.res
        # ```
        cond_expr = self._scan_rule('cond_expr')  # noqa
        # ```
        ctx.res.nodes.append(cond_expr.res)
        # ```
        if self._peek([
            'comma_hz',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) == 'comma_hz':
            comma_hz = self._scan_rule('comma_hz')  # noqa
            # ```
            ctx.res.has_comma = True
            # ```
            if self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'from_import_kw',
                'async_comp_item_as_name_kw',
                'async_with_kw',
                'async_loop_iterator_kw',
                'import_kw',
                'bit_invert_assign_op',
                'bit_right_shift_assign_op',
                'bit_left_shift_assign_op',
                'bit_xor_assign_op',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'decrement_op',
                'increment_op',
                'generator_generate_kw',
                'pass_kw',
                'comp_item_as_name_kw',
                'bit_and_assign_op',
                'bit_or_assign_op',
                'modulo_assign_op',
                'power_assign_op',
                'break_kw',
                'elif_kw',
                'class_end_kw',
                'block_end_kw',
                'block_start_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'floor_divide_assign_op',
                'finally_kw',
                'loop_iterator_item_as_name_kw',
                'with_kw',
                'assert_kw',
                'await_kw',
                'loop_always_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'func_end_kw',
                'async_func_start_kw',
                'del_kw',
                'multiply_assign_op',
                'subtract_assign_op',
                'add_assign_op',
                'as_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'raise_from_kw',
                'print_kw',
                'raise_kw',
                'comp_then_kw',
                'return_kw',
                'listcomp_generate_kw',
                'func_start_kw',
                'divide_assign_op',
                'end',
                'pause_hz',
                'period_hz',
                'assign_op',
                'subscript_end_kw',
                'right_parenthesis_hz',
                'comma_hz',
                'colon_hz',
                'semicolon_hz',
                'question_mark_hz'],
                is_required=True) in [
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz']:
                cond_exprs_list_item = self._scan_rule('cond_exprs_list_item')  # noqa

    def expr_no_comp(self, ctx):
        # ```
        nodes = []
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        cond_exprs_no_comp_list = self._scan_rule('cond_exprs_no_comp_list')  # noqa
        # ```
        nodes = cond_exprs_no_comp_list.res.nodes
        if len(nodes) == 1 and not cond_exprs_no_comp_list.res.has_comma:
            ctx.res = nodes[0]
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = Tuple(
                elts=nodes,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res.token_index = token_index
        # ```

    def cond_exprs_no_comp_list(self, ctx):
        # ```
        # Used in child `cond_exprs_no_comp_list_item`.
        ctx.res = AttrDict()
        ctx.res.nodes = []
        ctx.res.has_comma = False
        # ```
        cond_exprs_no_comp_list_item = self._scan_rule('cond_exprs_no_comp_list_item')  # noqa

    def cond_exprs_no_comp_list_item(self, ctx):
        # ```
        # Used in child `cond_exprs_no_comp_list_item`.
        ctx.res = ctx.par.res
        # ```
        cond_expr_no_comp = self._scan_rule('cond_expr_no_comp')  # noqa
        # ```
        ctx.res.nodes.append(cond_expr_no_comp.res)
        # ```
        if self._peek([
            'comma_hz',
            'async_comp_item_as_name_kw',
            'comp_item_as_name_kw'],
            is_required=True) == 'comma_hz':
            comma_hz = self._scan_rule('comma_hz')  # noqa
            # ```
            ctx.res.has_comma = True
            # ```
            if self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'async_comp_item_as_name_kw',
                'comp_item_as_name_kw'],
                is_required=True) in [
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz']:
                cond_exprs_no_comp_list_item = self._scan_rule('cond_exprs_no_comp_list_item')  # noqa

    def cond_expr(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        comp_expr = self._scan_rule('comp_expr')  # noqa
        # ```
        test_expr = comp_expr.res
        lhs_expr = None
        # ```
        if self._peek([
            'question_mark_hz',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz'],
            is_required=True) == 'question_mark_hz':
            question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
            comp_expr = self._scan_rule('comp_expr')  # noqa
            if self._peek([
                'question_mark_hz',
                'colon_hz'],
                is_required=True) == 'question_mark_hz':
                question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
                # ```
                self._retract()
                self._error(msg='连续的条件表达式请加括号。')
                # ```
            # ```
            lhs_expr = comp_expr.res
            # ```
            colon_hz = self._scan_rule('colon_hz')  # noqa
            comp_expr = self._scan_rule('comp_expr')  # noqa
            if self._peek([
                'question_mark_hz',
                'number',
                'string',
                'from_import_kw',
                'async_comp_item_as_name_kw',
                'async_with_kw',
                'async_loop_iterator_kw',
                'import_kw',
                'bit_invert_assign_op',
                'bit_right_shift_assign_op',
                'bit_left_shift_assign_op',
                'bit_xor_assign_op',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'decrement_op',
                'increment_op',
                'generator_generate_kw',
                'pass_kw',
                'comp_item_as_name_kw',
                'bit_and_assign_op',
                'bit_invert_op',
                'bit_or_assign_op',
                'modulo_assign_op',
                'power_assign_op',
                'break_kw',
                'tuple_with_kw',
                'elif_kw',
                'class_end_kw',
                'block_end_kw',
                'block_start_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'floor_divide_assign_op',
                'finally_kw',
                'loop_iterator_item_as_name_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'func_end_kw',
                'async_func_start_kw',
                'del_kw',
                'multiply_assign_op',
                'bool_false_kw',
                'subtract_assign_op',
                'add_assign_op',
                'tuple_kw',
                'as_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'raise_from_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'comp_then_kw',
                'return_kw',
                'listcomp_generate_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'divide_assign_op',
                'end',
                'pause_hz',
                'period_hz',
                'assign_op',
                'unary_subtract_op',
                'subscript_end_kw',
                'left_parenthesis_hz',
                'right_parenthesis_hz',
                'comma_hz',
                'colon_hz',
                'semicolon_hz'],
                is_required=True) == 'question_mark_hz':
                question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
                # ```
                self._retract()
                self._error(msg='连续的条件表达式请加括号。')
                # ```
            # ```
            rhs_expr = comp_expr.res
            # ```
        # ```
        if lhs_expr is None:
            ctx.res = test_expr
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = IfExp(
                test=test_expr,
                body=lhs_expr,
                orelse=rhs_expr,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
        # ```

    def cond_expr_no_comp(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        or_expr = self._scan_rule('or_expr')  # noqa
        # ```
        test_expr = or_expr.res
        lhs_expr = None
        # ```
        if self._peek([
            'question_mark_hz',
            'async_comp_item_as_name_kw',
            'comp_item_as_name_kw',
            'comma_hz'],
            is_required=True) == 'question_mark_hz':
            question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
            or_expr = self._scan_rule('or_expr')  # noqa
            if self._peek([
                'question_mark_hz',
                'colon_hz'],
                is_required=True) == 'question_mark_hz':
                question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
                # ```
                self._retract()
                self._error(msg='连续的条件表达式请加括号。')
                # ```
            # ```
            lhs_expr = or_expr.res
            # ```
            colon_hz = self._scan_rule('colon_hz')  # noqa
            or_expr = self._scan_rule('or_expr')  # noqa
            if self._peek([
                'question_mark_hz',
                'async_comp_item_as_name_kw',
                'comp_item_as_name_kw',
                'comma_hz'],
                is_required=True) == 'question_mark_hz':
                question_mark_hz = self._scan_rule('question_mark_hz')  # noqa
                # ```
                self._retract()
                self._error(msg='连续的条件表达式请加括号。')
                # ```
            # ```
            rhs_expr = or_expr.res
            # ```
        # ```
        if lhs_expr is None:
            ctx.res = test_expr
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = IfExp(
                test=test_expr,
                body=lhs_expr,
                orelse=rhs_expr,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
        # ```

    def comp_expr(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        or_expr = self._scan_rule('or_expr')  # noqa
        # ```
        ctx.res = or_expr.res
        ctx.start_row = start_row
        ctx.start_col = start_col
        # ```
        while self._peek([
            'async_comp_item_as_name_kw',
            'comp_item_as_name_kw',
            'number',
            'string',
            'from_import_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'async_comp_item_as_name_kw',
            'comp_item_as_name_kw']:
            comp_trailer = self._scan_rule('comp_trailer')  # noqa

    def comp_trailer(self, ctx):
        # ```
        iter_node = ctx.par.res
        start_row = ctx.par.start_row
        start_col = ctx.par.start_col
        comp_infos = []
        # ```
        if self._peek(['comp_item_as_name_kw']):
            comp_item_as_name_kw = self._scan_rule('comp_item_as_name_kw')  # noqa
            # ```
            is_async = False
            # ```
        elif self._peek(['async_comp_item_as_name_kw'], is_branch=True):
            async_comp_item_as_name_kw = self._scan_rule('async_comp_item_as_name_kw')  # noqa
            # ```
            is_async = True
            # ```
        else:
            self._error(token_names=[
            'async_comp_item_as_name_kw',
            'comp_item_as_name_kw'])
        # ```
        names_start_row, names_start_col = self._get_start_row_col()
        # ```
        comp_names_list = self._scan_rule('comp_names_list')  # noqa
        # ```
        names_end_row, names_end_col = self._get_end_row_col()
        if_expr = None
        # ```
        if self._peek([
            'comp_if_kw',
            'generator_generate_kw',
            'comp_then_kw',
            'listcomp_generate_kw'],
            is_required=True) == 'comp_if_kw':
            comp_if_kw = self._scan_rule('comp_if_kw')  # noqa
            expr = self._scan_rule('expr')  # noqa
            # ```
            if_expr = expr.res
            # ```
        # ```
        comp_info = dict(
            is_async=is_async,
            names_start_row=names_start_row,
            names_start_col=names_start_col,
            names_end_row=names_end_row,
            names_end_col=names_end_col,
            names_list=comp_names_list.res,
            if_expr=if_expr,
            iter_node=iter_node,
        )
        comp_infos.append(comp_info)
        # ```
        while self._peek([
            'comp_then_kw',
            'generator_generate_kw',
            'listcomp_generate_kw'],
            is_required=True) == 'comp_then_kw':
            comp_then_kw = self._scan_rule('comp_then_kw')  # noqa
            expr_no_comp = self._scan_rule('expr_no_comp')  # noqa
            # ```
            iter_node = expr_no_comp.res
            # ```
            if self._peek(['comp_item_as_name_kw']):
                comp_item_as_name_kw = self._scan_rule('comp_item_as_name_kw')  # noqa
                # ```
                is_async = False
                # ```
            elif self._peek(['async_comp_item_as_name_kw'], is_branch=True):
                async_comp_item_as_name_kw = self._scan_rule('async_comp_item_as_name_kw')  # noqa
                # ```
                is_async = True
                # ```
            else:
                self._error(token_names=[
                'async_comp_item_as_name_kw',
                'comp_item_as_name_kw'])
            # ```
            names_start_row, names_start_col = self._get_start_row_col()
            # ```
            comp_names_list = self._scan_rule('comp_names_list')  # noqa
            # ```
            names_end_row, names_end_col = self._get_end_row_col()
            if_expr = None
            # ```
            if self._peek([
                'comp_if_kw',
                'generator_generate_kw',
                'comp_then_kw',
                'listcomp_generate_kw'],
                is_required=True) == 'comp_if_kw':
                comp_if_kw = self._scan_rule('comp_if_kw')  # noqa
                expr = self._scan_rule('expr')  # noqa
                # ```
                if_expr = expr.res
                # ```
            # ```
            comp_info = dict(
                is_async=is_async,
                names_start_row=names_start_row,
                names_start_col=names_start_col,
                names_end_row=names_end_row,
                names_end_col=names_end_col,
                names_list=comp_names_list.res,
                if_expr=if_expr,
                iter_node=iter_node,
            )
            comp_infos.append(comp_info)
            # ```
        if self._peek(['listcomp_generate_kw']):
            listcomp_generate_kw = self._scan_rule('listcomp_generate_kw')  # noqa
            # ```
            is_generator = False
            # ```
        elif self._peek(['generator_generate_kw'], is_branch=True):
            generator_generate_kw = self._scan_rule('generator_generate_kw')  # noqa
            # ```
            is_generator = True
            # ```
        else:
            self._error(token_names=[
            'generator_generate_kw',
            'listcomp_generate_kw'])
        expr = self._scan_rule('expr')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()

        comp_nodes = []

        for comp_info in comp_infos:
            is_async = comp_info['is_async']
            names_start_row = comp_info['names_start_row']
            names_start_col = comp_info['names_start_col']
            names_end_row = comp_info['names_end_row']
            names_end_col = comp_info['names_end_col']
            names_list = comp_info['names_list']
            if_expr = comp_info['if_expr']
            iter_node = comp_info['iter_node']

            name_nodes = names_list

            name_nodes_count = len(name_nodes)

            for name_node in name_nodes:
                name_node.ctx = Store()

            if name_nodes_count == 1:
                comp_vars = name_nodes[0]
            else:
                comp_vars = Tuple(
                    elts=name_nodes,
                    ctx=Store(),
                    lineno=names_start_row,
                    col_offset=names_start_col,
                    end_lineno=names_end_row,
                    end_col_offset=names_end_col,
                )

            if if_expr is None:
                comp_node_end_row = name_nodes[-1].end_lineno
                comp_node_end_col = name_nodes[-1].end_col_offset
            else:
                comp_node_end_row = if_expr.end_lineno
                comp_node_end_col = if_expr.end_col_offset

            comp_node = comprehension(
                target=comp_vars,
                iter=iter_node,
                ifs=[] if if_expr is None else [if_expr],
                is_async=is_async,
                lineno=iter_node.lineno,
                col_offset=iter_node.col_offset,
                end_lineno=comp_node_end_row,
                end_col_offset=comp_node_end_col,
            )

            comp_nodes.append(comp_node)

        node_class = GeneratorExp if is_generator else ListComp

        ctx.par.res = node_class(
            elt=expr.res,
            generators=comp_nodes,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def comp_names_list(self, ctx):
        # ```
        # Used in child `comp_names_list_item`.
        ctx.res = []
        # ```
        comp_names_list_item = self._scan_rule('comp_names_list_item')  # noqa

    def comp_names_list_item(self, ctx):
        # ```
        # Used in child `comp_names_list_item`.
        ctx.res = ctx.par.res
        # ```
        name = self._scan_rule('name')  # noqa
        # ```
        ctx.res.append(name.res)
        # ```
        if self._peek([
            'pause_hz',
            'generator_generate_kw',
            'comp_then_kw',
            'listcomp_generate_kw',
            'comp_if_kw'],
            is_required=True) == 'pause_hz':
            pause_hz = self._scan_rule('pause_hz')  # noqa
            comp_names_list_item = self._scan_rule('comp_names_list_item')  # noqa

    def or_expr(self, ctx):
        # ```
        results = []
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        first_op_pos = None
        # ```
        and_expr = self._scan_rule('and_expr')  # noqa
        # ```
        results.append(and_expr.res)
        # ```
        while self._peek([
            'or_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) == 'or_op':
            # ```
            if first_op_pos is None:
                op_start_row, op_start_col = self._get_start_row_col()
            # ```
            or_op = self._scan_rule('or_op')  # noqa
            # ```
            if first_op_pos is None:
                op_end_row, op_end_col = self._get_end_row_col()

                first_op_pos = dict(
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                )
            # ```
            and_expr = self._scan_rule('and_expr')  # noqa
            # ```
            results.append(and_expr.res)
            # ```
        # ```
        if len(results) == 1:
            ctx.res = results[0]
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = BoolOp(
                op=Or(**first_op_pos),
                values=results,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res.token_index = token_index
        # ```

    def and_expr(self, ctx):
        # ```
        results = []
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        first_op_pos = None
        # ```
        not_expr = self._scan_rule('not_expr')  # noqa
        # ```
        results.append(not_expr.res)
        # ```
        while self._peek([
            'and_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) == 'and_op':
            # ```
            if first_op_pos is None:
                op_start_row, op_start_col = self._get_start_row_col()
            # ```
            and_op = self._scan_rule('and_op')  # noqa
            # ```
            if first_op_pos is None:
                op_end_row, op_end_col = self._get_end_row_col()

                first_op_pos = dict(
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                )
            # ```
            not_expr = self._scan_rule('not_expr')  # noqa
            # ```
            results.append(not_expr.res)
            # ```
        # ```
        if len(results) == 1:
            ctx.res = results[0]
        else:
            end_row, end_col = self._get_end_row_col()

            ctx.res = BoolOp(
                op=And(**first_op_pos),
                values=results,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res.token_index = token_index
        # ```

    def not_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['not_op']):
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            not_op = self._scan_rule('not_op')  # noqa
            # ```
            op_end_row, op_end_col = self._get_end_row_col()
            # ```
            not_expr = self._scan_rule('not_expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = UnaryOp(
                op=Not(
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                ),
                operand=not_expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek([
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'], is_branch=True):
            compare_expr = self._scan_rule('compare_expr')  # noqa
            # ```
            ctx.res = compare_expr.res
            # ```
        else:
            self._error(token_names=[
            'number',
            'string',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'])
        # ```
        ctx.res.token_index = token_index
        # ```

    def compare_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        arrow_expr = self._scan_rule('arrow_expr')  # noqa
        # ```
        left_expr = arrow_expr.res
        ops = []
        comparators = []
        # ```
        while self._peek([
            'not_in_op',
            'ge_op',
            'le_op',
            'not_equal_op',
            'in_op',
            'isnot_op',
            'gt_op',
            'lt_op',
            'is_op',
            'equal_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'decrement_op',
            'increment_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'not_in_op',
            'ge_op',
            'le_op',
            'not_equal_op',
            'in_op',
            'isnot_op',
            'gt_op',
            'lt_op',
            'is_op',
            'equal_op']:
            # ```
            op_start_row, op_start_col = self._get_row_col()
            # ```
            if self._peek(['is_op']):
                is_op = self._scan_rule('is_op')  # noqa
                # ```
                op_class = Is
                # ```
            elif self._peek(['isnot_op'], is_branch=True):
                isnot_op = self._scan_rule('isnot_op')  # noqa
                # ```
                op_class = IsNot
                # ```
            elif self._peek(['equal_op'], is_branch=True):
                equal_op = self._scan_rule('equal_op')  # noqa
                # ```
                op_class = Eq
                # ```
            elif self._peek(['not_equal_op'], is_branch=True):
                not_equal_op = self._scan_rule('not_equal_op')  # noqa
                # ```
                op_class = NotEq
                # ```
            elif self._peek(['lt_op'], is_branch=True):
                lt_op = self._scan_rule('lt_op')  # noqa
                # ```
                op_class = Lt
                # ```
            elif self._peek(['le_op'], is_branch=True):
                le_op = self._scan_rule('le_op')  # noqa
                # ```
                op_class = LtE
                # ```
            elif self._peek(['gt_op'], is_branch=True):
                gt_op = self._scan_rule('gt_op')  # noqa
                # ```
                op_class = Gt
                # ```
            elif self._peek(['ge_op'], is_branch=True):
                ge_op = self._scan_rule('ge_op')  # noqa
                # ```
                op_class = GtE
                # ```
            elif self._peek(['in_op'], is_branch=True):
                in_op = self._scan_rule('in_op')  # noqa
                # ```
                op_class = In
                # ```
            elif self._peek(['not_in_op'], is_branch=True):
                not_in_op = self._scan_rule('not_in_op')  # noqa
                # ```
                op_class = NotIn
                # ```
            else:
                self._error(token_names=[
                'not_in_op',
                'ge_op',
                'le_op',
                'not_equal_op',
                'in_op',
                'isnot_op',
                'gt_op',
                'lt_op',
                'is_op',
                'equal_op'])
            # ```
            op_end_row, op_end_col = self._get_end_row_col()

            op_node = op_class(
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=op_end_row,
                end_col_offset=op_end_col,
            )

            ops.append(op_node)
            # ```
            arrow_expr = self._scan_rule('arrow_expr')  # noqa
            # ```
            comparators.append(arrow_expr.res)
            # ```
        # ```
        if not ops:
            ctx.res = left_expr
        else:
            end_row, end_col = self._get_end_row_col()
            ctx.res = Compare(
                left=left_expr,
                ops=ops,
                comparators=comparators,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )

        ctx.res.token_index = token_index
        # ```

    def arrow_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        # ```
        bitwise_expr = self._scan_rule('bitwise_expr')  # noqa
        # ```
        res_expr = bitwise_expr.res
        # ```
        # ```
        rhs_infos = []
        # ```
        while self._peek([
            'arrow_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) == 'arrow_op':
            arrow_op = self._scan_rule('arrow_op')  # noqa
            # ```
            rhs_token_index = self._get_token_index()
            # ```
            bitwise_expr = self._scan_rule('bitwise_expr')  # noqa
            # ```
            rhs_infos.append((rhs_token_index, bitwise_expr.res))
            # ```
        # ```
        if len(rhs_infos) == 0:
            ctx.res = res_expr
        else:
            for rhs_token_index, rhs_expr in rhs_infos:
                if not isinstance(rhs_expr, Call):
                    self._retract(rhs_token_index)

                    self._error(msg='`接倒起`的右手边不是函数调用。')

                for arg_index, arg in enumerate(rhs_expr.args):
                    if isinstance(arg, Name) and arg.id == '…':
                        break
                else:
                    self._retract(rhs_token_index)

                    self._error(msg='`接倒起`的右手边函数调用参数缺占位符`…`。')

                rhs_expr.args[arg_index:arg_index+1] = [res_expr]

                res_expr = rhs_expr

            ctx.res = res_expr

        ctx.res.token_index = token_index
        # ```

    def bitwise_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        add_substruct_expr = self._scan_rule('add_substruct_expr')  # noqa
        # ```
        res_expr = add_substruct_expr.res
        # ```
        while self._peek([
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_and_op',
            'bit_or_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'arrow_op',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_and_op',
            'bit_or_op']:
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            if self._peek(['bit_and_op']):
                bit_and_op = self._scan_rule('bit_and_op')  # noqa
                # ```
                op_class = BitAnd
                # ```
            elif self._peek(['bit_or_op'], is_branch=True):
                bit_or_op = self._scan_rule('bit_or_op')  # noqa
                # ```
                op_class = BitOr
                # ```
            elif self._peek(['bit_xor_op'], is_branch=True):
                bit_xor_op = self._scan_rule('bit_xor_op')  # noqa
                # ```
                op_class = BitXor
                # ```
            elif self._peek(['bit_left_shift_op'], is_branch=True):
                bit_left_shift_op = self._scan_rule('bit_left_shift_op')  # noqa
                # ```
                op_class = LShift
                # ```
            elif self._peek(['bit_right_shift_op'], is_branch=True):
                bit_right_shift_op = self._scan_rule('bit_right_shift_op')  # noqa
                # ```
                op_class = RShift
                # ```
            else:
                self._error(token_names=[
                'bit_right_shift_op',
                'bit_left_shift_op',
                'bit_xor_op',
                'bit_and_op',
                'bit_or_op'])
            # ```
            end_row, end_col = self._get_end_row_col()
            op_node = op_class(
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
            add_substruct_expr = self._scan_rule('add_substruct_expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            res_expr = BinOp(
                left=res_expr,
                op=op_node,
                right=add_substruct_expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        # ```
        ctx.res = res_expr
        ctx.res.token_index = token_index
        # ```

    def add_substruct_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        multiply_divide_expr = self._scan_rule('multiply_divide_expr')  # noqa
        # ```
        res_expr = multiply_divide_expr.res
        # ```
        while self._peek([
            'subtract_op',
            'add_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'arrow_op',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'bit_and_op',
            'bit_or_op',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'subtract_op',
            'add_op']:
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            if self._peek(['add_op']):
                add_op = self._scan_rule('add_op')  # noqa
                # ```
                op_class = Add
                # ```
            elif self._peek(['subtract_op'], is_branch=True):
                subtract_op = self._scan_rule('subtract_op')  # noqa
                # ```
                op_class = Sub
                # ```
            else:
                self._error(token_names=[
                'subtract_op',
                'add_op'])
            # ```
            op_end_row, op_end_col = self._get_end_row_col()
            op_node = op_class(
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=op_end_row,
                end_col_offset=op_end_col,
            )
            # ```
            multiply_divide_expr = self._scan_rule('multiply_divide_expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            res_expr = BinOp(
                left=res_expr,
                op=op_node,
                right=multiply_divide_expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        # ```
        ctx.res = res_expr
        ctx.res.token_index = token_index
        # ```

    def multiply_divide_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        start_row, start_col = self._get_start_row_col()
        # ```
        power_expr = self._scan_rule('power_expr')  # noqa
        # ```
        res_expr = power_expr.res
        # ```
        while self._peek([
            'modulo_op',
            'floor_divide_op',
            'multiply_op',
            'divide_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'arrow_op',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'bit_and_op',
            'bit_or_op',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'subtract_op',
            'add_op',
            'assign_op',
            'unary_subtract_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'modulo_op',
            'floor_divide_op',
            'multiply_op',
            'divide_op']:
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            if self._peek(['multiply_op']):
                multiply_op = self._scan_rule('multiply_op')  # noqa
                # ```
                op_class = Mult
                # ```
            elif self._peek(['divide_op'], is_branch=True):
                divide_op = self._scan_rule('divide_op')  # noqa
                # ```
                op_class = Div
                # ```
            elif self._peek(['floor_divide_op'], is_branch=True):
                floor_divide_op = self._scan_rule('floor_divide_op')  # noqa
                # ```
                op_class = FloorDiv
                # ```
            elif self._peek(['modulo_op'], is_branch=True):
                modulo_op = self._scan_rule('modulo_op')  # noqa
                # ```
                op_class = Mod
                # ```
            else:
                self._error(token_names=[
                'modulo_op',
                'floor_divide_op',
                'multiply_op',
                'divide_op'])
            # ```
            op_end_row, op_end_col = self._get_end_row_col()
            op_node = op_class(
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=op_end_row,
                end_col_offset=op_end_col,
            )
            # ```
            power_expr = self._scan_rule('power_expr')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()

            res_expr = BinOp(
                left=res_expr,
                op=op_node,
                right=power_expr.res,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        # ```
        ctx.res = res_expr
        ctx.res.token_index = token_index
        # ```

    def power_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        stack = []
        # ```
        trailer_expr = self._scan_rule('trailer_expr')  # noqa
        # ```
        stack.append((trailer_expr.res, None, None, None, None))
        # ```
        while self._peek([
            'power_op',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'arrow_op',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'bit_and_op',
            'bit_or_op',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'modulo_op',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'floor_divide_op',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'multiply_op',
            'subtract_op',
            'add_op',
            'assign_op',
            'unary_subtract_op',
            'divide_op',
            'subscript_end_kw',
            'left_parenthesis_hz',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) == 'power_op':
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            power_op = self._scan_rule('power_op')  # noqa
            # ```
            op_end_row, op_end_col = self._get_end_row_col()
            # ```
            trailer_expr = self._scan_rule('trailer_expr')  # noqa
            # ```
            stack.append(
                (
                    trailer_expr.res,
                    op_start_row,
                    op_start_col,
                    op_end_row,
                    op_end_col,
                )
            )
            # ```
        # ```
        if len(stack) == 1:
            ctx.res = stack[0][0]
        else:
            rhs_node, op_start_row, op_start_col, op_end_row, op_end_col\
                = stack.pop()

            while stack:
                lhs_node, op_start_row2, op_start_col2, op_end_row2, op_end_col2\
                    = stack.pop()

                rhs_node = BinOp(
                    left=lhs_node,
                    op=Pow(
                        lineno=op_start_row,
                        col_offset=op_start_col,
                        end_lineno=op_end_row,
                        end_col_offset=op_end_col,
                    ),
                    right=rhs_node,
                    lineno=lhs_node.lineno,
                    col_offset=lhs_node.col_offset,
                    end_lineno=rhs_node.end_lineno,
                    end_col_offset=rhs_node.end_col_offset,
                )

                op_start_row = op_start_row2
                op_start_col = op_start_col2
                op_end_row = op_end_row2
                op_end_col = op_end_col2

            ctx.res = rhs_node

        ctx.res.token_index = token_index
        # ```

    def trailer_expr(self, ctx):
        # ```
        token_index = self._get_token_index()
        op_node = None
        # ```
        if self._peek([
            'bit_invert_op',
            'unary_subtract_op',
            'number',
            'string',
            'name',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'left_parenthesis_hz'],
            is_required=True) in [
            'bit_invert_op',
            'unary_subtract_op']:
            # ```
            op_start_row, op_start_col = self._get_start_row_col()
            # ```
            if self._peek(['unary_subtract_op']):
                unary_subtract_op = self._scan_rule('unary_subtract_op')  # noqa
                # ```
                op_class = USub
                # ```
            elif self._peek(['bit_invert_op'], is_branch=True):
                bit_invert_op = self._scan_rule('bit_invert_op')  # noqa
                # ```
                op_class = Invert
                # ```
            else:
                self._error(token_names=[
                'bit_invert_op',
                'unary_subtract_op'])
            # ```
            op_end_row, op_end_col = self._get_end_row_col()
            op_node = op_class(
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=op_end_row,
                end_col_offset=op_end_col,
            )
            # ```
        atom_expr = self._scan_rule('atom_expr')  # noqa
        # ```
        atom_node = atom_expr.res

        if op_node is not None:
            ctx.res = UnaryOp(
                op=op_node,
                operand=atom_node,
                lineno=op_start_row,
                col_offset=op_start_col,
                end_lineno=atom_node.end_lineno,
                end_col_offset=atom_node.end_col_offset,
            )
        else:
            ctx.res = atom_node

        ctx.res.token_index = token_index
        # ```
        while self._peek([
            'any_trailer',
            'all_trailer',
            'hex_trailer',
            'extend_trailer',
            'ord_trailer',
            'bytearray_trailer',
            'bin_trailer',
            'oct_trailer',
            'str_trailer',
            'bytes_trailer',
            'max_trailer',
            'min_trailer',
            'format_trailer',
            'float_trailer',
            'opposite_trailer',
            'abs_trailer',
            'range_trailer',
            'decorate_kw',
            'reciprocal_trailer',
            'tuple_trailer',
            'type_trailer',
            'name_trailer',
            'append_trailer',
            'chr_trailer',
            'count_trailer',
            'sort_trailer',
            'int_trailer',
            'add_trailer',
            'clear_trailer',
            'dict_trailer',
            'bool_trailer',
            'list_trailer',
            'repr_trailer',
            'set_trailer',
            'len_trailer',
            'nonlocal_kw',
            'global_kw',
            'sum_trailer',
            'dot_kw',
            'trailer_prefix',
            'subscript_start_kw',
            'left_parenthesis_hz',
            'number',
            'string',
            'from_import_kw',
            'async_comp_item_as_name_kw',
            'async_with_kw',
            'async_loop_iterator_kw',
            'import_kw',
            'bit_invert_assign_op',
            'bit_right_shift_assign_op',
            'bit_left_shift_assign_op',
            'bit_xor_assign_op',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'not_in_op',
            'decrement_op',
            'increment_op',
            'ge_op',
            'le_op',
            'generator_generate_kw',
            'pass_kw',
            'comp_item_as_name_kw',
            'bit_and_assign_op',
            'bit_invert_op',
            'bit_right_shift_op',
            'bit_left_shift_op',
            'bit_xor_op',
            'bit_or_assign_op',
            'modulo_assign_op',
            'power_assign_op',
            'break_kw',
            'not_equal_op',
            'tuple_with_kw',
            'elif_kw',
            'class_end_kw',
            'in_op',
            'block_end_kw',
            'block_start_kw',
            'except_kw',
            'loop_iterator_kw',
            'continue_kw',
            'arrow_op',
            'floor_divide_assign_op',
            'finally_kw',
            'loop_iterator_item_as_name_kw',
            'bit_and_op',
            'bit_or_op',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'modulo_op',
            'power_op',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'func_end_kw',
            'async_func_start_kw',
            'isnot_op',
            'del_kw',
            'multiply_assign_op',
            'bool_false_kw',
            'subtract_assign_op',
            'add_assign_op',
            'tuple_kw',
            'as_kw',
            'class_start_kw',
            'exit_kw',
            'gt_op',
            'if_kw',
            'lt_op',
            'is_op',
            'raise_from_kw',
            'and_op',
            'not_op',
            'print_kw',
            'or_op',
            'raise_kw',
            'floor_divide_op',
            'comp_then_kw',
            'return_kw',
            'listcomp_generate_kw',
            'dict_kw',
            'bool_true_kw',
            'equal_op',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'divide_assign_op',
            'end',
            'pause_hz',
            'period_hz',
            'multiply_op',
            'subtract_op',
            'add_op',
            'assign_op',
            'unary_subtract_op',
            'divide_op',
            'subscript_end_kw',
            'right_parenthesis_hz',
            'comma_hz',
            'colon_hz',
            'semicolon_hz',
            'question_mark_hz'],
            is_required=True) in [
            'any_trailer',
            'all_trailer',
            'hex_trailer',
            'extend_trailer',
            'ord_trailer',
            'bytearray_trailer',
            'bin_trailer',
            'oct_trailer',
            'str_trailer',
            'bytes_trailer',
            'max_trailer',
            'min_trailer',
            'format_trailer',
            'float_trailer',
            'opposite_trailer',
            'abs_trailer',
            'range_trailer',
            'decorate_kw',
            'reciprocal_trailer',
            'tuple_trailer',
            'type_trailer',
            'name_trailer',
            'append_trailer',
            'chr_trailer',
            'count_trailer',
            'sort_trailer',
            'int_trailer',
            'add_trailer',
            'clear_trailer',
            'dict_trailer',
            'bool_trailer',
            'list_trailer',
            'repr_trailer',
            'set_trailer',
            'len_trailer',
            'nonlocal_kw',
            'global_kw',
            'sum_trailer',
            'dot_kw',
            'trailer_prefix',
            'subscript_start_kw',
            'left_parenthesis_hz']:
            atom_trailer = self._scan_rule('atom_trailer')  # noqa

    def atom_expr(self, ctx):
        if self._peek(['none_kw']):
            none = self._scan_rule('none')  # noqa
            # ```
            ctx.res = none.res
            # ```
        elif self._peek([
            'bool_false_kw',
            'bool_true_kw'], is_branch=True):
            boolean = self._scan_rule('boolean')  # noqa
            # ```
            ctx.res = boolean.res
            # ```
        elif self._peek(['number'], is_branch=True):
            number = self._scan_rule('number')  # noqa
            # ```
            ctx.res = number.res
            # ```
        elif self._peek(['string'], is_branch=True):
            string = self._scan_rule('string')  # noqa
            # ```
            ctx.res = string.res
            # ```
        elif self._peek(['name'], is_branch=True):
            name = self._scan_rule('name')  # noqa
            # ```
            ctx.res = name.res
            # ```
        elif self._peek([
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'tuple_kw',
            'dict_kw',
            'list_kw',
            'set_kw'], is_branch=True):
            container = self._scan_rule('container')  # noqa
            # ```
            ctx.res = container.res
            # ```
        elif self._peek(['left_parenthesis_hz'], is_branch=True):
            parentheses_expr = self._scan_rule('parentheses_expr')  # noqa
            # ```
            ctx.res = parentheses_expr.res
            # ```
        else:
            self._error(token_names=[
            'number',
            'string',
            'name',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'bool_false_kw',
            'tuple_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'left_parenthesis_hz'])

    def container(self, ctx):
        if self._peek(['list_kw']):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            list_kw = self._scan_rule('list_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = List(
                elts=[],
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['list_with_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            list_with_kw = self._scan_rule('list_with_kw')  # noqa
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = List(
                elts=args_list.res.args,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['tuple_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            tuple_kw = self._scan_rule('tuple_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Tuple(
                elts=[],
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['tuple_with_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            tuple_with_kw = self._scan_rule('tuple_with_kw')  # noqa
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Tuple(
                elts=args_list.res.args,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['dict_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            dict_kw = self._scan_rule('dict_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Dict(
                keys=[],
                values=[],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['dict_with_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            dict_with_kw = self._scan_rule('dict_with_kw')  # noqa
            # ```
            kw_end_row, kw_end_col = self._get_end_row_col()
            args_start_row, args_start_col = self._get_start_row_col()
            # ```
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Call(
                func=Name(
                    id='dict',
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=kw_end_row,
                    end_col_offset=kw_end_col,
                ),
                args=[
                    List(
                        elts=args_list.res.args,
                        ctx=Load(),
                        lineno=args_start_row,
                        col_offset=args_start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    )
                ],
                keywords=[],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['set_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            set_kw = self._scan_rule('set_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Call(
                func=Name(
                    id='set',
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                ),
                args=[],
                keywords=[],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['set_with_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            set_with_kw = self._scan_rule('set_with_kw')  # noqa
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.res = Set(
                elts=args_list.res.args,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        else:
            self._error(token_names=[
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'tuple_kw',
            'dict_kw',
            'list_kw',
            'set_kw'])

    def parentheses_expr(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        left_parenthesis_hz = self._scan_rule('left_parenthesis_hz')  # noqa
        if self._peek(['right_parenthesis_hz']):
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            # ```
            # ```
            ctx.res = Tuple(
                elts=[],
                ctx=Store(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek([
            'number',
            'string',
            'yield_from_kw',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'yield_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'], is_branch=True):
            if self._peek([
                'yield_from_kw',
                'yield_kw']):
                yield_expr = self._scan_rule('yield_expr')  # noqa
                # ```
                ctx.res = yield_expr.res
                # ```
            elif self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'], is_branch=True):
                expr = self._scan_rule('expr')  # noqa
                # ```
                ctx.res = expr.res
                # ```
            else:
                self._error(token_names=[
                'number',
                'string',
                'yield_from_kw',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'yield_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'])
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
        else:
            self._error(token_names=[
            'number',
            'string',
            'yield_from_kw',
            'name',
            'bit_invert_op',
            'tuple_with_kw',
            'dict_with_kw',
            'list_with_kw',
            'set_with_kw',
            'yield_kw',
            'bool_false_kw',
            'tuple_kw',
            'not_op',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'unary_subtract_op',
            'left_parenthesis_hz',
            'right_parenthesis_hz'])

    def atom_trailer(self, ctx):
        if self._peek(['dot_kw']):
            # ```
            token_index = self._get_token_index()
            start_row, start_col = self._get_start_row_col()
            # ```
            dot_kw = self._scan_rule('dot_kw')  # noqa
            name = self._scan_rule('name')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            par_node = ctx.par.res
            ctx.par.res = Attribute(
                value=par_node,
                attr=name.res.id,
                ctx=Load(),
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.par.res.token_index = token_index
            # ```
        elif self._peek(['global_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            global_kw = self._scan_rule('global_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.par.res = Global(
                names=[ctx.par.res.id],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['nonlocal_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            nonlocal_kw = self._scan_rule('nonlocal_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.par.res = Nonlocal(
                names=[ctx.par.res.id],
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['left_parenthesis_hz'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            args_list = self._scan_rule('args_list')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            ctx.par.res = Call(
                func=ctx.par.res,
                args=args_list.res.args,
                keywords=args_list.res.kwargs,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            # ```
        elif self._peek(['subscript_start_kw'], is_branch=True):
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            subscript_start_kw = self._scan_rule('subscript_start_kw')  # noqa
            # ```
            is_slice = False
            slice_part1 = None
            slice_part2 = None
            slice_part3 = None
            index_start_row, index_start_col = self._get_start_row_col()
            # ```
            if self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz']):
                expr = self._scan_rule('expr')  # noqa
                # ```
                slice_part1 = expr.res
                # ```
                if self._peek([
                    'colon_hz',
                    'subscript_end_kw'],
                    is_required=True) == 'colon_hz':
                    colon_hz = self._scan_rule('colon_hz')  # noqa
                    # ```
                    is_slice = True
                    # ```
                    if self._peek([
                        'number',
                        'string',
                        'name',
                        'bit_invert_op',
                        'tuple_with_kw',
                        'dict_with_kw',
                        'list_with_kw',
                        'set_with_kw',
                        'bool_false_kw',
                        'tuple_kw',
                        'not_op',
                        'dict_kw',
                        'bool_true_kw',
                        'list_kw',
                        'none_kw',
                        'set_kw',
                        'unary_subtract_op',
                        'left_parenthesis_hz',
                        'colon_hz',
                        'subscript_end_kw'],
                        is_required=True):
                        if self._peek([
                            'number',
                            'string',
                            'name',
                            'bit_invert_op',
                            'tuple_with_kw',
                            'dict_with_kw',
                            'list_with_kw',
                            'set_with_kw',
                            'bool_false_kw',
                            'tuple_kw',
                            'not_op',
                            'dict_kw',
                            'bool_true_kw',
                            'list_kw',
                            'none_kw',
                            'set_kw',
                            'unary_subtract_op',
                            'left_parenthesis_hz',
                            'subscript_end_kw',
                            'colon_hz'],
                            is_required=True) in [
                            'number',
                            'string',
                            'name',
                            'bit_invert_op',
                            'tuple_with_kw',
                            'dict_with_kw',
                            'list_with_kw',
                            'set_with_kw',
                            'bool_false_kw',
                            'tuple_kw',
                            'not_op',
                            'dict_kw',
                            'bool_true_kw',
                            'list_kw',
                            'none_kw',
                            'set_kw',
                            'unary_subtract_op',
                            'left_parenthesis_hz']:
                            expr = self._scan_rule('expr')  # noqa
                            # ```
                            slice_part2 = expr.res
                            # ```
                        if self._peek([
                            'colon_hz',
                            'subscript_end_kw'],
                            is_required=True) == 'colon_hz':
                            colon_hz = self._scan_rule('colon_hz')  # noqa
                            if self._peek([
                                'number',
                                'string',
                                'name',
                                'bit_invert_op',
                                'tuple_with_kw',
                                'dict_with_kw',
                                'list_with_kw',
                                'set_with_kw',
                                'bool_false_kw',
                                'tuple_kw',
                                'not_op',
                                'dict_kw',
                                'bool_true_kw',
                                'list_kw',
                                'none_kw',
                                'set_kw',
                                'unary_subtract_op',
                                'left_parenthesis_hz',
                                'subscript_end_kw'],
                                is_required=True) in [
                                'number',
                                'string',
                                'name',
                                'bit_invert_op',
                                'tuple_with_kw',
                                'dict_with_kw',
                                'list_with_kw',
                                'set_with_kw',
                                'bool_false_kw',
                                'tuple_kw',
                                'not_op',
                                'dict_kw',
                                'bool_true_kw',
                                'list_kw',
                                'none_kw',
                                'set_kw',
                                'unary_subtract_op',
                                'left_parenthesis_hz']:
                                expr = self._scan_rule('expr')  # noqa
                                # ```
                                slice_part3 = expr.res
                                # ```
            elif self._peek(['colon_hz'], is_branch=True):
                colon_hz = self._scan_rule('colon_hz')  # noqa
                # ```
                is_slice = True
                # ```
                if self._peek([
                    'number',
                    'string',
                    'name',
                    'bit_invert_op',
                    'tuple_with_kw',
                    'dict_with_kw',
                    'list_with_kw',
                    'set_with_kw',
                    'bool_false_kw',
                    'tuple_kw',
                    'not_op',
                    'dict_kw',
                    'bool_true_kw',
                    'list_kw',
                    'none_kw',
                    'set_kw',
                    'unary_subtract_op',
                    'left_parenthesis_hz',
                    'colon_hz',
                    'subscript_end_kw'],
                    is_required=True):
                    if self._peek([
                        'number',
                        'string',
                        'name',
                        'bit_invert_op',
                        'tuple_with_kw',
                        'dict_with_kw',
                        'list_with_kw',
                        'set_with_kw',
                        'bool_false_kw',
                        'tuple_kw',
                        'not_op',
                        'dict_kw',
                        'bool_true_kw',
                        'list_kw',
                        'none_kw',
                        'set_kw',
                        'unary_subtract_op',
                        'left_parenthesis_hz',
                        'subscript_end_kw',
                        'colon_hz'],
                        is_required=True) in [
                        'number',
                        'string',
                        'name',
                        'bit_invert_op',
                        'tuple_with_kw',
                        'dict_with_kw',
                        'list_with_kw',
                        'set_with_kw',
                        'bool_false_kw',
                        'tuple_kw',
                        'not_op',
                        'dict_kw',
                        'bool_true_kw',
                        'list_kw',
                        'none_kw',
                        'set_kw',
                        'unary_subtract_op',
                        'left_parenthesis_hz']:
                        expr = self._scan_rule('expr')  # noqa
                        # ```
                        slice_part2 = expr.res
                        # ```
                    if self._peek([
                        'colon_hz',
                        'subscript_end_kw'],
                        is_required=True) == 'colon_hz':
                        colon_hz = self._scan_rule('colon_hz')  # noqa
                        if self._peek([
                            'number',
                            'string',
                            'name',
                            'bit_invert_op',
                            'tuple_with_kw',
                            'dict_with_kw',
                            'list_with_kw',
                            'set_with_kw',
                            'bool_false_kw',
                            'tuple_kw',
                            'not_op',
                            'dict_kw',
                            'bool_true_kw',
                            'list_kw',
                            'none_kw',
                            'set_kw',
                            'unary_subtract_op',
                            'left_parenthesis_hz',
                            'subscript_end_kw'],
                            is_required=True) in [
                            'number',
                            'string',
                            'name',
                            'bit_invert_op',
                            'tuple_with_kw',
                            'dict_with_kw',
                            'list_with_kw',
                            'set_with_kw',
                            'bool_false_kw',
                            'tuple_kw',
                            'not_op',
                            'dict_kw',
                            'bool_true_kw',
                            'list_kw',
                            'none_kw',
                            'set_kw',
                            'unary_subtract_op',
                            'left_parenthesis_hz']:
                            expr = self._scan_rule('expr')  # noqa
                            # ```
                            slice_part3 = expr.res
                            # ```
            else:
                self._error(token_names=[
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'colon_hz'])
            # ```
            index_end_row, index_end_col = self._get_end_row_col()
            # ```
            subscript_end_kw = self._scan_rule('subscript_end_kw')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()

            if is_slice:
                ctx.par.res = Subscript(
                    value=ctx.par.res,
                    slice=Slice(
                        lower=slice_part1,
                        upper=slice_part2,
                        step=slice_part3,
                        lineno=index_start_row,
                        col_offset=index_start_col,
                        end_lineno=index_end_row,
                        end_col_offset=index_end_col,
                    ),
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
            else:
                ctx.par.res = Subscript(
                    value=ctx.par.res,
                    slice=Index(
                        value=slice_part1,
                        lineno=index_start_row,
                        col_offset=index_start_col,
                        end_lineno=index_end_row,
                        end_col_offset=index_end_col,
                    ),
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
            # ```
        elif self._peek(['decorate_kw'], is_branch=True):
            decorate_kw = self._scan_rule('decorate_kw')  # noqa
            # ```
            name_node = ctx.par.res

            if not isinstance(name_node, Name):
                token_index = getattr(name_node, 'token_index', None)

                if token_index is not None:
                    self._retract(token_index)

                self._error(msg='`打整一哈`的左手边必须是名字。')

            decorator_nodes = []

            has_args = False
            # ```
            if self._peek([
                'left_parenthesis_hz',
                'name',
                'async_func_start_kw',
                'class_start_kw',
                'func_start_kw'],
                is_required=True) == 'left_parenthesis_hz':
                args_list = self._scan_rule('args_list')  # noqa
                # ```
                has_args = True
                # ```
            # ```
            end_row, end_col = self._get_end_row_col()

            if has_args:
                decorator_node = Call(
                    func=name_node,
                    args=args_list.res.args,
                    keywords=args_list.res.kwargs,
                    lineno=name_node.lineno,
                    col_offset=name_node.col_offset,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )

                decorator_nodes.append(decorator_node)
            else:
                decorator_nodes.append(name_node)
            # ```
            while self._peek([
                'name',
                'async_func_start_kw',
                'class_start_kw',
                'func_start_kw'],
                is_required=True) == 'name':
                # ```
                has_args = False
                # ```
                name = self._scan_rule('name')  # noqa
                decorate_kw = self._scan_rule('decorate_kw')  # noqa
                # ```
                name_node = name.res
                # ```
                if self._peek([
                    'left_parenthesis_hz',
                    'name',
                    'async_func_start_kw',
                    'class_start_kw',
                    'func_start_kw'],
                    is_required=True) == 'left_parenthesis_hz':
                    args_list = self._scan_rule('args_list')  # noqa
                    # ```
                    has_args = True
                    # ```
                # ```
                end_row, end_col = self._get_end_row_col()

                if has_args:
                    decorator_node = Call(
                        func=name_node,
                        args=args_list.res.args,
                        keywords=args_list.res.kwargs,
                        lineno=name_node.lineno,
                        col_offset=name_node.col_offset,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    )

                    decorator_nodes.append(decorator_node)
                else:
                    decorator_nodes.append(name_node)
                # ```
            # ```
            ctx.decorator_nodes = decorator_nodes
            # ```
            if self._peek([
                'async_func_start_kw',
                'func_start_kw']):
                func_def = self._scan_rule('func_def')  # noqa
                # ```
                ctx.par.res = func_def.res
                # ```
            elif self._peek(['class_start_kw'], is_branch=True):
                class_def = self._scan_rule('class_def')  # noqa
                # ```
                ctx.par.res = class_def.res
                # ```
            else:
                self._error(token_names=[
                'async_func_start_kw',
                'class_start_kw',
                'func_start_kw'])
        elif self._peek([
            'any_trailer',
            'all_trailer',
            'hex_trailer',
            'extend_trailer',
            'ord_trailer',
            'bytearray_trailer',
            'bin_trailer',
            'oct_trailer',
            'str_trailer',
            'bytes_trailer',
            'max_trailer',
            'min_trailer',
            'format_trailer',
            'float_trailer',
            'opposite_trailer',
            'abs_trailer',
            'range_trailer',
            'reciprocal_trailer',
            'tuple_trailer',
            'type_trailer',
            'name_trailer',
            'append_trailer',
            'chr_trailer',
            'count_trailer',
            'sort_trailer',
            'int_trailer',
            'add_trailer',
            'clear_trailer',
            'dict_trailer',
            'bool_trailer',
            'list_trailer',
            'repr_trailer',
            'set_trailer',
            'len_trailer',
            'sum_trailer',
            'trailer_prefix'], is_branch=True):
            # ```
            node = ctx.par.res
            start_row = ctx.par.res.lineno
            start_col = ctx.par.res.col_offset
            # ```
            if self._peek([
                'any_trailer',
                'all_trailer',
                'hex_trailer',
                'ord_trailer',
                'bytearray_trailer',
                'bin_trailer',
                'oct_trailer',
                'str_trailer',
                'bytes_trailer',
                'max_trailer',
                'min_trailer',
                'float_trailer',
                'abs_trailer',
                'tuple_trailer',
                'type_trailer',
                'chr_trailer',
                'count_trailer',
                'int_trailer',
                'dict_trailer',
                'bool_trailer',
                'list_trailer',
                'repr_trailer',
                'set_trailer',
                'len_trailer',
                'sum_trailer',
                'trailer_prefix']):
                if self._peek(['trailer_prefix']):
                    trailer_prefix = self._scan_rule('trailer_prefix')  # noqa
                    # ```
                    self._retract()
                    self._error(msg='`嘞`是保留的关键字。')
                    # ```
                elif self._peek(['type_trailer'], is_branch=True):
                    type_trailer = self._scan_rule('type_trailer')  # noqa
                    # ```
                    func_name = 'type'
                    # ```
                elif self._peek(['len_trailer'], is_branch=True):
                    len_trailer = self._scan_rule('len_trailer')  # noqa
                    # ```
                    func_name = 'len'
                    # ```
                elif self._peek(['count_trailer'], is_branch=True):
                    count_trailer = self._scan_rule('count_trailer')  # noqa
                    # ```
                    func_name = 'len'
                    # ```
                elif self._peek(['abs_trailer'], is_branch=True):
                    abs_trailer = self._scan_rule('abs_trailer')  # noqa
                    # ```
                    func_name = 'abs'
                    # ```
                elif self._peek(['min_trailer'], is_branch=True):
                    min_trailer = self._scan_rule('min_trailer')  # noqa
                    # ```
                    func_name = 'min'
                    # ```
                elif self._peek(['max_trailer'], is_branch=True):
                    max_trailer = self._scan_rule('max_trailer')  # noqa
                    # ```
                    func_name = 'max'
                    # ```
                elif self._peek(['bool_trailer'], is_branch=True):
                    bool_trailer = self._scan_rule('bool_trailer')  # noqa
                    # ```
                    func_name = 'bool'
                    # ```
                elif self._peek(['int_trailer'], is_branch=True):
                    int_trailer = self._scan_rule('int_trailer')  # noqa
                    # ```
                    func_name = 'int'
                    # ```
                elif self._peek(['float_trailer'], is_branch=True):
                    float_trailer = self._scan_rule('float_trailer')  # noqa
                    # ```
                    func_name = 'float'
                    # ```
                elif self._peek(['str_trailer'], is_branch=True):
                    str_trailer = self._scan_rule('str_trailer')  # noqa
                    # ```
                    func_name = 'str'
                    # ```
                elif self._peek(['repr_trailer'], is_branch=True):
                    repr_trailer = self._scan_rule('repr_trailer')  # noqa
                    # ```
                    func_name = 'repr'
                    # ```
                elif self._peek(['bytes_trailer'], is_branch=True):
                    bytes_trailer = self._scan_rule('bytes_trailer')  # noqa
                    # ```
                    func_name = 'bytes'
                    # ```
                elif self._peek(['bytearray_trailer'], is_branch=True):
                    bytearray_trailer = self._scan_rule('bytearray_trailer')  # noqa
                    # ```
                    func_name = 'bytearray'
                    # ```
                elif self._peek(['chr_trailer'], is_branch=True):
                    chr_trailer = self._scan_rule('chr_trailer')  # noqa
                    # ```
                    func_name = 'chr'
                    # ```
                elif self._peek(['ord_trailer'], is_branch=True):
                    ord_trailer = self._scan_rule('ord_trailer')  # noqa
                    # ```
                    func_name = 'ord'
                    # ```
                elif self._peek(['hex_trailer'], is_branch=True):
                    hex_trailer = self._scan_rule('hex_trailer')  # noqa
                    # ```
                    func_name = 'hex'
                    # ```
                elif self._peek(['oct_trailer'], is_branch=True):
                    oct_trailer = self._scan_rule('oct_trailer')  # noqa
                    # ```
                    func_name = 'oct'
                    # ```
                elif self._peek(['bin_trailer'], is_branch=True):
                    bin_trailer = self._scan_rule('bin_trailer')  # noqa
                    # ```
                    func_name = 'bin'
                    # ```
                elif self._peek(['sum_trailer'], is_branch=True):
                    sum_trailer = self._scan_rule('sum_trailer')  # noqa
                    # ```
                    func_name = 'sum'
                    # ```
                elif self._peek(['any_trailer'], is_branch=True):
                    any_trailer = self._scan_rule('any_trailer')  # noqa
                    # ```
                    func_name = 'any'
                    # ```
                elif self._peek(['all_trailer'], is_branch=True):
                    all_trailer = self._scan_rule('all_trailer')  # noqa
                    # ```
                    func_name = 'all'
                    # ```
                elif self._peek(['list_trailer'], is_branch=True):
                    list_trailer = self._scan_rule('list_trailer')  # noqa
                    # ```
                    func_name = 'list'
                    # ```
                elif self._peek(['tuple_trailer'], is_branch=True):
                    tuple_trailer = self._scan_rule('tuple_trailer')  # noqa
                    # ```
                    func_name = 'tuple'
                    # ```
                elif self._peek(['dict_trailer'], is_branch=True):
                    dict_trailer = self._scan_rule('dict_trailer')  # noqa
                    # ```
                    func_name = 'dict'
                    # ```
                elif self._peek(['set_trailer'], is_branch=True):
                    set_trailer = self._scan_rule('set_trailer')  # noqa
                    # ```
                    func_name = 'set'
                    # ```
                else:
                    self._error(token_names=[
                    'any_trailer',
                    'all_trailer',
                    'hex_trailer',
                    'ord_trailer',
                    'bytearray_trailer',
                    'bin_trailer',
                    'oct_trailer',
                    'str_trailer',
                    'bytes_trailer',
                    'max_trailer',
                    'min_trailer',
                    'float_trailer',
                    'abs_trailer',
                    'tuple_trailer',
                    'type_trailer',
                    'chr_trailer',
                    'count_trailer',
                    'int_trailer',
                    'dict_trailer',
                    'bool_trailer',
                    'list_trailer',
                    'repr_trailer',
                    'set_trailer',
                    'len_trailer',
                    'sum_trailer',
                    'trailer_prefix'])
                # ```
                end_row, end_col = self._get_end_row_col()
                func_name_node = Name(
                    id=func_name,
                    ctx=Load(),
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                node = Call(
                    func=func_name_node,
                    args=[node],
                    keywords=[],
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek(['opposite_trailer'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                opposite_trailer = self._scan_rule('opposite_trailer')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                node = UnaryOp(
                    op=USub(
                        lineno=op_start_row,
                        col_offset=op_start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    ),
                    operand=node,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek(['reciprocal_trailer'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                reciprocal_trailer = self._scan_rule('reciprocal_trailer')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                node = BinOp(
                    left=Num(
                        1,
                        kind=None,
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        end_lineno=node.end_lineno,
                        end_col_offset=node.end_col_offset,
                    ),
                    op=Div(
                        lineno=op_start_row,
                        col_offset=op_start_col,
                        end_lineno=end_row,
                        end_col_offset=end_col,
                    ),
                    right=node,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek(['range_trailer'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                range_trailer = self._scan_rule('range_trailer')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                func_name_node = Name(
                    id='range',
                    ctx=Load(),
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                node = Call(
                    func=func_name_node,
                    args=node.elts if isinstance(node, Tuple) else [node],
                    keywords=[],
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek([
                'extend_trailer',
                'format_trailer',
                'append_trailer',
                'sort_trailer',
                'add_trailer',
                'clear_trailer'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                if self._peek(['format_trailer']):
                    format_trailer = self._scan_rule('format_trailer')  # noqa
                    # ```
                    attr_name = 'format'
                    # ```
                elif self._peek(['add_trailer'], is_branch=True):
                    add_trailer = self._scan_rule('add_trailer')  # noqa
                    # ```
                    attr_name = 'add'
                    # ```
                elif self._peek(['append_trailer'], is_branch=True):
                    append_trailer = self._scan_rule('append_trailer')  # noqa
                    # ```
                    attr_name = 'append'
                    # ```
                elif self._peek(['extend_trailer'], is_branch=True):
                    extend_trailer = self._scan_rule('extend_trailer')  # noqa
                    # ```
                    attr_name = 'extend'
                    # ```
                elif self._peek(['clear_trailer'], is_branch=True):
                    clear_trailer = self._scan_rule('clear_trailer')  # noqa
                    # ```
                    attr_name = 'clear'
                    # ```
                elif self._peek(['sort_trailer'], is_branch=True):
                    sort_trailer = self._scan_rule('sort_trailer')  # noqa
                    # ```
                    attr_name = 'sort'
                    # ```
                else:
                    self._error(token_names=[
                    'extend_trailer',
                    'format_trailer',
                    'append_trailer',
                    'sort_trailer',
                    'add_trailer',
                    'clear_trailer'])
                # ```
                op_end_row, op_end_col = self._get_end_row_col()
                # ```
                args_list = self._scan_rule('args_list')  # noqa
                # ```
                end_row, end_col = self._get_end_row_col()
                attr_node = Attribute(
                    value=node,
                    attr=attr_name,
                    ctx=Load(),
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                )
                node = Call(
                    func=attr_node,
                    args=args_list.res.args,
                    keywords=args_list.res.kwargs,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
                # ```
            elif self._peek(['name_trailer'], is_branch=True):
                # ```
                op_start_row, op_start_col = self._get_start_row_col()
                # ```
                name_trailer = self._scan_rule('name_trailer')  # noqa
                # ```
                attr_name = '__name__'
                # ```
                # ```
                op_end_row, op_end_col = self._get_end_row_col()
                # ```
                # ```
                end_row, end_col = self._get_end_row_col()
                node = Attribute(
                    value=node,
                    attr=attr_name,
                    ctx=Load(),
                    lineno=op_start_row,
                    col_offset=op_start_col,
                    end_lineno=op_end_row,
                    end_col_offset=op_end_col,
                )
                # ```
            else:
                self._error(token_names=[
                'any_trailer',
                'all_trailer',
                'hex_trailer',
                'extend_trailer',
                'ord_trailer',
                'bytearray_trailer',
                'bin_trailer',
                'oct_trailer',
                'str_trailer',
                'bytes_trailer',
                'max_trailer',
                'min_trailer',
                'format_trailer',
                'float_trailer',
                'opposite_trailer',
                'abs_trailer',
                'range_trailer',
                'reciprocal_trailer',
                'tuple_trailer',
                'type_trailer',
                'name_trailer',
                'append_trailer',
                'chr_trailer',
                'count_trailer',
                'sort_trailer',
                'int_trailer',
                'add_trailer',
                'clear_trailer',
                'dict_trailer',
                'bool_trailer',
                'list_trailer',
                'repr_trailer',
                'set_trailer',
                'len_trailer',
                'sum_trailer',
                'trailer_prefix'])
            # ```
            ctx.par.res = node
            # ```
        else:
            self._error(token_names=[
            'any_trailer',
            'all_trailer',
            'hex_trailer',
            'extend_trailer',
            'ord_trailer',
            'bytearray_trailer',
            'bin_trailer',
            'oct_trailer',
            'str_trailer',
            'bytes_trailer',
            'max_trailer',
            'min_trailer',
            'format_trailer',
            'float_trailer',
            'opposite_trailer',
            'abs_trailer',
            'range_trailer',
            'decorate_kw',
            'reciprocal_trailer',
            'tuple_trailer',
            'type_trailer',
            'name_trailer',
            'append_trailer',
            'chr_trailer',
            'count_trailer',
            'sort_trailer',
            'int_trailer',
            'add_trailer',
            'clear_trailer',
            'dict_trailer',
            'bool_trailer',
            'list_trailer',
            'repr_trailer',
            'set_trailer',
            'len_trailer',
            'nonlocal_kw',
            'global_kw',
            'sum_trailer',
            'dot_kw',
            'trailer_prefix',
            'subscript_start_kw',
            'left_parenthesis_hz'])

    def compound_stmt(self, ctx):
        if self._peek(['if_kw']):
            if_stmt = self._scan_rule('if_stmt')  # noqa
            # ```
            ctx.res = if_stmt.res
            # ```
        elif self._peek(['loop_always_kw'], is_branch=True):
            loop_always_stmt = self._scan_rule('loop_always_stmt')  # noqa
            # ```
            ctx.res = loop_always_stmt.res
            # ```
        elif self._peek(['loop_if_kw'], is_branch=True):
            loop_if_stmt = self._scan_rule('loop_if_stmt')  # noqa
            # ```
            ctx.res = loop_if_stmt.res
            # ```
        elif self._peek(['loop_until_kw'], is_branch=True):
            loop_until_stmt = self._scan_rule('loop_until_stmt')  # noqa
            # ```
            ctx.res = loop_until_stmt.res
            # ```
        elif self._peek([
            'async_loop_iterator_kw',
            'loop_iterator_kw'], is_branch=True):
            loop_iterator_stmt = self._scan_rule('loop_iterator_stmt')  # noqa
            # ```
            ctx.res = loop_iterator_stmt.res
            # ```
        elif self._peek(['try_kw'], is_branch=True):
            try_stmt = self._scan_rule('try_stmt')  # noqa
            # ```
            ctx.res = try_stmt.res
            # ```
        elif self._peek([
            'async_with_kw',
            'with_kw'], is_branch=True):
            with_stmt = self._scan_rule('with_stmt')  # noqa
            # ```
            ctx.res = with_stmt.res
            # ```
        elif self._peek([
            'async_func_start_kw',
            'func_start_kw'], is_branch=True):
            func_def = self._scan_rule('func_def')  # noqa
            # ```
            ctx.res = func_def.res
            # ```
        elif self._peek(['class_start_kw'], is_branch=True):
            class_def = self._scan_rule('class_def')  # noqa
            # ```
            ctx.res = class_def.res
            # ```
        else:
            self._error(token_names=[
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'loop_iterator_kw',
            'with_kw',
            'loop_always_kw',
            'try_kw',
            'async_func_start_kw',
            'class_start_kw',
            'if_kw',
            'func_start_kw'])

    def if_stmt(self, ctx):
        # ```
        stack = []
        start_row, start_col = self._get_start_row_col()
        # ```
        if_kw = self._scan_rule('if_kw')  # noqa
        expr = self._scan_rule('expr')  # noqa
        # ```
        test_expr = expr.res
        # ```
        if self._peek([
            'block_start_kw',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'elif_kw',
            'block_end_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) == 'block_start_kw':
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        if_stmts = stmts.res or [Pass(
            lineno=body_start_row,
            col_offset=body_start_col,
            end_lineno=body_start_row,
            end_col_offset=body_start_col,
        )]
        stack.append(
            (test_expr, if_stmts, start_row, start_col, end_row, end_col)
        )
        # ```
        while self._peek([
            'elif_kw',
            'block_end_kw',
            'else_kw'],
            is_required=True) == 'elif_kw':
            # ```
            start_row, start_col = self._get_start_row_col()
            # ```
            elif_kw = self._scan_rule('elif_kw')  # noqa
            expr = self._scan_rule('expr')  # noqa
            # ```
            test_expr = expr.res
            # ```
            if self._peek([
                'block_start_kw',
                'number',
                'string',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'pass_kw',
                'bit_invert_op',
                'break_kw',
                'tuple_with_kw',
                'elif_kw',
                'block_end_kw',
                'loop_iterator_kw',
                'continue_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'async_func_start_kw',
                'del_kw',
                'bool_false_kw',
                'tuple_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'return_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'],
                is_required=True) == 'block_start_kw':
                block_start_kw = self._scan_rule('block_start_kw')  # noqa
            # ```
            body_start_row, body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            if_stmts = stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )]
            stack.append(
                (test_expr, if_stmts, start_row, start_col, end_row, end_col)
            )
            # ```
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            if self._peek([
                'block_start_kw',
                'number',
                'string',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'pass_kw',
                'bit_invert_op',
                'break_kw',
                'tuple_with_kw',
                'block_end_kw',
                'loop_iterator_kw',
                'continue_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'yield_kw',
                'try_kw',
                'async_func_start_kw',
                'del_kw',
                'bool_false_kw',
                'tuple_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'return_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'],
                is_required=True) == 'block_start_kw':
                block_start_kw = self._scan_rule('block_start_kw')  # noqa
            # ```
            body_start_row, body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        if else_stmts is None:
            else_stmts = []
        while stack:
            test_expr, if_stmts, start_row, start_col, end_row, end_col\
                = stack.pop()

            else_stmts = [
                If(
                    test=test_expr,
                    body=if_stmts,
                    orelse=else_stmts,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
            ]

        ctx.res = else_stmts[0]
        # ```

    def loop_always_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        loop_always_kw = self._scan_rule('loop_always_kw')  # noqa
        # ```
        test_start_row, test_start_col = self._get_start_row_col()
        # ```
        if self._peek([
            'block_start_kw',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'block_end_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) == 'block_start_kw':
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            # ```
            else_body_start_row, else_body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                lineno=else_body_start_row,
                col_offset=else_body_start_col,
                end_lineno=else_body_start_row,
                end_col_offset=else_body_start_col,
            )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = While(
            test=NameConstant(
                value=True,
                kind=None,
                lineno=test_start_row,
                col_offset=test_start_col,
                end_lineno=test_start_row,
                end_col_offset=test_start_col,
            ),
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            orelse=[] if else_stmts is None else else_stmts,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def loop_if_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        loop_if_kw = self._scan_rule('loop_if_kw')  # noqa
        expr = self._scan_rule('expr')  # noqa
        if self._peek([
            'block_start_kw',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'block_end_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) == 'block_start_kw':
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            # ```
            else_body_start_row, else_body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                        lineno=else_body_start_row,
                        col_offset=else_body_start_col,
                        end_lineno=else_body_start_row,
                        end_col_offset=else_body_start_col,
                    )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = While(
            test=expr.res,
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            orelse=[] if else_stmts is None else else_stmts,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def loop_until_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        loop_until_kw = self._scan_rule('loop_until_kw')  # noqa
        expr = self._scan_rule('expr')  # noqa
        if self._peek([
            'block_start_kw',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'block_end_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'else_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) == 'block_start_kw':
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            # ```
            else_body_start_row, else_body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                        lineno=else_body_start_row,
                        col_offset=else_body_start_col,
                        end_lineno=else_body_start_row,
                        end_col_offset=else_body_start_col,
                    )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        ctx.res = While(
            test=UnaryOp(
                op=Not(
                    lineno=expr.res.lineno,
                    col_offset=expr.res.col_offset,
                    end_lineno=expr.res.lineno,
                    end_col_offset=expr.res.col_offset,
                ),
                operand=expr.res,
                lineno=expr.res.lineno,
                col_offset=expr.res.col_offset,
                end_lineno=expr.res.end_lineno,
                end_col_offset=expr.res.end_col_offset,
            ),
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            orelse=[] if else_stmts is None else else_stmts,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def loop_iterator_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['loop_iterator_kw']):
            loop_iterator_kw = self._scan_rule('loop_iterator_kw')  # noqa
            # ```
            is_async = False
            # ```
        elif self._peek(['async_loop_iterator_kw'], is_branch=True):
            async_loop_iterator_kw = self._scan_rule('async_loop_iterator_kw')  # noqa
            # ```
            is_async = True
            # ```
        else:
            self._error(token_names=[
            'async_loop_iterator_kw',
            'loop_iterator_kw'])
        expr = self._scan_rule('expr')  # noqa
        # ```
        iterator_expr = expr.res
        # ```
        loop_iterator_item_as_name_kw = self._scan_rule('loop_iterator_item_as_name_kw')  # noqa
        loop_iterator_names_list = self._scan_rule('loop_iterator_names_list')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            # ```
            else_body_start_row, else_body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                        lineno=else_body_start_row,
                        col_offset=else_body_start_col,
                        end_lineno=else_body_start_row,
                        end_col_offset=else_body_start_col,
                    )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()

        var_name_nodes = loop_iterator_names_list.res

        for var_name_node in var_name_nodes:
            var_name_node.ctx = Store()

        if len(var_name_nodes) == 1:
            target = var_name_nodes[0]
        else:
            target = Tuple(
                elts=var_name_nodes,
                ctx=Store(),
                lineno=var_name_nodes[0].lineno,
                col_offset=var_name_nodes[0].col_offset,
                end_lineno=var_name_nodes[-1].end_lineno,
                end_col_offset=var_name_nodes[-1].end_col_offset,
            )

        ctx.res = (AsyncFor if is_async else For)(
            target=target,
            iter=iterator_expr,
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            orelse=[] if else_stmts is None else else_stmts,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def loop_iterator_names_list(self, ctx):
        # ```
        # Used in child `loop_iterator_names_list_item`.
        ctx.res = []
        # ```
        loop_iterator_names_list_item = self._scan_rule('loop_iterator_names_list_item')  # noqa

    def loop_iterator_names_list_item(self, ctx):
        # ```
        # Used in child `loop_iterator_names_list_item`.
        ctx.res = ctx.par.res
        # ```
        name = self._scan_rule('name')  # noqa
        # ```
        ctx.res.append(name.res)
        # ```
        if self._peek(['block_start_kw']):
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        elif self._peek(['pause_hz'], is_branch=True):
            pause_hz = self._scan_rule('pause_hz')  # noqa
            loop_iterator_names_list_item = self._scan_rule('loop_iterator_names_list_item')  # noqa
        else:
            self._error(token_names=[
            'block_start_kw',
            'pause_hz'])

    def try_stmt(self, ctx):
        # ```
        finally_stmts = None
        handlers = []
        start_row, start_col = self._get_start_row_col()
        # ```
        try_kw = self._scan_rule('try_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        # ```
        try_stmts = stmts.res or [Pass(
            lineno=body_start_row,
            col_offset=body_start_col,
            end_lineno=body_start_row,
            end_col_offset=body_start_col,
        )]
        try_stmts_post_token_index = self._get_token_index()
        # ```
        while self._peek([
            'except_kw',
            'block_end_kw',
            'finally_kw',
            'else_kw'],
            is_required=True) == 'except_kw':
            # ```
            exc_type = None
            exc_var_name = None
            except_start_row, except_start_col = self._get_start_row_col()
            # ```
            except_kw = self._scan_rule('except_kw')  # noqa
            if self._peek([
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'pass_kw',
                'break_kw',
                'block_end_kw',
                'except_kw',
                'loop_iterator_kw',
                'continue_kw',
                'finally_kw',
                'with_kw',
                'assert_kw',
                'await_kw',
                'loop_always_kw',
                'else_kw',
                'yield_kw',
                'try_kw',
                'async_func_start_kw',
                'del_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'print_kw',
                'raise_kw',
                'return_kw',
                'func_start_kw'],
                is_required=True) in [
                'number',
                'string',
                'name',
                'bit_invert_op',
                'tuple_with_kw',
                'dict_with_kw',
                'list_with_kw',
                'set_with_kw',
                'bool_false_kw',
                'tuple_kw',
                'not_op',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'unary_subtract_op',
                'left_parenthesis_hz']:
                expr = self._scan_rule('expr')  # noqa
                # ```
                exc_type = expr.res
                # ```
                if self._peek([
                    'as_kw',
                    'number',
                    'string',
                    'async_with_kw',
                    'async_loop_iterator_kw',
                    'loop_until_kw',
                    'loop_if_kw',
                    'yield_from_kw',
                    'name',
                    'pass_kw',
                    'bit_invert_op',
                    'break_kw',
                    'tuple_with_kw',
                    'block_end_kw',
                    'except_kw',
                    'loop_iterator_kw',
                    'continue_kw',
                    'finally_kw',
                    'with_kw',
                    'dict_with_kw',
                    'assert_kw',
                    'await_kw',
                    'list_with_kw',
                    'loop_always_kw',
                    'set_with_kw',
                    'else_kw',
                    'yield_kw',
                    'try_kw',
                    'async_func_start_kw',
                    'del_kw',
                    'bool_false_kw',
                    'tuple_kw',
                    'class_start_kw',
                    'exit_kw',
                    'if_kw',
                    'not_op',
                    'print_kw',
                    'raise_kw',
                    'return_kw',
                    'dict_kw',
                    'bool_true_kw',
                    'list_kw',
                    'none_kw',
                    'set_kw',
                    'func_start_kw',
                    'unary_subtract_op',
                    'left_parenthesis_hz'],
                    is_required=True) == 'as_kw':
                    as_kw = self._scan_rule('as_kw')  # noqa
                    name = self._scan_rule('name')  # noqa
                    # ```
                    exc_var_name = name.res.id
                    # ```
                if self._peek([
                    'block_end_kw',
                    'number',
                    'string',
                    'async_with_kw',
                    'async_loop_iterator_kw',
                    'loop_until_kw',
                    'loop_if_kw',
                    'yield_from_kw',
                    'name',
                    'pass_kw',
                    'bit_invert_op',
                    'break_kw',
                    'tuple_with_kw',
                    'except_kw',
                    'loop_iterator_kw',
                    'continue_kw',
                    'finally_kw',
                    'with_kw',
                    'dict_with_kw',
                    'assert_kw',
                    'await_kw',
                    'list_with_kw',
                    'loop_always_kw',
                    'set_with_kw',
                    'else_kw',
                    'yield_kw',
                    'try_kw',
                    'async_func_start_kw',
                    'del_kw',
                    'bool_false_kw',
                    'tuple_kw',
                    'class_start_kw',
                    'exit_kw',
                    'if_kw',
                    'not_op',
                    'print_kw',
                    'raise_kw',
                    'return_kw',
                    'dict_kw',
                    'bool_true_kw',
                    'list_kw',
                    'none_kw',
                    'set_kw',
                    'func_start_kw',
                    'unary_subtract_op',
                    'left_parenthesis_hz'],
                    is_required=True) == 'block_end_kw':
                    block_end_kw = self._scan_rule('block_end_kw')  # noqa
            # ```
            body_start_row, body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            end_row, end_col = self._get_end_row_col()
            handlers.append(
                ExceptHandler(
                    type=exc_type,
                    name=exc_var_name,
                    body=stmts.res or [Pass(
                        lineno=body_start_row,
                        col_offset=body_start_col,
                        end_lineno=body_start_row,
                        end_col_offset=body_start_col,
                    )],
                    lineno=except_start_row,
                    col_offset=except_start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
            )
            # ```
        # ```
        else_stmts = None
        # ```
        if self._peek([
            'else_kw',
            'block_end_kw',
            'finally_kw'],
            is_required=True) == 'else_kw':
            else_kw = self._scan_rule('else_kw')  # noqa
            if self._peek([
                'block_start_kw',
                'number',
                'string',
                'async_with_kw',
                'async_loop_iterator_kw',
                'loop_until_kw',
                'loop_if_kw',
                'yield_from_kw',
                'name',
                'pass_kw',
                'bit_invert_op',
                'break_kw',
                'tuple_with_kw',
                'block_end_kw',
                'loop_iterator_kw',
                'continue_kw',
                'finally_kw',
                'with_kw',
                'dict_with_kw',
                'assert_kw',
                'await_kw',
                'list_with_kw',
                'loop_always_kw',
                'set_with_kw',
                'yield_kw',
                'try_kw',
                'async_func_start_kw',
                'del_kw',
                'bool_false_kw',
                'tuple_kw',
                'class_start_kw',
                'exit_kw',
                'if_kw',
                'not_op',
                'print_kw',
                'raise_kw',
                'return_kw',
                'dict_kw',
                'bool_true_kw',
                'list_kw',
                'none_kw',
                'set_kw',
                'func_start_kw',
                'unary_subtract_op',
                'left_parenthesis_hz'],
                is_required=True) == 'block_start_kw':
                block_start_kw = self._scan_rule('block_start_kw')  # noqa
            # ```
            body_start_row, body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            else_stmts = stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )]
            # ```
        # ```
        finally_stmts = None
        # ```
        if self._peek([
            'finally_kw',
            'block_end_kw'],
            is_required=True) == 'finally_kw':
            finally_kw = self._scan_rule('finally_kw')  # noqa
            # ```
            body_start_row, body_start_col = self._get_start_row_col()
            # ```
            stmts = self._scan_rule('stmts')  # noqa
            # ```
            finally_stmts = stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )]
            # ```
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        if not handlers and finally_stmts is None:
            self._retract(try_stmts_post_token_index)
            self._error(msg='必须至少有一个`抓一哈`或`最后才`。\n')

        end_row, end_col = self._get_end_row_col()

        ctx.res = Try(
            body=try_stmts,
            handlers=handlers,
            orelse=[] if else_stmts is None else else_stmts,
            finalbody=[] if finally_stmts is None else finally_stmts,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def with_stmt(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['with_kw']):
            with_kw = self._scan_rule('with_kw')  # noqa
            # ```
            is_async = False
            # ```
        elif self._peek(['async_with_kw'], is_branch=True):
            async_with_kw = self._scan_rule('async_with_kw')  # noqa
            # ```
            is_async = True
            # ```
        else:
            self._error(token_names=[
            'async_with_kw',
            'with_kw'])
        with_values_list = self._scan_rule('with_values_list')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        block_end_kw = self._scan_rule('block_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        with_items = []
        for value_expr, name_expr in with_values_list.res:
            end_expr = name_expr if name_expr is not None else value_expr
            with_item = withitem(
                context_expr=value_expr,
                optional_vars=name_expr,
                lineno=value_expr.lineno,
                col_offset=value_expr.col_offset,
                end_lineno=end_expr.end_lineno,
                end_col_offset=end_expr.end_col_offset,
            )
            with_items.append(with_item)

        ctx.res = (AsyncWith if is_async else With)(
            items=with_items,
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def with_values_list(self, ctx):
        # ```
        # Used in child `with_values_list_item`.
        ctx.res = []
        # ```
        with_values_list_item = self._scan_rule('with_values_list_item')  # noqa

    def with_values_list_item(self, ctx):
        # ```
        # Used in child `with_values_list_item`.
        ctx.res = ctx.par.res
        # ```
        expr = self._scan_rule('expr')  # noqa
        # ```
        name_node = None
        # ```
        if self._peek([
            'as_kw',
            'block_start_kw',
            'pause_hz'],
            is_required=True) == 'as_kw':
            as_kw = self._scan_rule('as_kw')  # noqa
            name = self._scan_rule('name')  # noqa
            # ```
            name_node = name.res
            name_node.ctx = Store()
            # ```
        # ```
        ctx.res.append((expr.res, name_node))
        # ```
        if self._peek(['block_start_kw']):
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        elif self._peek(['pause_hz'], is_branch=True):
            pause_hz = self._scan_rule('pause_hz')  # noqa
            with_values_list_item = self._scan_rule('with_values_list_item')  # noqa
        else:
            self._error(token_names=[
            'block_start_kw',
            'pause_hz'])

    def func_def(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek(['func_start_kw']):
            func_start_kw = self._scan_rule('func_start_kw')  # noqa
            # ```
            is_async = False
            # ```
        elif self._peek(['async_func_start_kw'], is_branch=True):
            async_func_start_kw = self._scan_rule('async_func_start_kw')  # noqa
            # ```
            is_async = True
            # ```
        else:
            self._error(token_names=[
            'async_func_start_kw',
            'func_start_kw'])
        name = self._scan_rule('name')  # noqa
        # ```
        params_start_row, params_start_col = self._get_start_row_col()
        # ```
        params_list = self._scan_rule('params_list')  # noqa
        # ```
        params_end_row, params_end_col = self._get_end_row_col()
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        func_end_kw = self._scan_rule('func_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()

        decorator_list = self._get_ctx_attr(ctx.par, 'decorator_nodes')

        ctx.res = (AsyncFunctionDef if is_async else FunctionDef)(
            name=name.res.id,
            args=arguments(
                args=params_list.res.args,
                vararg=params_list.res.collect_args_node,
                posonlyargs=[],
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=params_list.res.collect_kwargs_node,
                defaults=params_list.res.defaults,
                lineno=params_start_row,
                col_offset=params_start_col,
                end_lineno=params_end_row,
                end_col_offset=params_end_col,
            ),
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            decorator_list=[] if decorator_list is None else decorator_list,
            returns=None,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```

    def params_list(self, ctx):
        # ```
        # Used in child `params_list_item`.
        ctx.res = AttrDict()
        ctx.res.args = []
        ctx.res.kwargs = []
        ctx.res.defaults = []
        ctx.res.collect_args_node = None
        ctx.res.collect_kwargs_node = None
        # ```
        left_parenthesis_hz = self._scan_rule('left_parenthesis_hz')  # noqa
        if self._peek(['right_parenthesis_hz']):
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
        elif self._peek([
            'name',
            'collect_kwargs_kw',
            'collect_args_kw'], is_branch=True):
            params_list_item = self._scan_rule('params_list_item')  # noqa
        else:
            self._error(token_names=[
            'name',
            'collect_kwargs_kw',
            'collect_args_kw',
            'right_parenthesis_hz'])

    def params_list_item(self, ctx):
        # ```
        # Used in child `params_list_item`
        ctx.res = ctx.par.res
        collect_mode = None
        start_row, start_col = self._get_start_row_col()
        # ```
        if self._peek([
            'collect_kwargs_kw',
            'collect_args_kw',
            'name'],
            is_required=True) in [
            'collect_kwargs_kw',
            'collect_args_kw']:
            if self._peek(['collect_args_kw']):
                collect_args_kw = self._scan_rule('collect_args_kw')  # noqa
                # ```
                if self._get_ctx_attr(ctx.par, 'is_class_def'):
                    self._retract()
                    self._error(msg='`名堂`不能用`收拢`参数。')

                if ctx.res.collect_args_node is not None:
                    self._retract()
                    self._error(msg='`收拢`不能用第二次。')

                if ctx.res.collect_kwargs_node is not None:
                    self._retract()
                    self._error(msg='`收拢`不能在`收拢来`之后。')

                collect_mode = 1
                # ```
            elif self._peek(['collect_kwargs_kw'], is_branch=True):
                collect_kwargs_kw = self._scan_rule('collect_kwargs_kw')  # noqa
                # ```
                if self._get_ctx_attr(ctx.par, 'is_class_def'):
                    self._retract()
                    self._error(msg='`名堂`不能用`收拢来`参数。')

                if ctx.res.collect_kwargs_node is not None:
                    self._retract()
                    self._error(msg='`收拢来`不能用第二次。')

                collect_mode = 2
                # ```
            else:
                self._error(token_names=[
                'collect_kwargs_kw',
                'collect_args_kw'])
        name = self._scan_rule('name')  # noqa
        # ```
        if not collect_mode and ctx.res.collect_args_node is not None:
            self._retract()
            self._error(msg='普通参数不能出现在`收拢`之后。')

        if not collect_mode and ctx.res.collect_kwargs_node is not None:
            self._retract()
            self._error(msg='普通参数不能出现在`收拢来`之后。')

        has_default = False
        # ```
        if self._peek([
            'assign_op',
            'right_parenthesis_hz',
            'comma_hz'],
            is_required=True) == 'assign_op':
            assign_op = self._scan_rule('assign_op')  # noqa
            # ```
            if collect_mode == 1:
                self._retract()
                self._error(msg='`收拢`参数不能有默认值。')
            elif collect_mode == 2:
                self._retract()
                self._error(msg='`收拢来`参数不能有默认值。')
            # ```
            cond_expr = self._scan_rule('cond_expr')  # noqa
            # ```
            has_default = True
            ctx.res.defaults.append(cond_expr.res)
            # ```
        # ```
        end_row, end_col = self._get_end_row_col()

        if collect_mode == 1:
            node = arg(
                arg=name.res.id,
                annotation=None,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.res.collect_args_node = node
        elif collect_mode == 2:
            node = arg(
                arg=name.res.id,
                annotation=None,
                lineno=start_row,
                col_offset=start_col,
                end_lineno=end_row,
                end_col_offset=end_col,
            )
            ctx.res.collect_kwargs_node = node
        else:
            if not has_default and ctx.res.defaults:
                self._retract()
                self._error(msg='无默认值参数不能出现在有默认值参数之后。')

            ctx.res.args.append(
                arg(
                    arg=name.res.id,
                    annotation=None,
                    lineno=start_row,
                    col_offset=start_col,
                    end_lineno=end_row,
                    end_col_offset=end_col,
                )
            )
        # ```
        if self._peek(['right_parenthesis_hz']):
            right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
        elif self._peek(['comma_hz'], is_branch=True):
            comma_hz = self._scan_rule('comma_hz')  # noqa
            if self._peek(['right_parenthesis_hz']):
                right_parenthesis_hz = self._scan_rule('right_parenthesis_hz')  # noqa
            elif self._peek([
                'name',
                'collect_kwargs_kw',
                'collect_args_kw'], is_branch=True):
                params_list_item = self._scan_rule('params_list_item')  # noqa
            else:
                self._error(token_names=[
                'name',
                'collect_kwargs_kw',
                'collect_args_kw',
                'right_parenthesis_hz'])
        else:
            self._error(token_names=[
            'right_parenthesis_hz',
            'comma_hz'])

    def class_def(self, ctx):
        # ```
        start_row, start_col = self._get_start_row_col()
        # ```
        class_start_kw = self._scan_rule('class_start_kw')  # noqa
        name = self._scan_rule('name')  # noqa
        # ```
        ctx.is_class_def = True
        # ```
        params_list = self._scan_rule('params_list')  # noqa
        if self._peek([
            'block_start_kw',
            'number',
            'string',
            'async_with_kw',
            'async_loop_iterator_kw',
            'loop_until_kw',
            'loop_if_kw',
            'yield_from_kw',
            'name',
            'pass_kw',
            'bit_invert_op',
            'break_kw',
            'tuple_with_kw',
            'class_end_kw',
            'loop_iterator_kw',
            'continue_kw',
            'with_kw',
            'dict_with_kw',
            'assert_kw',
            'await_kw',
            'list_with_kw',
            'loop_always_kw',
            'set_with_kw',
            'yield_kw',
            'try_kw',
            'async_func_start_kw',
            'del_kw',
            'bool_false_kw',
            'tuple_kw',
            'class_start_kw',
            'exit_kw',
            'if_kw',
            'not_op',
            'print_kw',
            'raise_kw',
            'return_kw',
            'dict_kw',
            'bool_true_kw',
            'list_kw',
            'none_kw',
            'set_kw',
            'func_start_kw',
            'unary_subtract_op',
            'left_parenthesis_hz'],
            is_required=True) == 'block_start_kw':
            block_start_kw = self._scan_rule('block_start_kw')  # noqa
        # ```
        body_start_row, body_start_col = self._get_start_row_col()
        # ```
        stmts = self._scan_rule('stmts')  # noqa
        class_end_kw = self._scan_rule('class_end_kw')  # noqa
        # ```
        end_row, end_col = self._get_end_row_col()
        kwd_args_count = len(params_list.res.defaults)
        if kwd_args_count == 0:
            pos_args = params_list.res.args
            kwd_args = []
        else:
            pos_args = params_list.res.args[:-kwd_args_count]
            kwd_args = params_list.res.args[-kwd_args_count:]
        base_name_nodes = [
            Name(
                id=pos_arg.arg,
                ctx=Load(),
                lineno=pos_arg.lineno,
                col_offset=pos_arg.col_offset,
                end_lineno=pos_arg.end_lineno,
                end_col_offset=pos_arg.end_col_offset,
            ) for pos_arg in pos_args
        ]
        keywords = [
            keyword(
                arg=kwd_arg.arg,
                value=params_list.res.defaults[i],
                lineno=kwd_arg.lineno,
                col_offset=kwd_arg.col_offset,
                end_lineno=kwd_arg.end_lineno,
                end_col_offset=kwd_arg.end_col_offset,
            ) for i, kwd_arg in enumerate(kwd_args)
        ]
        decorator_list = self._get_ctx_attr(ctx.par, 'decorator_nodes')
        ctx.res = ClassDef(
            name=name.res.id,
            bases=base_name_nodes,
            keywords=keywords,
            body=stmts.res or [Pass(
                lineno=body_start_row,
                col_offset=body_start_col,
                end_lineno=body_start_row,
                end_col_offset=body_start_col,
            )],
            decorator_list=[] if decorator_list is None else decorator_list,
            lineno=start_row,
            col_offset=start_col,
            end_lineno=end_row,
            end_col_offset=end_col,
        )
        # ```


def parse(txt, rule=None, debug=False):
    parser = Parser(
        txt=txt,
        debug=debug,
    )

    if rule is None:
        rule = 'source_code'

    parsing_result = None

    exc_info = None

    try:
        parser._make_tokens()

        parsing_result = parser._scan_rule(rule)
    except Exception:
        exc_info = sys.exc_info()

    return parser, parsing_result, exc_info


def parse_source_to_ast(source):
    parser, parsing_result, exc_info = parse(source)

    if exc_info:
        msg = parsing_error_to_msg(
            exc_info=exc_info,
            lex_error_class=LexError,
            syntax_error_class=SyntaxError,
            title='解析错误',
            txt=source,
        )

        raise ImportError(msg) from exc_info[1]

    ast_obj = parsing_result['res']

    return ast_obj


def debug_infos_to_msg(debug_infos, txt):
    rows = txt.split('\n')

    msgs = []

    for debug_info in debug_infos:
        row_txt = rows[debug_info.row]

        msg = '{indent}{error_sign}{name}: {row}.{col} ({pos}): {txt}'.format(
            indent='  ' * debug_info.slv,
            error_sign='' if debug_info.sss else '!',
            name=debug_info.name,
            row=debug_info.row + 1,
            col=debug_info.col + 1,
            pos=debug_info.pos + 1,
            txt=repr(
                row_txt[:debug_info.col] + '|' + row_txt[debug_info.col:]
            ),
        )

        msgs.append(msg)

    msg = '\n'.join(msgs)

    return msg


def parsing_error_to_msg(
    exc_info,
    lex_error_class,
    syntax_error_class,
    title,
    txt,
):
    msg = title

    exc = exc_info[1]

    if isinstance(exc, lex_error_class):
        return '{0}\n{1}'.format(title, str(exc))

    if not isinstance(exc, syntax_error_class):
        tb_lines = format_exception(*exc_info)

        tb_msg = ''.join(tb_lines)

        msg += '\n---\n{0}---\n'.format(tb_msg)

        return msg

    msgs = []

    msgs.append(msg)

    msgs.append(str(exc))

    # Messages below are for backtracking mode.
    reason_exc_infos = []

    if exc.eisp:
        reason_exc_infos.extend(ei for ei in exc.eisp if ei[1] is not exc)

    if exc.eis:
        reason_exc_infos.extend(ei for ei in exc.eis if ei[1] is not exc)

    if reason_exc_infos:
        rows = txt.split('\n')

        msg = '可能原因：'

        msgs.append(msg)

        for reason_exc_info in reason_exc_infos:
            exc = reason_exc_info[1]

            ctx_names = get_ctx_names(exc.ctx)

            ctx_msg = ''

            if ctx_names:
                ctx_msg = ' '.join(ctx_names)

            row_txt = rows[exc.row]

            narrow_column_index = get_narrow_column_index(row_txt, exc.col)

            col_mark = ' ' * narrow_column_index + '|'

            msg = (
                '无法处理规则`{rule}`，第{row}行，第{col}列，全文第{pos}个字符。\n'
                '上下文：{ctx_msg}。\n'
                '```\n'
                '{row_txt}\n'
                '{col_mark}\n'
                '```'
            ).format(
                rule=exc.ctx.name,
                row=exc.row + 1,
                col=exc.col + 1,
                pos=exc.pos + 1,
                ctx_msg=ctx_msg,
                row_txt=row_txt,
                col_mark=col_mark,
            )

            msgs.append(msg)

    msg = '\n'.join(msgs)

    return msg


def get_ctx_names(ctx):
    ctx_names = []

    ctx_name = getattr(ctx, 'name')

    ctx_names.append(ctx_name)

    while True:
        ctx = getattr(ctx, 'par', None)

        if ctx is None:
            break

        name = getattr(ctx, 'name')

        ctx_names.append(name)

    ctx_names = list(reversed(ctx_names))

    return ctx_names


WIDE_CHARS_REO = re.compile(
    '[\u4e00-\u9fa5，、；：。！？＃…—‘’“”（）【】《》『』]+'
)

NON_WIDE_CHARS_REO = re.compile(
    '[^\u4e00-\u9fa5，、；：。！？＃…—‘’“”（）【】《》『』]+'
)


def get_narrow_column_index(row_txt, column_index):
    if WIDE_CHARS_REO is None:
        return column_index

    row_txt = row_txt[:column_index]

    row_txt_count = len(row_txt)

    narrow_column_index = 0

    current_index = 0

    while current_index < row_txt_count:
        match_obj = WIDE_CHARS_REO.match(row_txt, current_index)

        if match_obj:
            chars_count = len(match_obj.group())

            narrow_column_index += chars_count * 2

            current_index += chars_count

        match_obj = NON_WIDE_CHARS_REO.match(row_txt, current_index)

        if match_obj:
            chars_count = len(match_obj.group())

            narrow_column_index += chars_count

            current_index += chars_count

    return narrow_column_index
