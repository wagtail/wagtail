"""Build the GitHub Actions job summary for the latest-deps CI workflow.

For each package listed in .github/latest-deps-overrides.txt, look up the
constraint declared in pyproject.toml and the version installed in the current
environment. Packages that resolved to a version outside their cap are shown
prominently — they are the actionable signal that the cap may be safe to lift.
The rest are folded into a collapsed details block.

Markdown output goes to stdout, to be appended to $GITHUB_STEP_SUMMARY.
"""

# ruff: noqa: T201

from importlib.metadata import PackageNotFoundError, version

import tomllib
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

with open(".github/latest-deps-overrides.txt") as f:
    overridden = set()
    for raw in f:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        overridden.add(canonicalize_name(Requirement(line).name))

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

deps = list(data["project"].get("dependencies", []))
for extra_deps in data["project"].get("optional-dependencies", {}).values():
    deps.extend(extra_deps)

caps = {}
for dep_str in deps:
    req = Requirement(dep_str)
    if canonicalize_name(req.name) in overridden:
        caps[canonicalize_name(req.name)] = req

exceeded = []
within = []
for canonical in sorted(overridden):
    req = caps.get(canonical)
    if req is None:
        continue
    try:
        resolved = Version(version(req.name))
    except PackageNotFoundError:
        continue
    row = (req.name, str(req.specifier), str(resolved))
    if req.specifier.contains(resolved, prereleases=True):
        within.append(row)
    else:
        exceeded.append(row)

if exceeded:
    print("## Resolved past the cap")
    print()
    print(
        "These packages resolved to a version outside their bound in "
        "`pyproject.toml`. If this run is green, the cap may be safe to extend."
    )
    print()
    print("| Package | Cap | Resolved |")
    print("| --- | --- | --- |")
    for name, cap, resolved in exceeded:
        print(f"| `{name}` | `{cap}` | **`{resolved}`** |")
    print()
else:
    print("## Resolved versions of capped dependencies")
    print()
    print("No overridden package resolved past its cap this run.")
    print()

if within:
    print("<details><summary>Resolved within the existing cap</summary>")
    print()
    print("| Package | Cap | Resolved |")
    print("| --- | --- | --- |")
    for name, cap, resolved in within:
        print(f"| `{name}` | `{cap}` | `{resolved}` |")
    print()
    print("</details>")
