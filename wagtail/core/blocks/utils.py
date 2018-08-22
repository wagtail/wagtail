import re


# helpers for Javascript expression formatting


def indent(string, depth=1):
    """indent all non-empty lines of string by 'depth' 4-character tabs"""
    return re.sub(r'(^|\n)([^\n]+)', r'\g<1>' + ('    ' * depth) + r'\g<2>', string)


def js_dict(d):
    """
    Return a Javascript expression string for the dict 'd'.
    Keys are assumed to be strings consisting only of JS-safe characters, and will be quoted but not escaped;
    values are assumed to be valid Javascript expressions and will be neither escaped nor quoted (but will be
    wrapped in parentheses, in case some awkward git decides to use the comma operator...)
    """
    dict_items = [
        indent("'%s': (%s)" % (k, v))
        for (k, v) in d.items()
    ]
    return "{\n%s\n}" % ',\n'.join(dict_items)


def recursive_deconstruct(block, with_kwargs=True):
    """
    Recursively deconstruct block definition
    """
    deconstructed = block.deconstruct()
    if not with_kwargs:
        deconstructed = deconstructed[:2]
    if hasattr(block, "child_blocks"):
        args = deconstructed[1]
        if args:
            subblocks = [
                (subblock_name, recursive_deconstruct(subblock, with_kwargs))
                for (subblock_name, subblock) in args[0]
            ]
            deconstructed = list(deconstructed)
            deconstructed[1][0] = subblocks
            deconstructed = tuple(deconstructed)
    return deconstructed
