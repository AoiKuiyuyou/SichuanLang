# coding: utf-8
from __future__ import absolute_import

from os.path import abspath
from os.path import dirname
from random import randint
import sys


sys.path.insert(0, dirname(dirname(dirname(abspath(__name__)))))

import sichuanlang.enable_import  # isort:skip
id(sichuanlang.enable_import)
from sichuanlang.demo.factorial import 阶乘  # isort:skip
from sichuanlang.demo.fibonacci_sequence import 斐波那契序列某位  # isort:skip
from sichuanlang.demo.selection_sort import 选择排序  # isort:skip
from sichuanlang.demo.cycle_sort import 圈排序  # isort:skip
from sichuanlang.demo.bubble_sort import 冒泡排序  # isort:skip
from sichuanlang.demo.cocktail_shaker_sort import 鸡尾酒排序  # isort:skip
from sichuanlang.demo.comb_sort import 梳子排序  # isort:skip
from sichuanlang.demo.gnome_sort import 地精排序  # isort:skip
from sichuanlang.demo.odd_even_sort import 奇偶排序  # isort:skip
from sichuanlang.demo.bitonic_sort import 双调排序  # isort:skip
from sichuanlang.demo.insertion_sort import 插入排序  # isort:skip
from sichuanlang.demo.shell_sort import 希尔排序  # isort:skip
from sichuanlang.demo.bucket_sort import 桶排序  # isort:skip
from sichuanlang.demo.bead_sort import 珠排序  # isort:skip
from sichuanlang.demo.counting_sort import 计数排序  # isort:skip
from sichuanlang.demo.pigeonhole_sort import 鸽巢排序  # isort:skip
from sichuanlang.demo.radix_sort import 基数排序  # isort:skip
from sichuanlang.demo.radix_exchange_sort import 基数交换排序  # isort:skip
from sichuanlang.demo.proxmap_sort import 近似映射排序  # isort:skip
from sichuanlang.demo.heap_sort import 堆排序  # isort:skip
from sichuanlang.demo.tournament_sort import 锦标赛排序  # isort:skip
from sichuanlang.demo.merge_sort import 归并排序  # isort:skip
from sichuanlang.demo.tim_sort import 蒂姆排序  # isort:skip
from sichuanlang.demo.quick_sort import 快速排序  # isort:skip
from sichuanlang.demo.slow_sort import 慢速排序  # isort:skip
from sichuanlang.demo.pancake_sort import 煎饼排序  # isort:skip
from sichuanlang.demo.stooge_sort import 臭皮匠排序  # isort:skip
from sichuanlang.demo.binary_tree_sort import 二叉树排序  # isort:skip


def 测试_阶乘():
    assert 阶乘(1) == 1
    assert 阶乘(2) == 2
    assert 阶乘(3) == 6
    assert 阶乘(4) == 24
    assert 阶乘(5) == 120


def 测试_斐波那契序列某位():
    assert 斐波那契序列某位(0) == 0
    assert 斐波那契序列某位(1) == 1
    assert 斐波那契序列某位(2) == 1
    assert 斐波那契序列某位(3) == 2
    assert 斐波那契序列某位(4) == 3
    assert 斐波那契序列某位(5) == 5


NUMBERS_COUNT = 100

NUMBERS = [randint(0, NUMBERS_COUNT) for _ in range(NUMBERS_COUNT)]


def 测试排序(排序函数):
    expected_items = list(NUMBERS)
    expected_items.sort()
    sorted_items = 排序函数(list(NUMBERS))
    assert sorted_items == expected_items


def 测试_选择排序():
    测试排序(选择排序)


def 测试_圈排序():
    测试排序(圈排序)


def 测试_冒泡排序():
    测试排序(冒泡排序)


def 测试_鸡尾酒排序():
    测试排序(鸡尾酒排序)


def 测试_梳子排序():
    测试排序(梳子排序)


def 测试_地精排序():
    测试排序(地精排序)


def 测试_奇偶排序():
    测试排序(奇偶排序)


def 测试_双调排序():
    测试排序(双调排序)


def 测试_插入排序():
    测试排序(插入排序)


def 测试_希尔排序():
    测试排序(希尔排序)


def 测试_桶排序():
    测试排序(桶排序)


def 测试_珠排序():
    测试排序(珠排序)


def 测试_计数排序():
    测试排序(计数排序)


def 测试_鸽巢排序():
    测试排序(鸽巢排序)


def 测试_基数排序():
    测试排序(基数排序)


def 测试_基数交换排序():
    测试排序(基数交换排序)


def 测试_近似映射排序():
    测试排序(近似映射排序)


def 测试_堆排序():
    测试排序(堆排序)


def 测试_锦标赛排序():
    测试排序(锦标赛排序)


def 测试_归并排序():
    测试排序(归并排序)


def 测试_蒂姆排序():
    测试排序(蒂姆排序)


def 测试_快速排序():
    测试排序(快速排序)


def 测试_慢速排序():
    测试排序(慢速排序)


def 测试_煎饼排序():
    测试排序(煎饼排序)


def 测试_臭皮匠排序():
    测试排序(臭皮匠排序)


def 测试_二叉树排序():
    测试排序(二叉树排序)


if __name__ == '__main__':
    for name, obj in vars().copy().items():
        if name.startswith('测试_') and callable(obj):
            print('# ----- {0} -----'.format(name))

            obj()
