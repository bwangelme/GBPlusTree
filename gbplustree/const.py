# -*- coding: utf-8 -*-

from collections import namedtuple

ENDIAN = 'little'

TreeConf = namedtuple('TestConf', [
    'page_size',
    'order',
    'key_size',
    'value_size',
    'serializer',
])
