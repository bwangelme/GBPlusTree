# -*- coding: utf-8 -*-

from collections import namedtuple

# 存储整数使用的端类型
ENDIAN = 'little'

# 用于存储页的索引的字节数
# 4KB 的页能够寻址 16 TB 的内存
PAGE_REFERENCE_BYTES = 4

# 在记录头中存储键或者值的长度的字节数
# 键或值的最大长度的限制为 64 KB
USED_KEY_LENGTH_BYTES = 2
USED_VALUE_LENGTH_BYTES = 2

TreeConf = namedtuple('TestConf', [
    'page_size',
    'order',
    'key_size',
    'value_size',
    'serializer',
])
