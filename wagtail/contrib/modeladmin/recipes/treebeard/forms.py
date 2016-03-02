from django.utils.translation import ugettext as _
from treebeard.forms import MoveNodeForm


class MoveForm(MoveNodeForm):
    @classmethod
    def mk_dropdown_tree(cls, model, for_node=None):
        """ Creates a tree-like list of choices """

        options = [(0, _('Root'))]
        for node in model.get_root_nodes():
            cls.add_subtree(for_node, node, options)
        return options


class NoIndentationMoveForm(MoveForm):
    @staticmethod
    def mk_indent(level):
        return ''
