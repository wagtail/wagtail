
import os
import sys
import array
import textwrap

from boltons.iterutils import unique, split

from face.utils import format_flag_label, format_flag_post_doc, format_posargs_label, echo
from face.parser import Flag

DEFAULT_HELP_FLAG = Flag('--help', parse_as=True, char='-h', doc='show this help message and exit')
DEFAULT_MAX_WIDTH = 120


def _get_termios_winsize():
    # TLPI, 62.9 (p. 1319)
    import fcntl
    import termios

    winsize = array.array('H', [0, 0, 0, 0])

    assert not fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, winsize)

    ws_row, ws_col, _, _ = winsize

    return ws_row, ws_col


def _get_environ_winsize():
    # the argparse approach. not sure which systems this works or
    # worked on, if any. ROWS/COLUMNS are special shell variables.
    try:
        rows, columns = int(os.environ['ROWS']), int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        rows, columns = None, None
    return rows, columns


def get_winsize():
    rows, cols = None, None
    try:
        rows, cols = _get_termios_winsize()
    except Exception:
        try:
            rows, cols = _get_environ_winsize()
        except Exception:
            pass
    return rows, cols


def get_wrap_width(max_width=DEFAULT_MAX_WIDTH):
    _, width = get_winsize()
    if width is None:
        width = 80
    width = min(width, max_width)
    width -= 2
    return width


def _wrap_stout_pair(indent, label, sep, doc, doc_start, max_doc_width):
    # TODO: consider making the fill character configurable (ljust
    # uses space by default, the just() methods can only take
    # characters, might be a useful bolton to take a repeating
    # sequence)
    ret = []
    append = ret.append
    lhs = indent + label

    if not doc:
        append(lhs)
        return ret

    len_sep = len(sep)
    wrapped_doc = textwrap.wrap(doc, max_doc_width)
    if len(lhs) <= doc_start:
        lhs_f = lhs.ljust(doc_start - len(sep)) + sep
        append(lhs_f + wrapped_doc[0])
    else:
        append(lhs)
        append((' ' * (doc_start - len_sep)) + sep + wrapped_doc[0])

    for line in wrapped_doc[1:]:
        append(' ' * doc_start + line)

    return ret


def _wrap_stout_cmd_doc(indent, doc, max_width):
    """Function for wrapping command description."""
    parts = []
    paras = ['\n'.join(para) for para in
             split(doc.splitlines(), lambda l: not l.lstrip())
             if para]
    for para in paras:
        part = textwrap.fill(text=para,
                             width=(max_width - len(indent)),
                             initial_indent=indent,
                             subsequent_indent=indent)
        parts.append(part)
    return '\n\n'.join(parts)


def get_stout_layout(labels, indent, sep, width=None, max_width=DEFAULT_MAX_WIDTH,
                     min_doc_width=40):
    width = width or get_wrap_width(max_width=max_width)

    len_sep = len(sep)
    len_indent = len(indent)

    max_label_width = 0
    max_doc_width = min_doc_width
    doc_start = width - min_doc_width
    for label in labels:
        cur_len = len(label)
        if cur_len < max_label_width:
            continue
        max_label_width = cur_len
        if (len_indent + cur_len + len_sep + min_doc_width) < width:
            max_doc_width = width - max_label_width - len_sep - len_indent
            doc_start = len_indent + cur_len + len_sep

    return {'width': width,
            'label_width': max_label_width,
            'doc_width': max_doc_width,
            'doc_start': doc_start}


DEFAULT_CONTEXT = {
    'usage_label': 'Usage:',
    'subcmd_section_heading': 'Subcommands: ',
    'flags_section_heading': 'Flags: ',
    'posargs_section_heading': 'Positional arguments:',
    'section_break': '\n',
    'group_break': '',
    'subcmd_example': 'subcommand',
    'width': None,
    'max_width': 120,
    'min_doc_width': 50,
    'format_posargs_label': format_posargs_label,
    'format_flag_label': format_flag_label,
    'format_flag_post_doc': format_flag_post_doc,
    'doc_separator': '   ',  # '   + ' is pretty classy as bullet points, too
    'section_indent': '  ',
    'pre_doc': '',  # TODO: these should go on CommandDisplay
    'post_doc': '\n',
}


class StoutHelpFormatter(object):
    """This formatter takes :class:`Parser` and :class:`Command` instances
    and generates help text. The output style is inspired by, but not
    the same as, argparse's automatic help formatting.

    Probably what most Pythonists expect, this help text is slightly
    stouter (conservative with vertical space) than other conventional
    help messages.

    The default output looks like::

        Usage: example.py subcommand [FLAGS]

        Does a bit of busy work


        Subcommands:

          sum        Just a lil fun in the sum
          subtract
          print


        Flags:

          --help / -h               show this help message and exit
          --verbose / -V


    Due to customizability, the constructor takes a large number of
    keyword arguments, the most important of which are highlighted
    here.

    Args:
       width (int): The width of the help output in
          columns/characters. Defaults to the width of the terminal,
          with a max of *max_width*.
       max_width (int): The widest the help output will get. Too wide
          and it can be hard to visually scan. Defaults to 120 columns.
       min_doc_width (int): The text documentation's minimum width in
          columns/characters. Puts flags and subcommands on their own
          lines when they're long or the terminal is narrow. Defaults to
          50.
       doc_separator (str): The string to put between a
          flag/subcommand and its documentation. Defaults to `' '`. (Try
          `' + '` for a classy bulleted doc style.

    An instance of StoutHelpFormatter can be passed to
    :class:`HelpHandler`, which can in turn be passed to
    :class:`Command` for maximum command customizability.

    Alternatively, when using :class:`Parser` object directly, you can
    instantiate this type and pass a :class:`Parser` object to
    :meth:`get_help_text()` or :meth:`get_usage_line()` to get
    identically formatted text without sacrificing flow control.

    HelpFormatters are stateless, in that they can be used more than
    once, with different Parsers and Commands without needing to be
    recreated or otherwise reset.

    """
    default_context = dict(DEFAULT_CONTEXT)

    def __init__(self, **kwargs):
        self.ctx = {}
        for key, val in self.default_context.items():
            self.ctx[key] = kwargs.pop(key, val)
        if kwargs:
            raise TypeError('unexpected formatter arguments: %r' % list(kwargs.keys()))

    def _get_layout(self, labels):
        ctx = self.ctx
        return get_stout_layout(labels=labels,
                                indent=ctx['section_indent'],
                                sep=ctx['doc_separator'],
                                width=ctx['width'],
                                max_width=ctx['max_width'],
                                min_doc_width=ctx['min_doc_width'])

    def get_help_text(self, parser, subcmds=(), program_name=None):
        """Turn a :class:`Parser` or :class:`Command` into a multiline
        formatted help string, suitable for printing. Includes the
        usage line and trailing newline by default.

        Args:
           parser (Parser): A :class:`Parser` or :class:`Command`
              object to generate help text for.
           subcmds (tuple): A sequence of subcommand strings
              specifying the subcommand to generate help text for.
              Defaults to ``()``.
           program_name (str): The program name, if it differs from
              the default ``sys.argv[0]``. (For example,
              ``example.py``, when running the command ``python
              example.py --flag val arg``.)

        """
        # TODO: incorporate "Arguments" section if posargs has a doc set
        ctx = self.ctx

        ret = [self.get_usage_line(parser, subcmds=subcmds, program_name=program_name)]
        append = ret.append
        append(ctx['group_break'])

        shown_flags = parser.get_flags(path=subcmds, with_hidden=False)
        if subcmds:
            parser = parser.subprs_map[subcmds]

        if parser.doc:
            append(_wrap_stout_cmd_doc(indent=ctx['section_indent'],
                                       doc=parser.doc,
                                       max_width=ctx['width'] or get_wrap_width(
                                           max_width=ctx['max_width'])))
            append(ctx['section_break'])

        if parser.subprs_map:
            subcmd_names = unique([sp[0] for sp in parser.subprs_map if sp])
            subcmd_layout = self._get_layout(labels=subcmd_names)

            append(ctx['subcmd_section_heading'])
            append(ctx['group_break'])
            for sub_name in unique([sp[0] for sp in parser.subprs_map if sp]):
                subprs = parser.subprs_map[(sub_name,)]
                # TODO: sub_name.replace('_', '-') = _cmd -> -cmd (need to skip replacing leading underscores)
                subcmd_lines = _wrap_stout_pair(indent=ctx['section_indent'],
                                                label=sub_name.replace('_', '-'),
                                                sep=ctx['doc_separator'],
                                                doc=subprs.doc,
                                                doc_start=subcmd_layout['doc_start'],
                                                max_doc_width=subcmd_layout['doc_width'])
                ret.extend(subcmd_lines)

            append(ctx['section_break'])

        if not shown_flags:
            return '\n'.join(ret)

        fmt_flag_label = ctx['format_flag_label']
        flag_labels = [fmt_flag_label(flag) for flag in shown_flags]
        flag_layout = self._get_layout(labels=flag_labels)

        fmt_flag_post_doc = ctx['format_flag_post_doc']
        append(ctx['flags_section_heading'])
        append(ctx['group_break'])
        for flag in shown_flags:
            disp = flag.display
            if disp.full_doc is not None:
                doc = disp.full_doc
            else:
                _parts = [disp.doc] if disp.doc else []
                post_doc = disp.post_doc if disp.post_doc else fmt_flag_post_doc(flag)
                if post_doc:
                    _parts.append(post_doc)
                doc = ' '.join(_parts)

            flag_lines = _wrap_stout_pair(indent=ctx['section_indent'],
                                          label=fmt_flag_label(flag),
                                          sep=ctx['doc_separator'],
                                          doc=doc,
                                          doc_start=flag_layout['doc_start'],
                                          max_doc_width=flag_layout['doc_width'])

            ret.extend(flag_lines)

        return ctx['pre_doc'] + '\n'.join(ret) + ctx['post_doc']

    def get_usage_line(self, parser, subcmds=(), program_name=None):
        """Get just the top line of automated text output. Arguments are the
        same as :meth:`get_help_text()`. Basic info about running the
        command, such as:

           Usage: example.py subcommand [FLAGS] [args ...]

        """
        ctx = self.ctx
        subcmds = tuple(subcmds or ())
        parts = [ctx['usage_label']] if ctx['usage_label'] else []
        append = parts.append

        program_name = program_name or parser.name

        append(' '.join((program_name,) + subcmds))

        # TODO: put () in subprs_map to handle some of this sorta thing
        if not subcmds and parser.subprs_map:
            append('subcommand')
        elif subcmds and parser.subprs_map[subcmds].subprs_map:
            append('subcommand')

        # with subcommands out of the way, look up the parser for flags and args
        if subcmds:
            parser = parser.subprs_map[subcmds]

        flags = parser.get_flags(with_hidden=False)

        if flags:
            append('[FLAGS]')

        if not parser.posargs.display.hidden:
            fmt_posargs_label = ctx['format_posargs_label']
            append(fmt_posargs_label(parser.posargs))

        return ' '.join(parts)



'''
class AiryHelpFormatter(object):
    """No wrapping a doc onto the same line as the label. Just left
    aligned labels + newline, then right align doc. No complicated
    width calculations either. See https://github.com/kbknapp/clap-rs
    """
    pass  # TBI
'''


class HelpHandler(object):
    """The HelpHandler is a one-stop object for that all-important CLI
    feature: automatic help generation. It ties together the actual
    help handler with the optional flag and subcommand such that it
    can be added to any :class:`Command` instance.

    The :class:`Command` creates a HelpHandler instance by default,
    and its constructor also accepts an instance of this type to
    customize a variety of helpful features.

    Args:
       flag (face.Flag): The Flag instance to use for triggering a
          help output in a Command setting. Defaults to the standard
          ``--help / -h`` flag. Pass ``False`` to disable.
       subcmd (str): A subcommand name to be added to any
          :class:`Command` using this HelpHandler. Defaults to
          ``None``.
       formatter: A help formatter instance or type. Type will be
          instantiated with keyword arguments passed to this
          constructor. Defaults to :class:`StoutHelpFormatter`.
       func (callable): The actual handler function called on flag
          presence or subcommand invocation. Defaults to
          :meth:`HelpHandler.default_help_func()`.

    All other remaining keyword arguments are used to construct the
    HelpFormatter, if *formatter* is a type (as is the default). For
    an example of a formatter, see :class:`StoutHelpFormatter`, the
    default help formatter.
    """
    # Other hooks (besides the help function itself):
    # * Callbacks for unhandled exceptions
    # * Callbacks for formatting errors (add a "see --help for more options")

    def __init__(self, flag=DEFAULT_HELP_FLAG, subcmd=None,
                 formatter=StoutHelpFormatter, func=None, **formatter_kwargs):
        # subcmd expects a string
        self.flag = flag
        self.subcmd = subcmd
        self.func = func if func is not None else self.default_help_func
        if not callable(self.func):
            raise TypeError('expected help handler func to be callable, not %r' % func)

        self.formatter = formatter
        if not formatter:
            raise TypeError('expected Formatter type or instance, not: %r' % formatter)
        if isinstance(formatter, type):
            self.formatter = formatter(**formatter_kwargs)
        elif formatter_kwargs:
            raise TypeError('only accepts extra formatter kwargs (%r) if'
                            ' formatter argument is a Formatter type, not: %r'
                            % (sorted(formatter_kwargs.keys()), formatter))
        _has_get_help_text = callable(getattr(self.formatter, 'get_help_text', None))
        if not _has_get_help_text:
            raise TypeError('expected valid formatter, or other object with a'
                            ' get_help_text() method, not %r' % (self.formatter,))
        return

    def default_help_func(self, cmd_, subcmds_, args_, command_):
        """The default help handler function. Called when either the help flag
        or subcommand is passed.

        Prints the output of the help formatter instance attached to
        this HelpHandler and exits with exit code 0.

        """
        echo(self.formatter.get_help_text(command_, subcmds=subcmds_, program_name=cmd_))


"""Usage: cmd_name sub_cmd [..as many subcommands as the max] --flags args ...

Possible commands:

(One of the possible styles below)

Flags:
  Group name (if grouped):
    -F, --flag VALUE      Help text goes here. (integer, defaults to 3)

Flag help notes:

* don't display parenthetical if it's string/None
* Also need to indicate required and mutual exclusion ("not with")
* Maybe experimental / deprecated support
* General flag listing should also include flags up the chain

Subcommand listing styles:

* Grouped, one-deep, flag overview on each
* One-deep, grouped or alphabetical, help string next to each
* Grouped by tree (new group whenever a subtree of more than one
  member finishes), with help next to each.

What about extra lines in the help (like zfs) (maybe each individual
line can be a template string?)

TODO: does face need built-in support for version subcommand/flag,
basically identical to help?

Group names can be ints or strings. When, group names are strings,
flags are indented under a heading consisting of the string followed
by a colon. All ungrouped flags go under a 'General Flags' group
name. When group names are ints, groups are not indented, but a
newline is still emitted by each group.

Alphabetize should be an option, otherwise everything stays in
insertion order.

Subcommands without handlers should not be displayed in help. Also,
their implicit handler prints the help.

Subcommand groups could be Commands with name='', and they can only be
added to other commands, where they would embed as siblings instead of
as subcommands. Similar to how clastic subapplications can be mounted
without necessarily adding to the path.

Is it better to delegate representations out or keep them all within
the help builder?

---

Help needs: a flag (and a way to disable it), as well as a renderer.

Usage:

Doc

Subcommands:

...   ...

Flags:

...

Postdoc


{usage_label} {cmd_name} {subcmd_path} {subcmd_blank} {flags_blank} {posargs_label}

{cmd.doc}

{subcmd_heading}

  {subcmd.name}   {subcmd.doc} {subcmd.post_doc}

{flags_heading}

  {group_name}:

    {flag_label}   {flag.doc} {flag.post_doc}

{cmd.post_doc}


--------

# Grouping

Effectively sorted on: (group_name, group_index, sort_order, label)

But group names should be based on insertion order, with the
default-grouped/ungrouped items showing up in the last group.

# Wrapping / Alignment

Docs start at the position after the longest "left-hand side"
(LHS/"key") item that would not cause the first line of the docs to be
narrower than the minimum doc width.

LHSes which do extend beyond this point will be on their own line,
with the doc starting on the line below.

# Window width considerations

With better termios-based logic in place to get window size, there are
going to be a lot of wider-than-80-char help messages.

The goal of help message alignment is to help eyes track across from a
flag or subcommand to its corresponding doc. Rather than maximizing
width usage or topping out at a max width limit, we should be
balancing or at least limiting the amount of whitespace between the
shortest flag and its doc.  (TODO)

A width limit might still make sense because reading all the way
across the screen can be tiresome, too.

TODO: padding_top and padding_bottom attributes on various displays
(esp FlagDisplay) to enable finer grained whitespace control without
complicated group setups.

"""
