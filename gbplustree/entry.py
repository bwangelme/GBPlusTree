# -*- coding: utf-8 -*-

import abc

from typing import Optional

from gbplustree.const import (
    ENDIAN,
    TreeConf,
    USED_KEY_LENGTH_BYTES,
    USED_VALUE_LENGTH_BYTES,
    PAGE_REFERENCE_BYTES,
)


class Entry(metaclass=abc.ABCMeta):

    __slots__ = []

    @abc.abstractmethod
    def load(self, data: bytes):
        """ 将 data 反序列化成对象 """

    @abc.abstractmethod
    def dump(self) -> bytes:
        """ 将对象序列化成 bytes """

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __le__(self, other):
        return self.key <= other.key

    def __gt__(self, other):
        return self.key > other.key

    def __ge__(self, other):
        return self.key >= other.key


class Record(Entry):

    __slots__ = ['_tree_conf', 'key', 'value', 'length', 'overflow_page']

    def __init__(self, tree_conf: TreeConf, key=None,
                 value: Optional[bytes]=None, data: Optional[bytes]=None,
                 overflow_page: Optional[int]=None):
        """
        数据组织的示意图: https://passage-1253400711.cos.ap-beijing.myqcloud.com/2018-04-17-024819.png

        :param tree_conf:
        :param key:
        :param value:
        :param data:
        :param overflow_page:
        """
        self._tree_conf = tree_conf
        self.key = key
        self.value = value
        self.overflow_page = overflow_page
        self.length = (
            USED_KEY_LENGTH_BYTES
            + self._tree_conf.key_size

            + USED_VALUE_LENGTH_BYTES
            + self._tree_conf.value_size

            + PAGE_REFERENCE_BYTES
        )

        if data:
            self.load(data)
        if value:
            assert len(self.value) <= self._tree_conf.value_size

    def load(self, data: bytes):
        """
        # TODO: 理解 overflow_page 的含义

        :param data:
        :return:
        """
        assert len(data) == self.length

        end_used_key_length = USED_KEY_LENGTH_BYTES
        used_key_length = int.from_bytes(data[0:end_used_key_length], ENDIAN)
        assert 0 <= used_key_length <= self._tree_conf.key_size

        end_key = end_used_key_length + used_key_length
        self.key = self._tree_conf.serializer.deserialize(
            data[end_used_key_length:end_key]
        )

        start_used_value_length = (
            end_used_key_length + self._tree_conf.key_size
        )
        end_used_value_length = (
            start_used_value_length + USED_VALUE_LENGTH_BYTES
        )
        used_value_length = int.from_bytes(
            data[start_used_value_length:end_used_value_length], ENDIAN
        )
        assert 0 <= used_value_length <= self._tree_conf.value_size

        end_value = end_used_value_length + used_value_length

        start_overflow = end_used_value_length + self._tree_conf.value_size
        end_overflow = start_overflow + PAGE_REFERENCE_BYTES
        overflow_page = int.from_bytes(
            data[start_overflow:end_overflow], ENDIAN
        )

        # overflow_page 和 value 两者不是共存的
        if overflow_page:
            self.overflow_page = overflow_page
            self.value = None
        else:
            self.overflow_page = None
            self.value = data[end_used_value_length:end_value]

    def dump(self) -> bytes:
        assert self.value is None or self.overflow_page is None
        # 将键变成字节形式
        key_as_bytes = self._tree_conf.serializer.serialize(
            self.key, self._tree_conf.key_size
        )
        used_key_length = len(key_as_bytes)
        overflow_page = self.overflow_page or 0
        if overflow_page:
            value = b''
        else:
            value = self.value
        used_value_length = len(value)

        data = (
            used_key_length.to_bytes(USED_KEY_LENGTH_BYTES, ENDIAN)
            + key_as_bytes
            + bytes(self._tree_conf.key_size - used_key_length)

            + used_value_length.to_bytes(USED_VALUE_LENGTH_BYTES, ENDIAN)
            + value
            + bytes(self._tree_conf.value_size - used_value_length)

            + overflow_page.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN)
        )

        return data

    def __repr__(self) -> str:
        if self.value:
            return "<Record: {} value={}>".format(self.key, self.value[0:16])
        if self.overflow_page:
            return "<Record: {} overflowing value>".format(self.key)

        return "<Record: {} unknown value>".format(self.key)


class Reference(Entry):

    __slots__ = ['_tree_conf', 'length', 'key', 'before', 'after']

    def __init__(self, tree_conf: TreeConf, key=None, before=None, after=None,
                 data: bytes = None):
        self._tree_conf = tree_conf
        self.length = (
            2 * PAGE_REFERENCE_BYTES
            + USED_KEY_LENGTH_BYTES
            + self._tree_conf.key_size
        )
        self.key = key
        self.before = before
        self.after = after
        if data:
            self.load(data)

    def dump(self) -> bytes:
        assert isinstance(self.before, int)
        assert isinstance(self.after, int)

        key_as_bytes = self._tree_conf.serializer.serialize(
            self.key, self._tree_conf.key_size
        )
        used_key_length = len(key_as_bytes)

        data = (
            self.before.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN)

            # 存储键的长度
            + used_key_length.to_bytes(USED_VALUE_LENGTH_BYTES, ENDIAN)

            + key_as_bytes
            + bytes(self._tree_conf.key_size - used_key_length)

            + self.after.to_bytes(PAGE_REFERENCE_BYTES, ENDIAN)
        )

        return data

    def load(self, data: bytes):
        assert len(data) == self.length
        end_before = PAGE_REFERENCE_BYTES
        self.before = int.from_bytes(data[0:end_before], ENDIAN)

        end_used_key_length = end_before + USED_KEY_LENGTH_BYTES
        used_key_length = int.from_bytes(
            data[end_before:end_used_key_length], ENDIAN
        )
        assert 0 <= used_key_length <= self._tree_conf.key_size

        end_key = end_used_key_length + used_key_length
        self.key = self._tree_conf.serializer.deserialize(
            data[end_used_key_length:end_key]
        )

        start_after = end_used_key_length + self._tree_conf.key_size
        end_after = start_after + PAGE_REFERENCE_BYTES
        self.after = int.from_bytes(data[start_after:end_after], ENDIAN)

    def __repr__(self):
        return '<Reference: key={} before={} after={}>'.format(
            self.key, self.before, self.after
        )
