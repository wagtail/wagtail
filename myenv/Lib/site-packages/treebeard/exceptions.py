"""Treebeard exceptions"""


class InvalidPosition(Exception):
    """Raised when passing an invalid pos value"""


class InvalidMoveToDescendant(Exception):
    """Raised when attempting to move a node to one of it's descendants."""


class NodeAlreadySaved(Exception):
    """
    Raised when attempting to add a node which is already saved to the
    database.
    """


class MissingNodeOrderBy(Exception):
    """
    Raised when an operation needs a missing
    :attr:`~treebeard.MP_Node.node_order_by` attribute
    """


class PathOverflow(Exception):
    """
    Raised when trying to add or move a node to a position where no more nodes
    can be added (see :attr:`~treebeard.MP_Node.path` and
    :attr:`~treebeard.MP_Node.alphabet` for more info)
    """
