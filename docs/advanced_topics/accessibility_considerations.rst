Accessibility considerations
============================

Accessibility for CMS-driven websites is a matter of :ref:`modeling content appropriately <content_modeling>`, :ref:`creating accessible templates <accessibility_in_templates>`, and :ref:`authoring content <authoring_accessible_content>` with readability and accessibility guidelines in mind. Wagtail generally puts developers in control of content modeling and front-end markup, but there are a few areas to be aware of nonetheless, and ways to help authors be aware of readability best practices.

* :ref:`Content modeling <content-modeling>`
* :ref:`Accessibility in templates <accessibility-in-templates>`
* :ref:`Authoring accessible content <authoring-accessible-content>`

.. _content_modeling:

Content modeling
~~~~~~~~~~~~~~~~

As part of defining your site’s models, here are areas to pay special attention to:

Images’ alt text
----------------

- alt text. Where it comes from in Wagtail (the `title` field by default). How to change that.
- With [guidance](https://axesslab.com/alt-texts/) on when you need alt text
- https://github.com/wagtail/rfcs/pull/51
- Images in rich text can override the alt text. Some implementations of the image chooser may allow that too. Document this.
- Images in rich text should allow empty alt text fields
- StreamField: https://github.com/wagtail/rfcs/pull/51

Available heading levels
------------------------

- Disabling heading elements

Bold and italic formatting in rich text
---------------------------------------

- `strong` vs `b`, `em` vs `i` #4665

----

.. _accessibility_in_templates:

Accessibility in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~

Empty heading tags
------------------

- Empty headings

TableBlock issues
-----------------

- #5989
- How to make the "caption" field mandatory if appropriate

Broken links
------------

- Ways to prevent `href="None"` issues when pages are unpublished or deleted

----

.. _authoring_accessible_content:

Authoring accessible content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test

----

Accessibility resources
~~~~~~~~~~~~~~~~~~~~~~~

References

https://a11yproject.com/
https://www.accessibility-developer-guide.com/
https://empathyprompts.net/
https://bbc.github.io/accessibility-news-and-you/
https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/
https://en.wikipedia.org/wiki/Universal_design
https://alphagov.github.io/wcag-primer/
https://thib.me/making-wagtail-accessible
https://github.com/wagtail/rfcs/pull/37
https://www.ibm.com/able/toolkit
https://github.com/brunopulis/awesome-a11y
https://accessibility.digital.gov/
https://accessibility.18f.gov/
https://github.com/scottaohara/accessibility_interview_questions
https://axesslab.com/alt-texts/
https://accessibility.psu.edu/boldfacehtml/


Testing tools

https://github.com/pa11y/pa11y
https://accessibilityinsights.io/

Content guidelines

https://readabilityguidelines.co.uk/
https://plainlanguage.gov/
