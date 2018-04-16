# -*- coding: utf-8 -*-

import pytest

from gbplustree.entry import Record, Reference
from gbplustree.const import TreeConf
from gbplustree.serializer import (
    IntSerializer,
    StrSerializer
)

tree_conf = TreeConf(4096, 4, 16, 16, IntSerializer())


def test_record_int_serialization():
    r1 = Record(tree_conf, 42, b'foo')
    data = r1.dump()

    r2 = Record(tree_conf, data=data)

    assert r1 == r2
    assert r1.value == r2.value
    assert r1.overflow_page == r2.overflow_page


def test_record_str_serialization():
    tree_conf = TreeConf(4096, 4, 40, 40, StrSerializer())
    r1 = Record(tree_conf, '0', b'0')
    data = r1.dump()

    r2 = Record(tree_conf, data=data)

    assert r1 == r2
    assert r1.value == r2.value
    assert r1.overflow_page == r2.overflow_page


def test_record_int_serialization_overflow_value():
    r1 = Record(tree_conf, 42, overflow_page=5)
    data = r1.dump()

    r2 = Record(tree_conf, data=data)

    assert r1 == r2
    assert r1.value == r2.value
    assert r1.overflow_page == r2.overflow_page


def test_record_repr():
    r1 = Record(tree_conf, 42, b'foo')
    assert repr(r1) == "<Record: 42 value=b'foo'>"

    r1.value = None
    assert repr(r1) == "<Record: 42 unknown value>"

    r1.overflow_page = 5
    assert repr(r1) == "<Record: 42 overflowing value>"

    r1.value = b'0123456789abcdefDO NOT SHOW'
    r1.overflow_page = None
    assert repr(r1) == "<Record: 42 value=b'0123456789abcdef'>"


def test_record_either_value_or_overflow_page():
    r1 = Record(tree_conf, 42, b'foo')
    r1.overflow_page = 10

    with pytest.raises(AssertionError):
        r1.dump()


def test_record_slots():
    r1 = Record(tree_conf, 42, b'foo')
    with pytest.raises(AttributeError):
        r1.foo = False


def test_reference_int_serialization():
    r1 = Reference(tree_conf, 42, 1, 2)
    data = r1.dump()

    r2 = Reference(tree_conf, data=data)

    assert r1 == r2
    assert r1.before == r2.before
    assert r1.after == r2.after


def test_reference_str_serialization():
    tree_conf = TreeConf(4096, 4, 40, 40, StrSerializer())
    r1 = Reference(tree_conf, 'foo', 1, 2)
    data = r1.dump()

    r2 = Reference(tree_conf, data=data)
    assert r1 == r2
    assert r1.before == r2.before
    assert r1.after == r2.after


def test_reference_repr():
    r1 = Reference(tree_conf, 42, 1, 2)
    assert repr(r1) == '<Reference: key=42 before=1 after=2>'
