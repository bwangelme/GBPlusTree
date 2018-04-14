# -*- coding: utf-8 -*-

from bplustree import BPlusTree


def main():
    tree = BPlusTree('/tmp/bplustree.db', order=50)

    tree[1] = b'foo'
    tree[2] = b'bar'

    print(tree.get(3), tree[1], list(tree.keys()))
    tree.close()


if __name__ == '__main__':
    main()
