import uuid

from django.db import models
from django.contrib.auth.models import User

from treebeard.mp_tree import MP_Node
from treebeard.al_tree import AL_Node
from treebeard.ns_tree import NS_Node


class RelatedModel(models.Model):
    desc = models.CharField(max_length=255)

    def __str__(self):
        return self.desc


class MP_TestNode(MP_Node):
    steplen = 3

    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_UnicodeNode(MP_Node):
    steplen = 3

    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return self.desc


class MP_TestNodeSomeDep(models.Model):
    node = models.ForeignKey(MP_TestNode, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeRelated(MP_Node):
    steplen = 3

    desc = models.CharField(max_length=255)
    related = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeInherited(MP_TestNode):
    extra_desc = models.CharField(max_length=255)


class MP_TestNodeCustomId(MP_Node):
    steplen = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class NS_TestNode(NS_Node):
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class NS_UnicodetNode(NS_Node):
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return self.desc


class NS_TestNodeSomeDep(models.Model):
    node = models.ForeignKey(NS_TestNode, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class NS_TestNodeRelated(NS_Node):
    desc = models.CharField(max_length=255)
    related = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class NS_TestNodeInherited(NS_TestNode):
    extra_desc = models.CharField(max_length=255)


class AL_TestNode(AL_Node):
    parent = models.ForeignKey(
        "self",
        related_name="children_set",
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    sib_order = models.PositiveIntegerField()
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class AL_UnicodeNode(AL_Node):
    parent = models.ForeignKey(
        "self",
        related_name="children_set",
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    sib_order = models.PositiveIntegerField()
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return self.desc


class AL_TestNodeSomeDep(models.Model):
    node = models.ForeignKey(AL_TestNode, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class AL_TestNodeRelated(AL_Node):
    parent = models.ForeignKey(
        "self",
        related_name="children_set",
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    sib_order = models.PositiveIntegerField()
    desc = models.CharField(max_length=255)
    related = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class AL_TestNodeInherited(AL_TestNode):
    extra_desc = models.CharField(max_length=255)


class MP_TestNodeSorted(MP_Node):
    steplen = 1
    node_order_by = ["val1", "val2", "desc"]
    val1 = models.IntegerField()
    val2 = models.IntegerField()
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class NS_TestNodeSorted(NS_Node):
    node_order_by = ["val1", "val2", "desc"]
    val1 = models.IntegerField()
    val2 = models.IntegerField()
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class AL_TestNodeSorted(AL_Node):
    parent = models.ForeignKey(
        "self",
        related_name="children_set",
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
    )
    node_order_by = ["val1", "val2", "desc"]
    val1 = models.IntegerField()
    val2 = models.IntegerField()
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeAlphabet(MP_Node):
    steplen = 2

    numval = models.IntegerField()

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeSmallStep(MP_Node):
    steplen = 1
    alphabet = "0123456789"

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeSortedAutoNow(MP_Node):
    desc = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    node_order_by = ["created"]

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeShortPath(MP_Node):
    steplen = 1
    alphabet = "012345678"
    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


class MP_TestNodeUuid(MP_Node):
    steplen = 1
    custom_id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)

    desc = models.CharField(max_length=255)

    def __str__(self):  # pragma: no cover
        return "Node %s" % self.pk


# This is how you change the default fields defined in a Django abstract class
# (in this case, MP_Node), since Django doesn't allow overriding fields, only
# mehods and attributes
MP_TestNodeShortPath._meta.get_field("path").max_length = 4


class MP_TestNode_Proxy(MP_TestNode):
    class Meta:
        proxy = True


class NS_TestNode_Proxy(NS_TestNode):
    class Meta:
        proxy = True


class AL_TestNode_Proxy(AL_TestNode):
    class Meta:
        proxy = True


class MP_TestSortedNodeShortPath(MP_Node):
    steplen = 1
    alphabet = "012345678"
    desc = models.CharField(max_length=255)

    node_order_by = ["desc"]

    def __str__(self):  # pragma: no cover
        return "Node %d" % self.pk


MP_TestSortedNodeShortPath._meta.get_field("path").max_length = 4


class MP_TestManyToManyWithUser(MP_Node):
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(User)


BASE_MODELS = (
    AL_TestNode,
    MP_TestNode,
    NS_TestNode,
    MP_TestNodeUuid,
    MP_TestNodeCustomId,
)
PROXY_MODELS = AL_TestNode_Proxy, MP_TestNode_Proxy, NS_TestNode_Proxy
SORTED_MODELS = AL_TestNodeSorted, MP_TestNodeSorted, NS_TestNodeSorted
DEP_MODELS = AL_TestNodeSomeDep, MP_TestNodeSomeDep, NS_TestNodeSomeDep
MP_SHORTPATH_MODELS = MP_TestNodeShortPath, MP_TestSortedNodeShortPath
RELATED_MODELS = AL_TestNodeRelated, MP_TestNodeRelated, NS_TestNodeRelated
UNICODE_MODELS = AL_UnicodeNode, MP_UnicodeNode, NS_UnicodetNode
INHERITED_MODELS = (AL_TestNodeInherited, MP_TestNodeInherited, NS_TestNodeInherited)


def empty_models_tables(models):
    for model in models:
        model.objects.all().delete()
