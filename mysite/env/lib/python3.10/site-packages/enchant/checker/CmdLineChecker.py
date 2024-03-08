# pyenchant
#
# Copyright (C) 2004-2008, Ryan Kelly
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
# In addition, as a special exception, you are
# given permission to link the code of this program with
# non-LGPL Spelling Provider libraries (eg: a MSFT Office
# spell checker backend) and distribute linked combinations including
# the two.  You must obey the GNU Lesser General Public License in all
# respects for all of the code used other than said providers.  If you modify
# this file, you may extend this exception to your version of the
# file, but you are not obligated to do so.  If you do not wish to
# do so, delete this exception statement from your version.
#
"""

    enchant.checker.CmdLineChecker:  Command-Line spell checker

    This module provides the class CmdLineChecker, which interactively
    spellchecks a piece of text by interacting with the user on the
    command line.  It can also be run as a script to spellcheck a file.

"""

import sys

from enchant.checker import SpellChecker

# Helpers

colors = {
    "normal": "\x1b[0m",
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "purple": "\x1b[35m",
    "cyan": "\x1b[36m",
    "grey": "\x1b[90m",
    "gray": "\x1b[90m",
    "bold": "\x1b[1m",
}


def color(string, color="normal", prefix=""):
    """
    Change text color for the Linux terminal.

    Args:
        string (str): String to colorify
        color (str): Color to colorify the string in the following list:
            black, red, green, yellow, blue, purple, cyan, gr[ae]y
        prefix (str): Prefix to add to string (ex: Beginning of line graphics)
    """
    if sys.stdout.isatty():
        return colors[color] + prefix + string + colors["normal"]
    else:
        return prefix + string


def success(string):
    return "[" + color("+", color="green") + "] " + string


def error(string):
    return "[" + color("!", color="red") + "] " + string


def warning(string):
    return "[" + color("*", color="yellow") + "] " + string


def info(string):
    return "[" + color(".", color="blue") + "] " + string


class CmdLineChecker:
    """A simple command-line spell checker.

    This class implements a simple command-line spell checker.  It must
    be given a SpellChecker instance to operate on, and interacts with
    the user by printing instructions on stdout and reading commands from
    stdin.
    """

    _DOC_ERRORS = ["stdout", "stdin"]

    def __init__(self):
        self._stop = False
        self._checker = None

    def set_checker(self, chkr):
        self._checker = chkr

    def get_checker(self, chkr):
        return self._checker

    def run(self):
        """Run the spellchecking loop."""
        self._stop = False
        for err in self._checker:
            self.error = err
            self.print_error()
            self.print_suggestions()
            status = self.read_command()
            while not status and not self._stop:
                status = self.read_command()
            if self._stop:
                break

    def print_error(self):
        """print the spelling error to the console.

        Prints the misspelled word along with 100 characters of
        context on either side.  This number was arbitrarily chosen
        and could be modified to be tunable or changed entirely.
        It seems to be enough context to be helpful though
        """
        error_string = self._build_context(
            self.error.get_text(), self.error.word, self.error.wordpos
        )
        print([error("ERROR: %s" % color(self.error.word, color="red"))])
        print([info("")])
        print([info(error_string)])
        print([info("")])

    @staticmethod
    def _build_context(text, error_word, error_start):
        """creates the context line.

        This function will search forward and backward
        from the error word to find the nearest newlines.
        it will return this line with the error word
        colored red."""
        start_newline = text.rfind("\n", 0, error_start)
        end_newline = text.find("\n", error_start)
        return text[start_newline + 1 : end_newline].replace(
            error_word, color(error_word, color="red")
        )

    def print_suggestions(self):
        """Prints out the suggestions for a given error.

        This function will add vertical pipes to separate choices
        as well as the index of the replacement as expected by the replace function.
        I don't believe zero indexing is a problem as long as the user can see the numbers :)
        """
        result = ""
        suggestions = self.error.suggest()
        for index, sugg in enumerate(suggestions):
            if index == 0:
                result = (
                    result
                    + color(str(index), color="yellow")
                    + ": "
                    + color(sugg, color="bold")
                )
            else:
                result = (
                    result
                    + " | "
                    + color(str(index), color="yellow")
                    + ": "
                    + color(sugg, color="bold")
                )
        print([info("HOW ABOUT:"), result])

    def print_help(self):
        print(
            [
                info(
                    color("0", color="yellow")
                    + ".."
                    + color("N", color="yellow")
                    + ":\t"
                    + color("replace", color="bold")
                    + " with the numbered suggestion"
                )
            ]
        )
        print(
            [
                info(
                    color("R", color="cyan")
                    + color("0", color="yellow")
                    + ".."
                    + color("R", color="cyan")
                    + color("N", color="yellow")
                    + ":\t"
                    + color("always replace", color="bold")
                    + " with the numbered suggestion"
                )
            ]
        )
        print(
            [
                info(
                    color("i", color="cyan")
                    + ":\t\t"
                    + color("ignore", color="bold")
                    + " this word"
                )
            ]
        )
        print(
            [
                info(
                    color("I", color="cyan")
                    + ":\t\t"
                    + color("always ignore", color="bold")
                    + " this word"
                )
            ]
        )
        print(
            [
                info(
                    color("a", color="cyan")
                    + ":\t\t"
                    + color("add", color="bold")
                    + " word to personal dictionary"
                )
            ]
        )
        print(
            [
                info(
                    color("e", color="cyan")
                    + ":\t\t"
                    + color("edit", color="bold")
                    + " the word"
                )
            ]
        )
        print(
            [
                info(
                    color("q", color="cyan")
                    + ":\t\t"
                    + color("quit", color="bold")
                    + " checking"
                )
            ]
        )
        print(
            [
                info(
                    color("h", color="cyan")
                    + ":\t\tprint this "
                    + color("help", color="bold")
                    + " message"
                )
            ]
        )
        print([info("----------------------------------------------------")])
        self.print_suggestions()

    def read_command(self):
        cmd = input(">> ")
        cmd = cmd.strip()

        if cmd.isdigit():
            repl = int(cmd)
            suggs = self.error.suggest()
            if repl >= len(suggs):
                print([warning("No suggestion number"), repl])
                return False
            print(
                [
                    success(
                        "Replacing '%s' with '%s'"
                        % (
                            color(self.error.word, color="red"),
                            color(suggs[repl], color="green"),
                        )
                    )
                ]
            )
            self.error.replace(suggs[repl])
            return True

        if cmd[0] == "R":
            if not cmd[1:].isdigit():
                print([warning("Badly formatted command (try 'help')")])
                return False
            repl = int(cmd[1:])
            suggs = self.error.suggest()
            if repl >= len(suggs):
                print([warning("No suggestion number"), repl])
                return False
            self.error.replace_always(suggs[repl])
            return True

        if cmd == "i":
            return True

        if cmd == "I":
            self.error.ignore_always()
            return True

        if cmd == "a":
            self.error.add()
            return True

        if cmd == "e":
            repl = input(info("New Word: "))
            self.error.replace(repl.strip())
            return True

        if cmd == "q":
            self._stop = True
            return True

        if "help".startswith(cmd.lower()):
            self.print_help()
            return False

        print([warning("Badly formatted command (try 'help')")])
        return False

    def run_on_file(self, infile, outfile=None, enc=None):
        """Run spellchecking on the named file.
        This method can be used to run the spellchecker over the named file.
        If <outfile> is not given, the corrected contents replace the contents
        of <infile>.  If <outfile> is given, the corrected contents will be
        written to that file.  Use "-" to have the contents written to stdout.
        If <enc> is given, it specifies the encoding used to read the
        file's contents into a unicode string.  The output will be written
        in the same encoding.
        """
        inStr = "".join(open(infile).readlines())
        if enc is not None:
            inStr = inStr.decode(enc)
        self._checker.set_text(inStr)
        begin_msg = "Beginning spell check of %s" % infile
        print([info(begin_msg)])
        print([info("-" * len(begin_msg))])
        self.run()
        print([success("Completed spell check of %s" % infile)])
        outStr = self._checker.get_text()
        if enc is not None:
            outStr = outStr.encode(enc)
        if outfile is None:
            outF = open(infile, "w")
        elif outfile == "-":
            outF = sys.stdout
        else:
            outF = open(outfile, "w")
        outF.write(outStr)
        outF.close()

    run_on_file._DOC_ERRORS = ["outfile", "infile", "outfile", "stdout"]


def _run_as_script():
    """Run the command-line spellchecker as a script.
    This function allows the spellchecker to be invoked from the command-line
    to check spelling in a file.
    """
    # Check necessary command-line options
    from optparse import OptionParser

    op = OptionParser()
    op.add_option(
        "-o", "--output", dest="outfile", metavar="FILE", help="write changes into FILE"
    )
    op.add_option(
        "-l",
        "--lang",
        dest="lang",
        metavar="TAG",
        default="en_US",
        help="use language idenfified by TAG",
    )
    op.add_option(
        "-e",
        "--encoding",
        dest="enc",
        metavar="ENC",
        help="file is unicode with encoding ENC",
    )
    (opts, args) = op.parse_args()
    # Sanity check
    if len(args) < 1:
        raise ValueError("Must name a file to check")
    if len(args) > 1:
        raise ValueError("Can only check a single file")
    # Create and run the checker
    chkr = SpellChecker(opts.lang)
    cmdln = CmdLineChecker()
    cmdln.set_checker(chkr)
    cmdln.run_on_file(args[0], opts.outfile, opts.enc)


if __name__ == "__main__":
    _run_as_script()
