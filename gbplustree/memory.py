# -*- coding: utf-8 -*-

import io
import logging
import os
import platform
import rwlock
import cachetools
from typing import Tuple, Union, Optional, BinaryIO

from .node import Node
from .const import (
    TreeConf,
    PAGE_REFERENCE_BYTES,
    FRAME_TYPE_BYTES
)


logger = logging.getLogger(__name__)


class ReachedEndOfFile(Exception):
    """Read a file until its end"""


def open_file_in_dir(path: str) -> Tuple[BinaryIO, Optional[int]]:
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        raise ValueError('No directory {}'.format(directory))

    # buffering 的作用参考: ﻿
    # http://3ea84aca.wiz03.com/share/s/0-G4Ha2WtkJT2bJ4VU3guUn80kfA1m0qN4gF2xoKTw3cbmx5
    if not os.path.exists(path):
        file_fd = open(path, mode='x+b', buffering=0)
    else:
        file_fd = open(path, mode='r+b', buffering=0)

    if platform.system() == 'Windows':
        """
        windows 不支持打开一个目录，但这也不是一个问题，
        因为Windows上不需要通过 fsync 函数来持久化元数据
        """
        dir_fd = None
    else:
        dir_fd = os.open(directory, os.O_RDONLY)

    return file_fd, dir_fd


class FileMemory:

    __slots__ = ['_filename', '_tree_conf', '_lock', '_cache', '_fd',
                 '_dir_fd', '_wal', 'last_page']

    def __init__(self, filename: str, tree_conf: TreeConf,
                 cache_size: int = 512):
        self._filename = filename
        self._tree_conf = tree_conf
        self._lock = rwlock.RWLock

        if cache_size == 0:
            self._cache = FakeCache()
        else:
            self._cache = cachetools.LRUCache(maxsize=cache_size)

        self._fd, self._dir_fd = open_file_in_dir(filename)

        self._wal = WAL(filename, tree_conf.page_size)

    def get_node(self, page: int) -> Node:
        pass

    def set_node(self, node: Node):
        pass


class FakeCache:
    """
    一个不缓存任何内容的缓存类，因为 cachetool 不支持 maxsize = 0
    """

    def get(self, k):
        pass

    def __setitem__(self, key, value):
        pass

    def clear(self):
        pass


class WAL:

    __slots__ = ['filename', '_fd', '_dir_fd', '_page_size',
                 '_committed_pages', '_not_committed_pages', 'need_recovery']

    FRAME_HEADER_LENGTH = (
        FRAME_TYPE_BYTES + PAGE_REFERENCE_BYTES
    )

    def __init__(self, filename: str, page_size: int):
        self.filename = filename + '-wal'
        self._fd, self._dir_fd = open_file_in_dir(self.filename)
        self._page_size = page_size
        self._committed_pages = dict()
        self._not_committed_pages = dict()

        self._fd.seek(0, io.SEEK_END)
        if self._fd.tell() == 0:
            self._create_header()
            self.need_recovery = False
        else:
            logger.warning("Find an existing WAL file"
                           "the B+Tree was not closed properly")
            self.need_recovery = True
            self._load_wal()
