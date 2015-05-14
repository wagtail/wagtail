Python coding guidelines
========================

* PEP8. We ask that all Python contributions adhere to the `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ style guide, apart from the restriction on line length (E501). The `pep8 tool <http://pep8.readthedocs.org/en/latest/>`_ makes it easy to check your code, e.g. ``pep8 --ignore=E501 your_file.py``.
* Python 2 and 3 compatibility. All contributions should support Python 2 and 3 and we recommend using the `six <https://pythonhosted.org/six/>`_ compatibility library (use the pip version installed as a dependency, not the version bundled with Django).
* Tests. Wagtail has a suite of tests, which we are committed to improving and expanding. We run continuous integration at `travis-ci.org/torchbox/wagtail <https://travis-ci.org/torchbox/wagtail>`_ to ensure that no commits or pull requests introduce test failures. If your contributions add functionality to Wagtail, please include the additional tests to cover it; if your contributions alter existing functionality, please update the relevant tests accordingly.
