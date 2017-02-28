from __future__ import absolute_import, unicode_literals

import difflib

from bs4 import BeautifulSoup
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _


class FieldComparison:
    is_field = True
    is_child_relation = False

    def __init__(self, field, obj_a, obj_b):
        self.field = field
        self.val_a = field.value_from_object(obj_a)
        self.val_b = field.value_from_object(obj_b)

    def field_label(self):
        """
        Returns a label for this field to be displayed to the user
        """
        verbose_name = getattr(self.field, 'verbose_name', None)

        if verbose_name is None:
            # Relations don't have a verbose_name
            verbose_name = self.field.name.replace('_', ' ')

        return capfirst(verbose_name)

    def htmldiff(self):
        if self.val_a != self.val_b:
            return TextDiff([('deletion', self.val_a), ('addition', self.val_b)]).to_html()
        else:
            return escape(self.val_a)

    def has_changed(self):
        """
        Returns True if the field has changed
        """
        return self.val_a != self.val_b


class TextFieldComparison(FieldComparison):
    def htmldiff(self):
        return diff_text(self.val_a, self.val_b).to_html()


class RichTextFieldComparison(TextFieldComparison):
    def htmldiff(self):
        return diff_text(
            BeautifulSoup(force_text(self.val_a), 'html5lib').getText(),
            BeautifulSoup(force_text(self.val_b), 'html5lib').getText()
        ).to_html()


class StreamFieldComparison(RichTextFieldComparison):
    pass


class ChoiceFieldComparison(FieldComparison):
    def htmldiff(self):
        val_a = force_text(dict(self.field.flatchoices).get(self.val_a, self.val_a), strings_only=True)
        val_b = force_text(dict(self.field.flatchoices).get(self.val_b, self.val_b), strings_only=True)

        if self.val_a != self.val_b:
            return TextDiff([('deletion', val_a), ('addition', val_b)]).to_html()
        else:
            return escape(val_a)


class M2MFieldComparison(FieldComparison):
    def get_items(self):
        return list(self.val_a), list(self.val_b)

    def get_item_display(self, item):
        return str(item)

    def htmldiff(self):
        # Get tags
        items_a, items_b = self.get_items()

        # Calculate changes
        sm = difflib.SequenceMatcher(0, items_a, items_b)
        changes = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'replace':
                for item in items_a[i1:i2]:
                    changes.append(('deletion', self.get_item_display(item)))
                for item in items_b[j1:j2]:
                    changes.append(('addition', self.get_item_display(item)))
            elif op == 'delete':
                for item in items_a[i1:i2]:
                    changes.append(('deletion', self.get_item_display(item)))
            elif op == 'insert':
                for item in items_b[j1:j2]:
                    changes.append(('addition', self.get_item_display(item)))
            elif op == 'equal':
                for item in items_a[i1:i2]:
                    changes.append(('equal', self.get_item_display(item)))

        # Convert changelist to HTML
        return TextDiff(changes, separator=", ").to_html()

    def has_changed(self):
        items_a, items_b = self.get_items()
        return items_a != items_b


class TagsFieldComparison(M2MFieldComparison):
    def get_items(self):
        tags_a = [
            tag.tag
            for tag in self.val_a
        ]

        tags_b = [
            tag.tag
            for tag in self.val_b
        ]

        return tags_a, tags_b

    def get_item_display(self, tag):
        return tag.slug


class ForeignObjectComparison(FieldComparison):
    def get_objects(self):
        model = self.field.related_model
        obj_a = model.objects.filter(id=self.val_a).first()
        obj_b = model.objects.filter(id=self.val_b).first()
        return obj_a, obj_b

    def htmldiff(self):
        obj_a, obj_b = self.get_objects()

        if obj_a != obj_b:
            if obj_a and obj_b:
                # Changed
                return TextDiff([('deletion', force_text(obj_a)), ('addition', force_text(obj_b))]).to_html()
            elif obj_b:
                # Added
                return TextDiff([('addition', force_text(obj_b))]).to_html()
            elif obj_a:
                # Removed
                return TextDiff([('deletion', force_text(obj_a))]).to_html()
        else:
            if obj_a:
                return escape(force_text(obj_a))
            else:
                return mark_safe(_("None"))


class ChildRelationComparison:
    is_field = False
    is_child_relation = True

    def __init__(self, field, field_comparisons, obj_a, obj_b):
        self.field = field
        self.field_comparisons = field_comparisons
        self.val_a = getattr(obj_a, field.related_name)
        self.val_b = getattr(obj_b, field.related_name)

    def field_label(self):
        """
        Returns a label for this field to be displayed to the user
        """
        verbose_name = getattr(self.field, 'verbose_name', None)

        if verbose_name is None:
            # Relations don't have a verbose_name
            verbose_name = self.field.name.replace('_', ' ')

        return capfirst(verbose_name)

    def get_mapping(self, objs_a, objs_b):
        """
        This bit of code attempts to match the objects in the A revision with
        their counterpart in the B revision.

        A match is firstly attempted by ID (where a matching ID indicates they're the same).
        We compare remaining the objects by their field data; the objects with the fewest
        fields changed are matched until there are no more possible matches left.

        This returns 4 values:
         - map_forwards => a mapping of object indexes from the B version to the A version
         - map_backwards => a mapping of object indexes from the A version to the B version
         - added => a list of indices for objects that didn't exist in the B version
         - deleted => a list of indices for objects that didn't exist in the A version

        Note the indices are 0-based array indices indicating the location of the object in either
        the objs_a or objs_b arrays.

        For example:

        objs_a => A, B, C, D
        objs_b => B, C, D, E

        Will return the following:

        map_forwards = {
            1: 0,  # B (objs_a: objs_b)
            2: 1,  # C (objs_a: objs_b)
            3: 2,  # D (objs_a: objs_b)
        }
        map_backwards = {
            0: 1,  # B (objs_b: objs_a)
            1: 2,  # C (objs_b: objs_a)
            2: 3,  # D (objs_b: objs_a)
        }
        added = [4]  # D in objs_b
        deleted = [0]  # A in objs_a
        """
        map_forwards = {}
        map_backwards = {}
        added = []
        deleted = []

        # Match child objects on ID
        for a_idx, a_child in enumerate(objs_a):
            for b_idx, b_child in enumerate(objs_b):
                if b_idx in map_backwards:
                    continue

                if a_child.id is not None and b_child.id is not None and a_child.id == b_child.id:
                    map_forwards[a_idx] = b_idx
                    map_backwards[b_idx] = a_idx

        # Now try to match them by data
        matches = []
        for a_idx, a_child in enumerate(objs_a):
            if a_idx not in map_forwards:
                for b_idx, b_child in enumerate(objs_b):
                    if b_idx not in map_backwards:
                        # If they both have an ID that is different, they can't be the same child object
                        if a_child.id and b_child.id and a_child.id != b_child.id:
                            continue

                        comparison = self.get_child_comparison(objs_a[a_idx], objs_b[b_idx])
                        num_differences = comparison.get_num_differences()

                        matches.append((a_idx, b_idx, num_differences))

        # Objects with the least differences will be matched first. So only the best possible matches are made
        matches.sort(key=lambda match: match[2])
        for a_idx, b_idx, num_differences in matches:
            # Make sure both objects were not matched previously
            if a_idx in map_forwards or b_idx in map_backwards:
                continue

            # Match!
            map_forwards[a_idx] = b_idx
            map_backwards[b_idx] = a_idx

        # Mark unmapped objects as added/deleted
        for a_idx, a_child in enumerate(objs_a):
            if a_idx not in map_forwards:
                deleted.append(a_idx)

        for b_idx, b_child in enumerate(objs_b):
            if b_idx not in map_backwards:
                added.append(b_idx)

        return map_forwards, map_backwards, added, deleted

    def get_child_comparison(self, obj_a, obj_b):
        return ChildObjectComparison(self.field.related_model, self.field_comparisons, obj_a, obj_b)

    def get_child_comparisons(self):
        """
        Returns a list of ChildObjectComparison objects. Representing all child
        objects that existed in either version.

        They are returned in the order they appear in the B version with deletions
        appended at the end.

        All child objects are returned, regardless of whether they were actually changed.
        """
        objs_a = list(self.val_a.all())
        objs_b = list(self.val_b.all())

        map_forwards, map_backwards, added, deleted = self.get_mapping(objs_a, objs_b)
        objs_a = dict(enumerate(objs_a))
        objs_b = dict(enumerate(objs_b))

        comparisons = []

        for b_idx, b_child in objs_b.items():
            if b_idx in added:
                comparisons.append(self.get_child_comparison(None, b_child))
            else:
                comparisons.append(self.get_child_comparison(objs_a[map_backwards[b_idx]], b_child))

        for a_idx, a_child in objs_a.items():
            if a_idx in deleted:
                comparisons.append(self.get_child_comparison(a_child, None))

        return comparisons

    def has_changed(self):
        """
        Returns true if any changes were made to any of the child objects. This includes
        adding, deleting and reordering.
        """
        objs_a = list(self.val_a.all())
        objs_b = list(self.val_b.all())

        map_forwards, map_backwards, added, deleted = self.get_mapping(objs_a, objs_b)

        if added or deleted:
            return True

        for a_idx, b_idx in map_forwards.items():
            comparison = self.get_child_comparison(objs_a[a_idx], objs_b[b_idx])

            if comparison.has_changed():
                return True

        return False


class ChildObjectComparison:
    def __init__(self, model, field_comparisons, obj_a, obj_b):
        self.model = model
        self.field_comparisons = field_comparisons
        self.obj_a = obj_a
        self.obj_b = obj_b

    def is_addition(self):
        """
        Returns True if this child object was created since obj_a
        """
        return self.obj_b and not self.obj_a

    def is_deletion(self):
        """
        Returns True if this child object was deleted in obj_b
        """
        return self.obj_a and not self.obj_b

    def get_position_change(self):
        """
        Returns the change in position as an integer. Positive if the object
        was moved down, negative if it moved up.

        For example: '3' indicates the object moved down three spaces. '-1'
        indicates the object moved up one space.
        """
        if not self.is_addition() and not self.is_deletion():
            sort_a = getattr(self.obj_a, 'sort_order', 0) or 0
            sort_b = getattr(self.obj_b, 'sort_order', 0) or 0
            return sort_b - sort_a

    def get_field_comparisons(self):
        """
        Returns a list of comparisons for all the fields in this object.
        Fields that haven't changed are included as well.
        """
        comparisons = []

        if self.is_addition() or self.is_deletion():
            # Display the fields without diff as one of the versions are missing
            obj = self.obj_a or self.obj_b

            for field_comparison in self.field_comparisons:
                comparisons.append(field_comparison(obj, obj))
        else:
            for field_comparison in self.field_comparisons:
                comparisons.append(field_comparison(self.obj_a, self.obj_b))

        return comparisons

    def has_changed(self):
        for comparison in self.get_field_comparisons():
            if comparison.has_changed():
                return True

        return False

    def get_num_differences(self):
        """
        Returns the number of fields that differ between the two
        objects.
        """
        num_differences = 0

        for comparison in self.get_field_comparisons():
            if comparison.has_changed():
                num_differences += 1

        return num_differences


class TextDiff:
    def __init__(self, changes, separator=""):
        self.changes = changes
        self.separator = separator

    def to_html(self, tag='span', addition_class='addition', deletion_class='deletion'):
        html = []

        for change_type, value in self.changes:
            if change_type == 'equal':
                html.append(escape(value))
            elif change_type == 'addition':
                html.append('<{tag} class="{classname}">{value}</{tag}>'.format(
                    tag=tag,
                    classname=addition_class,
                    value=escape(value)
                ))
            elif change_type == 'deletion':
                html.append('<{tag} class="{classname}">{value}</{tag}>'.format(
                    tag=tag,
                    classname=deletion_class,
                    value=escape(value)
                ))

        return mark_safe(self.separator.join(html))


def diff_text(a, b):
    """
    Performs a diffing algorithm on two pieces of text. Returns
    a string of HTML containing the content of both texts with
    <span> tags inserted indicating where the differences are.
    """
    def tokenise(text):
        """
        Tokenises a string by spliting it into individual characters
        and grouping the alphanumeric ones together.

        This means that punctuation, whitespace, CJK characters, etc
        become separate tokens and words/numbers are merged together
        to form bigger tokens.

        This makes the output of the diff easier to read as words are
        not broken up.
        """
        tokens = []
        current_token = ""

        for c in text:
            if c.isalnum():
                current_token += c
            else:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""

                tokens.append(c)

        if current_token:
            tokens.append(current_token)

        return tokens

    a_tok = tokenise(a)
    b_tok = tokenise(b)
    sm = difflib.SequenceMatcher(lambda t: len(t) <= 4, a_tok, b_tok)

    changes = []

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'replace':
            for token in a_tok[i1:i2]:
                changes.append(('deletion', token))
            for token in b_tok[j1:j2]:
                changes.append(('addition', token))
        elif op == 'delete':
            for token in a_tok[i1:i2]:
                changes.append(('deletion', token))
        elif op == 'insert':
            for token in b_tok[j1:j2]:
                changes.append(('addition', token))
        elif op == 'equal':
            for token in a_tok[i1:i2]:
                changes.append(('equal', token))

    # Merge ajacent changes which have the same type. This just cleans up the HTML a bit
    merged_changes = []
    current_value = []
    current_change_type = None
    for change_type, value in changes:
        if change_type != current_change_type:
            if current_change_type is not None:
                merged_changes.append((current_change_type, ''.join(current_value)))
                current_value = []

            current_change_type = change_type

        current_value.append(value)

    if current_value:
        merged_changes.append((current_change_type, ''.join(current_value)))

    return TextDiff(merged_changes)
