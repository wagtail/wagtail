
django-treebeard
================

django-treebeard is a library that implements efficient tree implementations
for the Django Web Framework 1.4+, written by Gustavo Picón and licensed under
the Apache License 2.0.

django-treebeard is:

- **Flexible**: Includes 3 different tree implementations with the same API:

  1. Adjacency List
  2. Materialized Path
  3. Nested Sets

- **Fast**: Optimized non-naive tree operations
- **Easy**: Uses Django Model Inheritance with abstract classes to define your own
  models.
- **Clean**: Testable and well tested code base. Code/branch test coverage is above
  96%. Tests are available in Jenkins:

  - Test suite running on different versions of Python, Django and database
    engine: https://tabo.pe/jenkins/job/django-treebeard/
  - Code quality: https://tabo.pe/jenkins/job/django-treebeard-quality/

You can find the documentation in

    https://tabo.pe/projects/django-treebeard/docs/tip/
