# coding: utf-8
from __future__ import absolute_import


HANZI_DIGIT_TO_VALUE = {
    '〇': 0,
    '零': 0,
    '一': 1,
    '壹': 1,
    '二': 2,
    '贰': 2,
    '貮': 2,
    '两': 2,
    '三': 3,
    '叁': 3,
    '四': 4,
    '肆': 4,
    '五': 5,
    '伍': 5,
    '六': 6,
    '陆': 6,
    '七': 7,
    '柒': 7,
    '八': 8,
    '捌': 8,
    '九': 9,
    '玖': 9,
}


HANZI_UNIT_TO_VALUE = {
    '十': 10,
    '拾': 10,
    '百': 100,
    '佰': 100,
    '千': 1000,
    '仟': 1000,
    '万': 10000,
    '萬': 10000,
    '亿': 100000000,
    '億': 100000000,
    '兆': 1000000000000,
}


HANZI_DIGITS_AND_UNITS = set(HANZI_DIGIT_TO_VALUE.keys())\
    | set(HANZI_UNIT_TO_VALUE.keys())


def hanzi_digits_to_value(text):
    digits = list(text)

    unit_value = 0

    unit_types = []

    while digits:
        digit = digits.pop()

        digit_value = HANZI_DIGIT_TO_VALUE.get(digit)

        if digit_value is not None:
            if unit_value:
                digit_value = digit_value * unit_value

                unit_value = 0

            unit_types.append(digit_value)

            continue

        unit_value = HANZI_UNIT_TO_VALUE.get(digit)

        if unit_value is not None:
            if unit_value == 10000:
                unit_types.append('w')
                unit_value = 1
            elif unit_value == 100000000:
                unit_types.append('y')
                unit_value = 1
            elif unit_value == 1000000000000:
                unit_types.append('z')
                unit_value = 1

            continue

        raise ValueError('Unrecongnized character: `{0}`.'.format(digit))

    if unit_value == 10:
        unit_types.append(10)

    result = 0

    pending_value = 0

    while unit_types:
        unit_type = unit_types.pop()

        if unit_type == 'w':
            pending_value *= 10000
            result += pending_value
            pending_value = 0
        elif unit_type == 'y':
            pending_value *= 100000000
            result += pending_value
            pending_value = 0
        elif unit_type == 'z':
            pending_value *= 1000000000000
            result += pending_value
            pending_value = 0
        else:
            pending_value += unit_type

    result += pending_value

    return result
