# -*- coding: utf-8 -*-

import abc
import math
import bisect
from typing import Optional

from .const import (
    TreeConf,
    NODE_TYPE_BYTES,
    ENDIAN,
    PAGE_REFERENCE_BYTES,
    USED_PAGE_LENGTH_BYTES
)
from .entry import Entry, Record, Reference


class Node(metaclass=abc.ABCMeta):

    __slots__ = ['_tree_conf', 'entries', 'page', 'parent', 'next_page']

    # 下面这些属性可以在子类中被重新定义
    _node_type_int = 0
    max_children = 0
    min_children = 0
    _entry_class = None

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int = None, parent: 'Node'=None, next_page: int=None):
        self._tree_conf = tree_conf
        self.entries = list()
        self.page = page
        self.parent = parent
        self.next_page = next_page
        if data:
            self.load(data)

    def load(self, data: bytes):
        """ 将数据从字节转换成一个 B+ 树节点

        :param data:
        :return:
        """
        # 检查数据的长度是否相等
        assert len(data) == self._tree_conf.page_size

        # 计算使用长度的区间
        end_used_length_bytes = NODE_TYPE_BYTES + USED_PAGE_LENGTH_BYTES
        # 恢复使用的长度
        used_length = int.from_bytes(
            data[NODE_TYPE_BYTES:end_used_length_bytes],
            ENDIAN
        )

        # 计算 next_page 的区间
        end_reference_bytes = end_used_length_bytes + PAGE_REFERENCE_BYTES
        next_page = int.from_bytes(
            data[end_used_length_bytes:end_reference_bytes],
            ENDIAN
        )
        # 恢复 next_page
        self.next_page = None if next_page == 0 else next_page

        # 获取 entry 的长度，从数据中逐个恢复entry
        # node 节点头的长度为 4
        entry_length = self._entry_class(self._tree_conf).length
        for start_offset in range(
                end_reference_bytes,
                used_length + end_reference_bytes - 4,
                entry_length):
            entry_data = data[start_offset:start_offset+entry_length]
            entry = self._entry_class(self._tree_conf, data=entry_data)
            self.entries.append(entry)

    def dump(self) -> bytearray:
        """
        节点结构示意图: https://passage-1253400711.cos.ap-beijing.myqcloud.com/2018-04-25-075426.png

        :return:
        bytearry 和 bytes 类似，都是由整数组成的序列，区别在于 bytearray 是可变的数组，bytes 是不可变的数组
        """
        data = bytearray()
        # 首先备份所有数据
        for record in self.entries:
            data.extend(record.dump())

        # 然后计算使用的页的长度，包括数据和头，4表示B+树节点头的长度
        used_length = len(data) + 4
        # 检查使用的页的长度有没有超出页大小
        assert 4 <= used_length < self._tree_conf.page_size

        # 获取 next_page 的内容
        next_page = 0 if self.next_page is None else self.next_page

        # 计算头的数据
        header = (
            self._node_type_int.to_bytes(NODE_TYPE_BYTES, ENDIAN)
            + used_length.to_bytes(USED_PAGE_LENGTH_BYTES, ENDIAN)
            + next_page.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN)
        )

        # 获取总的数据，添加padding
        data = bytearray(header) + data
        padding = self._tree_conf.page_size - len(data)

        # 检查padding长度是否正确
        assert padding >= 0
        data.extend(bytearray(padding))

        # 检查最后总的数据是否是page_size
        assert len(data) == self._tree_conf.page_size

        return data

    @property
    def can_add_entry(self) -> bool:
        return self.num_children < self.max_children

    @property
    def can_delete_entry(self) -> bool:
        return self.num_children > self.min_children

    @property
    def smallest_key(self):
        return self.smallest_entry.key

    @property
    def smallest_entry(self):
        return self.entries[0]

    @property
    def biggest_key(self):
        return self.biggest_entry.key

    @property
    def biggest_entry(self):
        return self.entries[-1]

    @property
    @abc.abstractmethod
    def num_children(self) -> int:
        """
        #TODO 对于这个注释还不太理解

        Number of entries or other nodes connected to the node
        返回 entries 的个数或者关联到这个节点的其他节点的个数
        :return:
        """

    def pop_smallest(self) -> Entry:
        return self.entries.pop(0)

    def insert_entry(self, entry: Entry):
        bisect.insort(self.entries, entry)

    def insert_entry_at_the_end(self, entry: Entry):
        """
        当已知一个要插入的 entry 的键是最大的时候，可以调用这个方法插入值
        :param entry:
        :return:
        """
        self.entries.append(entry)

    def remove_entry(self, key):
        self.entries.pop(self._find_entry_index(key))

    def get_entry(self, key) -> Entry:
        return self.entries[self._find_entry_index(key)]

    def _find_entry_index(self, key) -> int:
        entry = self._entry_class(
            self._tree_conf,
            key=key
        )
        i = bisect.bisect_left(self.entries, entry)
        if i != len(self.entries) and self.entries[i] == entry:
            return i
        raise ValueError('No entry for key {}'.format(key))

    def split_entries(self) -> list:
        len_entries = len(self.entries)

        rv = self.entries[len_entries//2:]
        self.entries = self.entries[:len_entries//2]
        assert len(self.entries) + len(rv) == len_entries
        return rv

    @classmethod
    def from_page_data(cls, tree_conf: TreeConf, data: bytes,
                       page: int = None) -> 'Node':
        node_type_byte = data[0:NODE_TYPE_BYTES]
        node_type_int = int.from_bytes(node_type_byte, ENDIAN)
        if node_type_int == 1:
            return LonelyRootNode(tree_conf, data, page)
        elif node_type_int == 2:
            return RootNode(tree_conf, data, page)
        elif node_type_int == 3:
            return InternalNode(tree_conf, data, page)
        elif node_type_int == 4:
            return LeafNode(tree_conf, data, page)
        else:
            assert False, 'No Node with type {} exists'.format(node_type_int)

    def __repr__(self):
        return '<{}: page={} entries={}>'.format(
            self.__class__.__name__, self.page, len(self.entries)
        )

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and self.page == other.page
            and self.entries == other.entries
        )


class RecordNode(Node):

    __slots__ = ['_entry_class']

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int=None, parent: 'Node'=None, next_page: int=None):
        # TODO: 这里 Pycharm 为什么会警告 _entry_class 是只读的
        self._entry_class = Record
        super().__init__(tree_conf, data, page, parent, next_page)

    @property
    def num_children(self) -> int:
        return len(self.entries)


class LonelyRootNode(RecordNode):
    """ 拥有记录的 root 节点

    这个节点针对的是只有一个节点的B+树
    """

    __slots__ = ['_node_type_int', 'min_children', 'max_children']

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int=None, parent: 'Node'=None, next_page: int=None):
        self._node_type_int = 1
        self.min_children = 0
        self.max_children = tree_conf.order - 1
        super().__init__(tree_conf, data, page, parent)

    def convert_to_leaf(self):
        leaf = LeafNode(self._tree_conf, page=self.page)
        leaf.entries = self.entries
        return leaf


class ReferenceNode(Node):

    __slots__ = ["_entry_class"]

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int = None, parent: 'Node'=None):
        self._entry_class = Reference
        super().__init__(tree_conf, data, page, parent)

    def insert_entry(self, entry: Reference):
        super().insert_entry(entry)
        i = self.entries.index(entry)
        if i > 0:
            prev_entry = self.entries[i-1]
            prev_entry.after = entry.before

        try:
            next_entry = self.entries[i+1]
        except IndexError:
            pass
        else:
            next_entry.before = entry.after

    @property
    def num_children(self) -> int:
        # TODO: 为什么这里长度要 +1
        return len(self.entries) + 1 if self.entries else 0


class InternalNode(ReferenceNode):

    __slots__ = ['_node_type_int', 'min_children', 'max_children']

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int=None, parent: 'Node'=None):
        self._node_type_int = 3
        self.min_children = math.ceil(tree_conf.order / 2)
        self.max_children = tree_conf.order
        super().__init__(tree_conf, data, page, parent)


class RootNode(ReferenceNode):

    __slots__ = ['_node_type_int', 'min_children', 'max_children']

    def __init__(self, tree_conf: TreeConf, data: Optional[bytes]=None,
                 page: int=None, parent: 'Node'=None):
        self._node_type_int = 2
        self.min_children = 2
        self.max_children = tree_conf.order
        # 这个等价于 super(RootNode, self).__init__(tree_conf, data, page, parent)
        super().__init__(tree_conf, data, page, parent)

    def convert_to_internal(self) -> InternalNode:
        internal = InternalNode(self._tree_conf, page=self.page)
        internal.entries = self.entries
        return internal


class LeafNode(RecordNode):

    __slots__ = ['_node_type_int', 'min_children', 'max_children']

    def __init__(self, tree_conf: TreeConf,
                 data: Optional[bytes] = None, page: int = None,
                 parent: 'Node' = None, next_page: int = None):
        self._node_type_int = 4
        self.min_children = math.ceil(tree_conf.order / 2) - 1
        self.max_children = tree_conf.order - 1
        super().__init__(tree_conf, data, page, parent, next_page)
