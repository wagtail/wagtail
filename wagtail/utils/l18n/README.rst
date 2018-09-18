l18n
====

|copyright| 2014-2016 Thomas Khyn

Locale internationalization package. Translations for places, timezones ...

Tested with the latest minor versions of Python 2 and 3.

Supported languages: English, French, German, Czech, Chinese
(`want to add yours?`_)


What is l18n?
-------------

As you may have noticed, ``l18n`` is a contraction of ``i18n`` and ``l10n``,
namely 'internationalisation' and 'localization'. It basically provides
lazy translations for names used for localization purposes (e.g. places and
timezones).

I started writing ``l18n`` when I was looking for translations for the pytz_
library. Indeed, on a multi-lingual site where users can select the timezone
they are in, it's much better if they can select in their language, as in some
cases, the differences with the english name can be significant, hence the
place to look for it when it's sorted in alphabetical order.

And as I am lazy, I thought of a way to - almost - automatically fetch the
translations from the CLDR_ (Unicode's Common Locale Data Repository) database.

Integrating function to link timezone to country codes, there was no reason not
to try and provide translations also for the latter. In the near future, I -
or contributors - may also add currencies or measurement units fetched from
the CLDR database ...


How does it work?
-----------------

To use ``l18n``, you first need to install it. It works well with ``pip``::

   pip install l18n

Then, in your code::

   >>> import l18n

``l18n`` exposes several read-only dictionary-like objects:

l18n.tz_cities

   is a mapping between all the timezones listed in ``pytz.all_timezones``
   and human-friendly **lazy** versions of the translated name of the city
   in the current language (see `Selecting the language`_ below). For example,
   if the language is English::

      >>> l18n.tz_cities['Pacific/Easter']
      L18NLazyString <Easter Island>
      >>> str(l18n.tz_cities['Pacific/Easter'])
      'Easter Island'

   In French, it would give::

      >>> str(l18n.tz_cities['Pacific/Easter'])
      'Île de Pâques'

l18n.tz_fullnames

   is a mapping between all the timezones listed in ``pytz.all_timezones``
   and **lazy** versions of the timezones' full names in the current language.
   For example::

      >>> str(l18n.tz_fullnames['Pacific/Easter'])
      'Pacific/Easter Island'  # or 'Pacifique/Île de Pâques' in French

   It is interesting to note that for 3-components timezone names where the
   local state or territory appears in the city name, ``l18n`` cleverly strips
   this information so that it is not repeated::

      >>> str(l18n.tz_fullnames['America/North_Dakota/New_Salem'])
      'America/North Dakota/New Salem'

   indeed::

      >>> str(l18n.tz_cities['America/North_Dakota/New_salem'])
      'New Salem, North Dakota'

l18n.territories

   is a mapping between the territory codes as defined in the CLDR_ and their
   localized names, lazily defined. For example::

      >>> str(l18n.territories['CZ'])
      'Czech Republic'  # or 'République Tchèque' in French


.. note::

   The values are translated each time they are evaluated, there is no caching.
   This means that the same L18NLazyString / L18NLazyStringsList instance can
   be used and produce 2 different outputs if you change the language between
   the evaluations.


.. note::

   The values in the above mentionned dictionaries can be overriden by your
   own translations. The dictionaries are not read-only and values can be
   added or removed at your convenience.


Lazy mappings special features (v.2016.6.3 onwards)
---------------------------------------------------

The fore-mentioned ``tz_cities``, ``tz_fullnames`` and ``territories`` are not
simple dictionaries and provide additional features.

Sorting
.......

When iterating over an ``L18NMap``, the items, keys or values are *yielded* in
alphabetical order **in the currently selected language**. For performance, the
results are cached by language, so the sort is only performed once per language.
Note that the values are still lazy objects that are evaluated only when
rendered into a string.

Subsets
.......

It is possible to generate a new ``L18NMap`` from an existing one by using the
``subset`` method and passing an iterable of ``keys`` that need to be kept in
the new mapping. Any cached sort is also used to generate the new cache, so
that there is nothing to re-calculate in the new subset.

For example, one can generate a map of translations for
``pytz.common_timezones``::

   >>> common_cities = l18n.tz_cities.subset(pytz.common_timezones.keys())


Selecting the language
----------------------

By default, when importing ``l18n``, the current default locale is used (via
``locale.getdefaultlocale()``). If it is not the one you want or if you need to
change it, it is rather easy::

   >>> l18n.set_language('en')
   >>> str(l18n.tz_cities['Pacific/Easter'])
   'Easter Island'
   >>> l18n.set_language('fr')
   >>> str(l18n.tz_cities['Pacific/Easter'])
   'Île de Pâques'

And in case you want to disable translation and use raw default strings::

   >>> l18n.set_language(None)


Utilities
---------

``l18n`` also exposes a few functions that may be helpful in some cases:

``l18n.utils.get_country_tzs(country_code)``

   returns a list of locations for the given country code, sorted in
   alphabetical order in the currently selected language

``l18n.utils.get_country_code_from_tz(timezone)``

   returns the country code from a given (untranslated) timezone


Versionning
-----------

``l18n``'s main version number matches ``pytz``'s version number. ``l18n``
2014.10.X will be fully compatible with ``pytz`` 2014.10 whatever the value of
X. Indeed, the primary aim is to keep ``l18n``'s translation files consistent
with ``pytz``'s timezone names.

Before ``l18n`` 2016.6, the ``pytz`` version was pinned against the ``l18n``
version. Now, ``l18n`` YEAR.MONTH can now be used with any subsequent ``pytz``
version. However, note that there may be missing translations if the 2 versions
are too different from each other. In that case, open an issue_ to request a
new version of ``l18n`` to be published.


.. _`want to add yours?`:

Want to add a language?
-----------------------

Great idea !! Have a look at CONTRIBUTE.rst_.


Roadmap
-------

- Add supported languages
- Add currencies and other stuff


.. |copyright| unicode:: 0xA9

.. _pytz: https://pypi.python.org/pypi/pytz/
.. _CLDR: http://cldr.unicode.org/
.. _CONTRIBUTE.rst: https://bitbucket.org/tkhyn/l18n/src/tip/CONTRIBUTE.rst
.. _issue: https://bitbucket.org/tkhyn/l18n/issues/new
