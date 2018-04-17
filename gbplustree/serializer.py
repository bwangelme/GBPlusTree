# -*- coding: utf-8 -*-

import abc
from datetime import datetime, timezone

from uuid import UUID

from .const import ENDIAN

try:
    import temporenc
except ImportError:
    temporenc = None


class Serializer(metaclass=abc.ABCMeta):

    """
    slots 属性的作用是限制实例的属性，如果定义了 __slots__ ，只有 __slots__ 内定义的属性才可以被设置
    slots 只对当前类起作用，对子类不起作用。
        如果子类定义了 slots，那么可用的属性为 子类 + 父类 中slots中定义的属性
    >>> class S:
    ...     pass
    ...
    >>> s = S()
    >>> s.a = True
    >>> class S:
    ...     __slots__ = ['b']
    ...
    >>> s = S()
    >>> s.a = True
    Traceback (most recent call last):
      File "<ipython-input-42-184f863bf658>", line 1, in <module>
        s.a = True
    AttributeError: 'S' object has no attribute 'a'

    >>> s.b = True
    """
    __slots__ = []

    @abc.abstractmethod
    def serialize(self, obj: object, key_size: int) -> bytes:
        """将 key 序列化成 bytes"""

    @abc.abstractmethod
    def deserialize(self, data: bytes) -> object:
        """ 根据 bytes 创建一个 key 对象 """

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)


class IntSerializer(Serializer):

    __slots__ = []

    def serialize(self, obj: int, key_size: int) -> bytes:
        return obj.to_bytes(key_size, ENDIAN)

    def deserialize(self, data: bytes) -> int:
        return int.from_bytes(data, ENDIAN)


class StrSerializer(Serializer):

    __slots__ = []

    def serialize(self, obj: str, key_size: int) -> bytes:
        rv = obj.encode(encoding='utf-8')
        assert len(rv) <= key_size
        return rv

    def deserialize(self, data: bytes) -> str:
        return data.decode(encoding='utf-8')


class UUIDSerializer(Serializer):

    __slots__ = []

    def serialize(self, obj: UUID, key_size: int) -> bytes:
        return obj.bytes

    def deserialize(self, data: bytes) -> UUID:
        return UUID(bytes=data)


class DatetimeUTCSerializer(Serializer):

    __slots__ = []

    def __init__(self):
        if temporenc is None:
            raise RuntimeError('Serialization to/from datetime needs the '
                               'third-party library "temporenc"')

    def serialize(self, obj: datetime, key_size: int) -> bytes:
        if obj.tzinfo is None:
            raise ValueError("DatetimeUTCSerializer needs a timezone aware"
                             " datetime")
        return temporenc.packb(obj, type="DTS")

    def deserialize(self, data: bytes) -> datetime:
        rv = temporenc.unpackb(data).datetime()
        rv = rv.replace(tzinfo=timezone.utc)
        return rv
