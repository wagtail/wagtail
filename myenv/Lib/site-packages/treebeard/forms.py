"""Forms for treebeard."""

from django import forms
from django.db.models.query import QuerySet
from django.forms.models import ErrorList
from django.forms.models import modelform_factory as django_modelform_factory
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from treebeard.al_tree import AL_Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node


class MoveNodeForm(forms.ModelForm):
    """
    Form to handle moving a node in a tree.

    Handles sorted/unsorted trees.

    It adds two fields to the form:

    - Relative to: The target node where the current node will
                   be moved to.
    - Position: The position relative to the target node that
                will be used to move the node. These can be:

                - For sorted trees: ``Child of`` and ``Sibling of``
                - For unsorted trees: ``First child of``, ``Before`` and
                  ``After``

    .. warning::

        Subclassing :py:class:`MoveNodeForm` directly is
        discouraged, since special care is needed to handle
        excluded fields, and these change depending on the
        tree type.

        It is recommended that the :py:func:`movenodeform_factory`
        function is used instead.

    """

    __position_choices_sorted = (
        ('sorted-child', _('Child of')),
        ('sorted-sibling', _('Sibling of')),
    )

    __position_choices_unsorted = (
        ('first-child', _('First child of')),
        ('left', _('Before')),
        ('right', _('After')),
    )

    _position = forms.ChoiceField(required=True, label=_("Position"))

    _ref_node_id = forms.ChoiceField(required=False, label=_("Relative to"))

    def _get_position_ref_node(self, instance):
        if self.is_sorted:
            position = 'sorted-child'
            node_parent = instance.get_parent()
            if node_parent:
                ref_node_id = node_parent.pk
            else:
                ref_node_id = ''
        else:
            prev_sibling = instance.get_prev_sibling()
            if prev_sibling:
                position = 'right'
                ref_node_id = prev_sibling.pk
            else:
                position = 'first-child'
                if instance.is_root():
                    ref_node_id = ''
                else:
                    ref_node_id = instance.get_parent().pk
        return {'_ref_node_id': ref_node_id,
                '_position': position}

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, **kwargs):
        opts = self._meta
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified')

        # update the '_position' field choices
        self.is_sorted = getattr(opts.model, 'node_order_by', False)
        if self.is_sorted:
            choices_sort_mode = self.__class__.__position_choices_sorted
        else:
            choices_sort_mode = self.__class__.__position_choices_unsorted
        self.declared_fields['_position'].choices = choices_sort_mode

        # update the '_ref_node_id' choices
        choices = self.mk_dropdown_tree(opts.model, for_node=instance)
        self.declared_fields['_ref_node_id'].choices = choices
        # use the formfield `to_python` method to coerse the field for custom ids
        pkFormField = opts.model._meta.pk.formfield()
        self.declared_fields['_ref_node_id'].coerce = pkFormField.to_python if pkFormField else int

        # put initial data for these fields into a map, update the map with
        # initial data, and pass this new map to the parent constructor as
        # initial data
        if instance is None:
            initial_ = {}
        else:
            initial_ = self._get_position_ref_node(instance)

        if initial is not None:
            initial_.update(initial)

        super().__init__(
            data=data, files=files, auto_id=auto_id, prefix=prefix,
            initial=initial_, error_class=error_class,
            label_suffix=label_suffix, empty_permitted=empty_permitted,
            instance=instance, **kwargs)

    def _clean_cleaned_data(self):
        """ delete auxilary fields not belonging to node model """
        reference_node_id = None

        if '_ref_node_id' in self.cleaned_data:
            if self.cleaned_data['_ref_node_id'] != '0':
                reference_node_id = self.cleaned_data['_ref_node_id']
                if reference_node_id.isdigit():
                    reference_node_id = int(reference_node_id)
            del self.cleaned_data['_ref_node_id']

        position_type = self.cleaned_data['_position']
        del self.cleaned_data['_position']

        return position_type, reference_node_id

    def save(self, commit=True):
        position_type, reference_node_id = self._clean_cleaned_data()

        if self.instance._state.adding:
            if reference_node_id:
                reference_node = self._meta.model.objects.get(
                    pk=reference_node_id)
                self.instance = reference_node.add_child(instance=self.instance)
                self.instance.move(reference_node, pos=position_type)
            else:
                self.instance = self._meta.model.add_root(instance=self.instance)
        else:
            self.instance.save()
            if reference_node_id:
                reference_node = self._meta.model.objects.get(
                    pk=reference_node_id)
                self.instance.move(reference_node, pos=position_type)
            else:
                if self.is_sorted:
                    pos = 'sorted-sibling'
                else:
                    pos = 'first-sibling'
                self.instance.move(self._meta.model.get_first_root_node(), pos)
        # Reload the instance
        self.instance.refresh_from_db()
        super().save(commit=commit)
        return self.instance

    @staticmethod
    def is_loop_safe(for_node, possible_parent):
        if for_node is not None:
            return not (
                possible_parent == for_node
                ) or (possible_parent.is_descendant_of(for_node))
        return True

    @staticmethod
    def mk_indent(level):
        return '&nbsp;&nbsp;&nbsp;&nbsp;' * (level - 1)

    @classmethod
    def add_subtree(cls, for_node, node, options):
        """ Recursively build options tree. """
        if cls.is_loop_safe(for_node, node):
            for item, _ in node.get_annotated_list(node):
                options.append((item.pk, mark_safe(cls.mk_indent(item.get_depth()) + escape(item))))

    @classmethod
    def mk_dropdown_tree(cls, model, for_node=None):
        """ Creates a tree-like list of choices """

        options = [(None, _('-- root --'))]
        for node in model.get_root_nodes():
            cls.add_subtree(for_node, node, options)
        return options


def movenodeform_factory(model, form=MoveNodeForm, fields=None, exclude=None,
                         formfield_callback=None,  widgets=None):
    """Dynamically build a MoveNodeForm subclass with the proper Meta.

    :param Node model:

        The subclass of :py:class:`Node` that will be handled
        by the form.

    :param form:

        The form class that will be used as a base. By
        default, :py:class:`MoveNodeForm` will be used.

    :return: A :py:class:`MoveNodeForm` subclass
    """
    _exclude = _get_exclude_for_model(model, exclude)
    return django_modelform_factory(
        model, form, fields, _exclude, formfield_callback, widgets)


def _get_exclude_for_model(model, exclude):
    if exclude:
        _exclude = tuple(exclude)
    else:
        _exclude = ()
    if issubclass(model, AL_Node):
        _exclude += ('sib_order', 'parent')
    elif issubclass(model, MP_Node):
        _exclude += ('depth', 'numchild', 'path')
    elif issubclass(model, NS_Node):
        _exclude += ('depth', 'lft', 'rgt', 'tree_id')
    return _exclude
