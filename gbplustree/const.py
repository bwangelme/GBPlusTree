# -*- coding: utf-8 -*-

from collections import namedtuple

# 存储整数使用的端类型
ENDIAN = 'little'

# 保存B+树中节点类型的长度
NODE_TYPE_BYTES = 1

# B+树节点中使用长度的长度
USED_PAGE_LENGTH_BYTES = 3

# 用于存储页的索引的字节数
# 4KB 的页能够寻址 16 TB 的内存
# 这里最多支持 2^32 个 4 KB 页，也就是说支持的内存为 2^32 * 2^12 B，即 16 TB
PAGE_REFERENCE_BYTES = 4

# 帧的类型最多有 256 种
FRAME_TYPE_BYTES = 1

# 保存键长度的内存空间的长度
USED_KEY_LENGTH_BYTES = 2
# 保存值长度的内存空间的长度
USED_VALUE_LENGTH_BYTES = 2

# 用于存储有特定目的的整数，例如文件的元数据
OTHER_BYTES = 4

TreeConf = namedtuple('TestConf', [
    'page_size',
    'order',
    'key_size',
    'value_size',
    'serializer',
])
