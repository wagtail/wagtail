import argparse
import itertools
import logging
import os
import random
import sys
import textwrap

from io import TextIOWrapper
from pathlib import Path
from typing import Dict, List, Optional, TextIO, TypeVar, Union

from . import VERSION, Faker, documentor, exceptions
from .config import AVAILABLE_LOCALES, DEFAULT_LOCALE, META_PROVIDERS_MODULES
from .documentor import Documentor
from .providers import BaseProvider

__author__ = "joke2k"

T = TypeVar("T")


def print_provider(
    doc: Documentor,
    provider: BaseProvider,
    formatters: Dict[str, T],
    excludes: Optional[List[str]] = None,
    output: Optional[TextIO] = None,
) -> None:
    if output is None:
        output = sys.stdout
    if excludes is None:
        excludes = []

    print(file=output)
    print(f"### {doc.get_provider_name(provider)}", file=output)
    print(file=output)

    margin = max(30, doc.max_name_len + 2)
    for signature, example in formatters.items():
        if signature in excludes:
            continue
        signature_lines = textwrap.wrap(signature, width=margin, subsequent_indent="  ")
        try:
            lines = textwrap.wrap(
                str(example).expandtabs(),
                width=150 - margin,
                initial_indent="# ",
                subsequent_indent="  ",
            )
        except UnicodeDecodeError:
            # The example is actually made of bytes.
            # We could coerce to bytes, but that would fail anyway when we wiil
            # try to `print` the line.
            lines = ["<bytes>"]
        except UnicodeEncodeError:
            raise Exception(f"error on {signature!r} with value {example!r}")
        for left, right in itertools.zip_longest(signature_lines, lines, fillvalue=""):
            print(f"\t{left:<{margin}}  {right}", file=output)


def print_doc(
    provider_or_field: Optional[str] = None,
    args: Optional[List[T]] = None,
    lang: str = DEFAULT_LOCALE,
    output: Optional[Union[TextIO, TextIOWrapper]] = None,
    seed: Optional[float] = None,
    includes: Optional[List[str]] = None,
) -> None:
    if args is None:
        args = []
    if output is None:
        output = sys.stdout
    fake = Faker(locale=lang, includes=includes)
    fake.seed_instance(seed)

    from faker.providers import BaseProvider

    base_provider_formatters = list(dir(BaseProvider))

    if provider_or_field:
        if "." in provider_or_field:
            parts = provider_or_field.split(".")
            locale = parts[-2] if parts[-2] in AVAILABLE_LOCALES else lang
            fake = Faker(locale, providers=[provider_or_field], includes=includes)
            fake.seed_instance(seed)
            doc = documentor.Documentor(fake)
            doc.already_generated = base_provider_formatters
            print_provider(
                doc,
                fake.get_providers()[0],
                doc.get_provider_formatters(fake.get_providers()[0]),
                output=output,
            )
        else:
            try:
                print(fake.format(provider_or_field, *args), end="", file=output)
            except AttributeError:
                raise ValueError(f'No faker found for "{provider_or_field}({args})"')

    else:
        doc = documentor.Documentor(fake)
        unsupported: List[str] = []

        while True:
            try:
                formatters = doc.get_formatters(with_args=True, with_defaults=True, excludes=unsupported)
            except exceptions.UnsupportedFeature as e:
                unsupported.append(e.name)
            else:
                break

        for provider, fakers in formatters:
            print_provider(doc, provider, fakers, output=output)


class Command:
    def __init__(self, argv: Optional[str] = None) -> None:
        self.argv = argv or sys.argv[:]
        self.prog_name = Path(self.argv[0]).name

    def execute(self) -> None:
        """
        Given the command-line arguments, this creates a parser appropriate
        to that command, and runs it.
        """

        # retrieve default language from system environment
        default_locale = os.environ.get("LANG", "en_US").split(".")[0]
        if default_locale not in AVAILABLE_LOCALES:
            default_locale = DEFAULT_LOCALE

        epilog = f"""supported locales:

  {', '.join(sorted(AVAILABLE_LOCALES))}

  Faker can take a locale as an optional argument, to return localized data. If
  no locale argument is specified, the factory falls back to the user's OS
  locale as long as it is supported by at least one of the providers.
     - for this user, the default locale is {default_locale}.

  If the optional argument locale and/or user's default locale is not available
  for the specified provider, the factory falls back to faker's default locale,
  which is {DEFAULT_LOCALE}.

examples:

  $ faker address
  968 Bahringer Garden Apt. 722
  Kristinaland, NJ 09890

  $ faker -l de_DE address
  Samira-Niemeier-Allee 56
  94812 Biedenkopf

  $ faker profile ssn,birthdate
  {{'ssn': u'628-10-1085', 'birthdate': '2008-03-29'}}

  $ faker -r=3 -s=";" name
  Willam Kertzmann;
  Josiah Maggio;
  Gayla Schmitt;

"""

        formatter_class = argparse.RawDescriptionHelpFormatter
        parser = argparse.ArgumentParser(
            prog=self.prog_name,
            description=f"{self.prog_name} version {VERSION}",
            epilog=epilog,
            formatter_class=formatter_class,
        )

        parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="show INFO logging events instead "
            "of CRITICAL, which is the default. These logging "
            "events provide insight into localization of "
            "specific providers.",
        )

        parser.add_argument(
            "-o",
            metavar="output",
            type=argparse.FileType("w"),
            default=sys.stdout,
            help="redirect output to a file",
        )

        parser.add_argument(
            "-l",
            "--lang",
            choices=AVAILABLE_LOCALES,
            default=default_locale,
            metavar="LOCALE",
            help="specify the language for a localized " "provider (e.g. de_DE)",
        )
        parser.add_argument(
            "-r",
            "--repeat",
            default=1,
            type=int,
            help="generate the specified number of outputs",
        )
        parser.add_argument(
            "-s",
            "--sep",
            default="\n",
            help="use the specified separator after each " "output",
        )

        parser.add_argument(
            "--seed",
            metavar="SEED",
            type=int,
            help="specify a seed for the random generator so "
            "that results are repeatable. Also compatible "
            "with 'repeat' option",
        )

        parser.add_argument(
            "-i",
            "--include",
            default=META_PROVIDERS_MODULES,
            nargs="*",
            help="list of additional custom providers to "
            "user, given as the import path of the module "
            "containing your Provider class (not the provider "
            "class itself)",
        )

        parser.add_argument(
            "fake",
            action="store",
            nargs="?",
            help="name of the fake to generate output for " "(e.g. profile)",
        )

        parser.add_argument(
            "fake_args",
            metavar="fake argument",
            action="store",
            nargs="*",
            help="optional arguments to pass to the fake "
            "(e.g. the profile fake takes an optional "
            "list of comma separated field names as the "
            "first argument)",
        )

        arguments = parser.parse_args(self.argv[1:])

        if arguments.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.CRITICAL)

        random.seed(arguments.seed)
        seeds = [random.random() for _ in range(arguments.repeat)]

        for i in range(arguments.repeat):
            print_doc(
                arguments.fake,
                arguments.fake_args,
                lang=arguments.lang,
                output=arguments.o,
                seed=seeds[i],
                includes=arguments.include,
            )
            print(arguments.sep, file=arguments.o)

            if not arguments.fake:
                # repeat not supported for all docs
                break


def execute_from_command_line(argv: Optional[str] = None) -> None:
    """A simple method that runs a Command."""
    if sys.stdout.encoding is None:
        print(
            "please set python env PYTHONIOENCODING=UTF-8, example: "
            "export PYTHONIOENCODING=UTF-8, when writing to stdout",
            file=sys.stderr,
        )
        exit(1)

    command = Command(argv)
    command.execute()


if __name__ == "__main__":
    execute_from_command_line()
