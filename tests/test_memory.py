# -*- coding: utf-8 -*-
import io
from unittest import mock
import os
import platform
import pytest

from gbplustree.memory import (
    FileMemory,
    WAL,
    ReachedEndOfFile,
    open_file_in_dir,
    write_to_file,
)
from gbplustree.const import (TreeConf)
from gbplustree.serializer import IntSerializer
from gbplustree.node import LeafNode

from .conftest import filename


tree_conf = TreeConf(4096, 4, 16, 16, IntSerializer())
node = LeafNode(tree_conf, page=3)


def test_file_memory_node():
    mem = FileMemory(filename, tree_conf)

    with pytest.raises(ReachedEndOfFile):
        mem.get_node(3)

    mem.set_node(node)
    assert node == mem.get_node(3)

    mem.close()


def test_wal_create_reopen_empty():
    WAL(filename, 64)

    wal = WAL(filename, 64)
    assert wal._page_size == 64


def test_write_to_file_multi_times():
    def side_effect(*args, **kwargs):
        if len(args) == 1:
            data = args[0]
        if len(data) > 5:
            return 5
        else:
            return len(data)

    mock_fd = mock.MagicMock()
    mock_fd.write.side_effect = side_effect

    write_to_file(mock_fd, None, b'abcdefg')


def test_open_file_in_dir():
    with pytest.raises(ValueError):
        open_file_in_dir('/foo/bar/does/not/exist')

    for _ in range(2):
        file_fd, dir_fd = open_file_in_dir(filename)

        assert isinstance(file_fd, io.FileIO)
        file_fd.close()

        if platform.system() == 'Windows':
            assert dir_fd is None
        else:
            assert isinstance(dir_fd, int)
            os.close(dir_fd)


@mock.patch('gbplustree.memory.platform.system', return_value='Windows')
def test_open_file_in_dir_on_windows(_):
    file_fd, dir_fd = open_file_in_dir(filename)
    assert isinstance(file_fd, io.FileIO)
    file_fd.close()
    assert dir_fd is None


def test_file_memory_repr():
    mem = FileMemory(filename, tree_conf)
    assert repr(mem) == '<FileMemory: {}>'.format(filename)
    mem.close()
