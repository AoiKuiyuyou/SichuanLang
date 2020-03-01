# coding: utf-8
from __future__ import absolute_import

from os.path import abspath
from os.path import dirname
import sys


def init_syspath():
    my_dir = dirname(abspath(__file__))

    for path in ['', '.', my_dir]:
        if path in sys.path:
            sys.path.remove(path)

    src_dir = dirname(my_dir)

    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def main():
    if sys.version_info[0] == 2\
    or sys.version_info[0] == 3 and sys.version_info[1] < 5:
        sys.stderr.write(
            'Error: Please use Python 3.5+.\n'
        )

        sys.exit(1)

    init_syspath()

    from sichuanlang.main import main_imp

    main_imp()


if __name__ == '__main__':
    sys.exit(main())
