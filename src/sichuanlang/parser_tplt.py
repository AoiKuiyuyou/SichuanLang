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

    _RULE_FUNC_PRF = '{SS_RULE_FUNC_NAME_PRF}'

    _RULE_FUNC_POF = '{SS_RULE_FUNC_NAME_POF}'

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
{SS_BACKTRACKING_FUNCS}
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

{SS_RULE_FUNCS}


def parse(txt, rule=None, debug=False):
    parser = Parser(
        txt=txt,
        debug=debug,
    )

    if rule is None:
        rule = '{SS_ENTRY_RULE}'

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
