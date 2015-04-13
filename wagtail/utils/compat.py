import django


def get_related_model(rel):
    # In Django 1.7 and under, the related model is accessed by doing: rel.model
    # This was renamed in Django 1.8 to rel.related_model. rel.model now returns
    # the base model.
    if django.VERSION >= (1, 8):
        return rel.related_model
    else:
        return rel.model
