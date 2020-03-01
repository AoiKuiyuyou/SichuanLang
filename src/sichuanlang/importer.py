# coding: utf-8
from __future__ import absolute_import

import importlib
from importlib import machinery
import os
import sys

from .parser import parse_source_to_ast


def _has_sichuan_ext(filename):
    return os.path.isfile(filename) and (filename.endswith('.sichuan'))


def patch_importlib():
    machinery.SOURCE_SUFFIXES.insert(0, '.sichuan')

    _py_source_to_code = machinery.SourceFileLoader.source_to_code

    def _sichuan_source_to_code(self, data, path, _optimize=-1):
        if _has_sichuan_ext(path):
            source_code = data.decode("utf-8")

            data = parse_source_to_ast(source_code)

        code_obj = _py_source_to_code(
            self, data, path, _optimize=_optimize
        )

        return code_obj

    machinery.SourceFileLoader.source_to_code\
        = _sichuan_source_to_code

    sys.path_importer_cache.clear()

    importlib.invalidate_caches()
