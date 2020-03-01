# coding: utf-8
from __future__ import absolute_import

from argparse import ArgumentParser
from importlib import import_module
import os.path
import sys
from traceback import format_exc

from . import parser
from .importer import patch_importlib
from .parser import parse_source_to_ast


def get_arg_parser():
    arg_parser = ArgumentParser()

    arg_parser.add_argument(
        '-m', '--module',
        dest='module_name',
        required=True,
        metavar='模块名或路径',
        help='要运行的模块名或路径。',
    )

    arg_parser.add_argument(
        '-n', '--narrow-column',
        dest='hz_is_narrow_column',
        action='store_true',
        default=False,
        help=(
            '假定汉字在命令行显示时只占一列。默认假定汉字占两列。此设置影响报错信息的'
            '错误位置标记符是否显示在正确的列。'
        ),
    )

    arg_parser.add_argument(
        '-p', '--python-code',
        dest='convert_to_python_code',
        action='store_true',
        default=False,
        help='转换成Python源码。',
    )

    return arg_parser


def main_imp():
    arg_parser = get_arg_parser()

    args = arg_parser.parse_args()

    if args.hz_is_narrow_column:
        parser.WIDE_CHARS_REO = None
        parser.NON_WIDE_CHARS_REO = None

    patch_importlib()

    module_path = None

    ast_node = None

    if args.module_name.endswith('.sichuan')\
    or '/' in args.module_name\
    or '\\' in args.module_name:
        module_path = os.path.join(os.getcwd(), args.module_name)
    elif args.convert_to_python_code:
        module_relative_path = args.module_name.replace('.', os.sep)

        for dir_path in sys.path:
            module_path = os.path.join(dir_path, module_relative_path)

            module_path += '.sichuan'

            if os.path.isfile(module_path):
                break
        else:
            msg = '未找到模块文件路径。\n'
            sys.stderr.write(msg)
            sys.exit(1)

    if module_path is not None:
        if not os.path.isfile(module_path):
            msg = '错误：模块路径不存在：`{0}`。\n'.format(module_path)
            sys.stderr.write(msg)
            sys.exit(1)

        try:
            with open(module_path, encoding='utf-8') as source_file:
                source_code = source_file.read()
        except Exception:
            msg = '错误：读取源文件出错：`{0}`。\n'.format(module_path)
            sys.stderr.write(msg)
            sys.stderr.write(
                '----- 错误细节 -----\n{0}===== 错误细节 =====\n'.format(
                    format_exc()
                )
            )
            sys.exit(1)

        try:
            ast_node = parse_source_to_ast(source_code)
        except Exception:
            msg = '错误：解析源代码到抽象语法树出错：`{0}`。\n'.format(module_path)
            sys.stderr.write(msg)
            sys.stderr.write(
                '----- 错误细节 -----\n{0}===== 错误细节 =====\n'.format(
                    format_exc()
                )
            )
            sys.exit(1)

    if not args.convert_to_python_code:
        if ast_node is None:
            import_module(args.module_name)
        else:
            code_obj = compile(ast_node, filename=module_path, mode='exec')

            exec(code_obj, {}, {})
    else:
        try:
            import astunparse
        except ImportError:
            msg = '错误：请安装`astunparse`。\npip install astunparse\n'
            sys.stderr.write(msg)
            sys.exit(1)

        try:
            py_source_code = astunparse.unparse(ast_node)

            py_source_code = py_source_code.strip() + '\n'
        except Exception:
            msg = '错误：反解析抽象语法树到源代码出错。\n'
            sys.stderr.write(msg)
            sys.stderr.write(
                '----- 错误细节 -----\n{0}===== 错误细节 =====\n'.format(
                    format_exc()
                )
            )
            sys.exit(1)

        print(py_source_code)
