"""
Entrypoint for all 4 command-line tools. Typical usage:

    $ djhtml file1.html file2.html

Passing "-" as the filename will read from standard input and write to
standard output. Example usage:

    $ djhtml - < input.html > output.html

Passing a directory name will recurse into the directory and format
all files with typical extensions. For more fine-grained control of
which files get processed, use external tools like find, xargs or
pre-commit.

"""

import sys
from pathlib import Path

from . import modes, options


def main():
    changed_files = 0
    unchanged_files = 0
    problematic_files = 0

    # Determine mode based on script name
    script_name = Path(sys.argv[0])
    if script_name.stem == "djtxt":
        Mode = modes.DjTXT
        suffixes = [".txt"]
    elif script_name.stem == "djcss":
        Mode = modes.DjCSS
        suffixes = [".css", ".scss"]
    elif script_name.stem == "djjs":
        Mode = modes.DjJS
        suffixes = [".js"]
    else:
        Mode = modes.DjHTML
        suffixes = [".html"]

    if len(options.input_filenames) > 1 and "-" in options.input_filenames:
        sys.exit("I’m sorry Dave, I’m afraid I can’t do that.")

    for filename in _generate_filenames(options.input_filenames, suffixes):
        # Read input file
        try:
            if filename == "-":
                source = sys.stdin.read()
            else:
                with open(filename) as input_file:
                    source = input_file.read()
        except Exception as e:
            problematic_files += 1
            _error(e)
            continue

        # Guess tabwidth
        if not options.tabwidth:
            prev = 0
            probabilities = [0] * 9
            for line in source.splitlines():
                if line and not line.isspace():
                    depth = _get_depth(line)
                    if abs(depth - prev) in [2, 4, 8]:
                        probabilities[abs(depth - prev)] += 1
                    prev = depth
            guess = probabilities.index(max(probabilities))

        # Indent input file
        try:
            result = Mode(source).indent(options.tabwidth or guess or 4)
        except modes.MaxLineLengthExceeded:
            problematic_files += 1
            _error(f"Maximum line length exceeded in {filename}")
            continue
        except Exception:
            _error(
                f"Fatal error while processing {filename}\n\n"
                "    If you have time and are using the latest version, we\n"
                "    would very much appreciate if you opened an issue on\n"
                "    https://github.com/rtts/djhtml/issues\n"
            )
            raise

        if changed := _verify_changed(source, result):
            changed_files += 1
        else:
            unchanged_files += 1

        # Write output file
        if not options.check:
            if filename == "-":
                print(result, end="")
            elif changed:
                try:
                    with open(filename, "w") as output_file:
                        output_file.write(result)
                except Exception as e:
                    changed_files -= 1
                    problematic_files += 1
                    _error(e)
                    continue
                _info(f"reindented {output_file.name}")
        elif changed and filename != "-":
            _info(f"would have reindented {filename}")

    # Print final summary
    s = "s" if changed_files != 1 else ""
    have = "would have" if options.check else "have" if s else "has"
    _info(f"{changed_files} template{s} {have} been reindented.")
    if unchanged_files:
        s = "s" if unchanged_files != 1 else ""
        were = "were" if s else "was"
        _info(f"{unchanged_files} template{s} {were} already perfect!")
    if problematic_files:
        s = "s" if problematic_files != 1 else ""
        _info(
            f"{problematic_files} template{s} could not be processed due to an error."
        )

    if options.debug:
        print(Mode(source).debug(), file=sys.stderr)

    # Exit with appropriate exit status
    if problematic_files:
        sys.exit(123)
    if options.check and changed_files:
        sys.exit(1)
    sys.exit(0)


def _generate_filenames(paths, suffixes):
    for filename in paths:
        if filename == "-":
            yield filename
        else:
            path = Path(filename)
            if path.is_dir():
                yield from _generate_filenames_from_directory(path, suffixes)
            else:
                yield path


def _generate_filenames_from_directory(directory, suffixes):
    for path in directory.iterdir():
        if path.is_file() and path.suffix in suffixes:
            yield path
        elif path.is_dir():
            yield from _generate_filenames_from_directory(path, suffixes)


def _verify_changed(source, result):
    output_lines = result.split("\n")
    changed = False
    for line_nr, line in enumerate(source.split("\n")):
        if line != output_lines[line_nr]:
            changed = True
        if line.strip() != output_lines[line_nr].strip():
            raise IndentationError("Non-whitespace changes detected. Core dumped.")
    return changed


def _get_depth(line):
    count = 0
    for char in line:
        if char == " ":
            count += 1
        elif char == "\t":
            count += 4
        else:
            break
    return count


def _info(msg):
    print(msg, file=sys.stderr)


def _error(msg):
    _info(f"Error: {msg}")


if __name__ == "__main__":
    main()
