"""Helper functions to support django-treebeard"""

from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Concat, Substr
from treebeard.exceptions import PathOverflow


class TreebeardPathFixMixin:
    """
    Extends the fix_tree method with a `fix_paths` option that non-destructively fixes holes in
    path sequences, and applies the node_order_by ordering, if specified.
    Taken from https://github.com/django-treebeard/django-treebeard/pull/165 - can be removed
    if / when that PR is included in a django-treebeard release.
    """

    @classmethod
    def fix_tree(cls, fix_paths=False, **kwargs):
        super().fix_tree(**kwargs)

        if fix_paths:
            with transaction.atomic():
                # To fix holes and mis-orderings in paths, we consider each non-leaf node in turn
                # and ensure that its children's path values are consecutive (and in the order
                # given by node_order_by, if applicable). children_to_fix is a queue of child sets
                # that we know about but have not yet fixed, expressed as a tuple of
                # (parent_path, depth). Since we're updating paths as we go, we must take care to
                # only add items to this list after the corresponding parent node has been fixed
                # (and is thus not going to change).

                # Initially children_to_fix is the set of root nodes, i.e. ones with a path
                # starting with '' and depth 1.
                children_to_fix = [("", 1)]

                while children_to_fix:
                    parent_path, depth = children_to_fix.pop(0)

                    children = cls.objects.filter(
                        path__startswith=parent_path, depth=depth
                    ).values("pk", "path", "depth", "numchild")

                    desired_sequence = children.order_by(
                        *(cls.node_order_by or ["path"])
                    )

                    # mapping of current path position (converted to numeric) to item
                    actual_sequence = {}

                    # highest numeric path position currently in use
                    max_position = None

                    # loop over items to populate actual_sequence and max_position
                    for item in desired_sequence:
                        actual_position = cls._str2int(item["path"][-cls.steplen :])
                        actual_sequence[actual_position] = item
                        if max_position is None or actual_position > max_position:
                            max_position = actual_position

                    # loop over items to perform path adjustments
                    for (i, item) in enumerate(desired_sequence):
                        desired_position = i + 1  # positions are 1-indexed
                        actual_position = cls._str2int(item["path"][-cls.steplen :])
                        if actual_position == desired_position:
                            pass
                        else:
                            # if a node is already in the desired position, move that node
                            # to max_position + 1 to get it out of the way
                            occupant = actual_sequence.get(desired_position)
                            if occupant:
                                old_path = occupant["path"]
                                max_position += 1
                                new_path = cls._get_path(
                                    parent_path, depth, max_position
                                )
                                if len(new_path) > len(old_path):
                                    previous_max_path = cls._get_path(
                                        parent_path, depth, max_position - 1
                                    )
                                    raise PathOverflow(
                                        "Path Overflow from: '%s'"
                                        % (previous_max_path,)
                                    )

                                cls._rewrite_node_path(old_path, new_path)
                                # update actual_sequence to reflect the new position
                                actual_sequence[max_position] = occupant
                                del actual_sequence[desired_position]
                                occupant["path"] = new_path

                            # move item into the (now vacated) desired position
                            old_path = item["path"]
                            new_path = cls._get_path(
                                parent_path, depth, desired_position
                            )
                            cls._rewrite_node_path(old_path, new_path)
                            # update actual_sequence to reflect the new position
                            actual_sequence[desired_position] = item
                            del actual_sequence[actual_position]
                            item["path"] = new_path

                        if item["numchild"]:
                            # this item has children to process, and we have now moved the parent
                            # node into its final position, so it's safe to add to children_to_fix
                            children_to_fix.append((item["path"], depth + 1))

    @classmethod
    def _rewrite_node_path(cls, old_path, new_path):
        cls.objects.filter(path__startswith=old_path).update(
            path=Concat(Value(new_path), Substr("path", len(old_path) + 1))
        )
