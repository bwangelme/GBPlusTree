# -*- coding: utf-8 -*-

from datetime import datetime, timezone

from unittest import mock
import uuid
import pytest

from gbplustree.serializer import (
    IntSerializer,
    StrSerializer,
    UUIDSerializer,
    DatetimeUTCSerializer,
)


def test_int_serializer():
    s = IntSerializer()
    assert s.serialize(42, 2) == b'*\x00'
    assert s.deserialize(b'*\x00') == 42
    assert repr(s) == 'IntSerializer()'


def test_serializer_slots():
    s = IntSerializer()
    with pytest.raises(AttributeError):
        s.foo = True


def test_str_serializer():
    s = StrSerializer()
    assert s.serialize('foo', 3) == b'foo'
    assert s.deserialize(b'foo') == 'foo'
    assert repr(s) == 'StrSerializer()'


def test_uuid_serializer():
    s = UUIDSerializer()
    id_ = uuid.uuid4()
    assert s.serialize(id_, 16) == id_.bytes
    assert s.deserialize(id_.bytes) == id_
    assert repr(s) == 'UUIDSerializer()'


def test_datetime_utc_serializer():
    s = DatetimeUTCSerializer()
    dt = datetime(2018, 4, 15, 12, 00, 0, 424739, tzinfo=timezone.utc)
    serialized = s.serialize(dt, 8)
    assert serialized == b'W\xe270\x00\x19\xec\x8c'
    assert s.deserialize(serialized) == dt
    assert repr(s) == 'DatetimeUTCSerializer()'


@mock.patch.dict('gbplustree.serializer.__dict__', {'temporenc': None})
def test_datetime_utc_serializer_no_temporenc():
    with pytest.raises(RuntimeError):
        DatetimeUTCSerializer()


def test_datetime_utc_serializer_no_timezone():
    with pytest.raises(ValueError):
        s = DatetimeUTCSerializer()
        dt = datetime(2018, 4, 15, 12, 00, 0, 424739)
        s.serialize(dt, 8)
