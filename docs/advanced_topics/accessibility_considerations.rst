Accessibility considerations
============================

Accessibility for CMS-driven websites is a matter of :ref:`modeling content appropriately <content_modeling>`, :ref:`creating accessible templates <accessibility_in_templates>`, and :ref:`authoring content <authoring_accessible_content>` with readability and accessibility guidelines in mind. Wagtail generally puts developers in control of content modeling and front-end markup, but there are a few areas to be aware of nonetheless, and ways to help authors be aware of readability best practices.

* :ref:`Content modeling <content_modeling>`
* :ref:`Accessibility in templates <accessibility_in_templates>`
* :ref:`Authoring accessible content <authoring_accessible_content>`

----

.. _content_modeling:

Content modeling
~~~~~~~~~~~~~~~~

As part of defining your site’s models, here are areas to pay special attention to:

Alt text for images
-------------------

The default behavior for Wagtail images is to use the ``title`` field as the alt text (`#4945 <https://github.com/wagtail/wagtail/issues/4945>`_).
This is inappropriate, as this isn’t communicated in the CMS interface, and the image upload form uses the image’s filename as the title by default.

Ideally, always add an optional “alt text” field wherever an image is used, alongside the image field:

- For normal fields, add an alt text field to your image’s panel.
- For StreamField, add an extra field to your image block.
- For rich text – Wagtail already makes it possible to customize alt text for rich text images. Unfortunately it’s not currently possible to elect not to provide alt text for decorative images (`#ISSUE <https://github.com/wagtail/wagtail/issues/ISSUE>`_).

When defining the alt text fields, make sure they are optional so editors can choose to not write any alt text for decorative images, and take the time to provide ``help_text`` with appropriate guidance.
For example, linking to `established resources on the topic <https://axesslab.com/alt-texts/>`_.

.. note:: Why not have an alt text field on the Image model?

    It’s better than nothing to have a dedicated alt field on the Image model (`#5789 <https://github.com/wagtail/wagtail/pull/5789>`_), and may be appropriate for some websites, but we recommend to have it inline with the content because ideally alt text should be written for the context the image is used in:

    - An image might be decorative in some cases only.
    - If the alt text’s content is already part of the rest of the page, ideally the image should not repeat the same content.
    - Ideally the alt text should be written based on the context the image is displayed in.

See `RFC 51: Contextual alt text <https://github.com/wagtail/rfcs/pull/51>`_ for a long-term solution to this problem.

Embeds title
------------

In some cases (`#5982 <https://github.com/wagtail/wagtail/issues/5982>`_), Wagtail embeds don’t have a ``title`` attribute set.
This is very problematic for screen reader users, who rely on this to understand what the embed is, and whether to interact with it or not.

If your website relies on embeds that have unreliable title extraction, make sure to add a custom (required?) Title field to your embeds so they always have a title.

Available heading levels
------------------------

Wagtail makes it very easy for developers to control which heading levels should be available for any given content, via :ref:`rich text features <rich_text_features>` or custom StreamField blocks.
In both cases, take the time to restrict what heading levels are available so the pages’ document outline is more likely to be logical and sequential.

Bold and italic formatting in rich text
---------------------------------------

By default, Wagtail stores its bold formatting as a ``b`` tag, and italic as ``i`` (`#4665 <https://github.com/wagtail/wagtail/issues/4665>`_). While those tags don’t necessarily always have correct semantics (``strong`` and ``em`` are more ubiquitous), there `isn’t much consequence for screen reader users <https://accessibility.psu.edu/boldfacehtml/>`_, as by default screen readers do not announce content differently based on emphasis.

If this is a concern to you, you can change which tags are used when saving content with :ref:`rich text format converters <rich_text_format_converters>`. In the future, :ref:`rich text rewrite handlers <rich_text_rewrite_handlers>` should also support this being done without altering the storage format (`#4223 <https://github.com/wagtail/wagtail/issues/4223>`_).


TableBlock
----------

The TableBlock’s default implementation makes it too easy for end users not to realise they need either row or column headers (`#5989 <https://github.com/wagtail/wagtail/issues/5989>`_).
Its Caption field should be mandatory for sites where accessibility matters.

----

.. _accessibility_in_templates:

Accessibility in templates
~~~~~~~~~~~~~~~~~~~~~~~~~~

Here are common gotchas to be aware of to make the site’s templates as accessible as possible,

Alt text in templates
---------------------

See the :ref:`content modelling <content_modeling>` section above. Additionally, make sure to :ref:`customise images’ alt text <image_tag_alt>`, either setting it to the relevant field, or to an empty string for decorative images, or images where the alt text would be a repeat of other content.

Empty heading tags
------------------

In both rich text and custom StreamField blocks, it’s very easy for editors to create a heading block but not add any content to it. If this is a problem for your site,

- Add validation rules to those StreamField blocks, making sure the page can’t be saved with the empty fields
- Consider adding similar validation rules for rich text fields, or alternatively hide those rich text blocks.

Hiding empty blocks can be done with CSS:

.. code-block:: css

    h2:empty {
        display: none;
    }

In the future, :ref:`rich text rewrite handlers <rich_text_rewrite_handlers>` should also support this being done server-side (`#4223 <https://github.com/wagtail/wagtail/issues/4223>`_).

Links
-----

- Avoid using "Read more", "Click here", "Find out more" as link text. If needed, make sure to use ``aria-label`` to set a screen-reader-only link text based on the existing one, with additional context.

----

.. _authoring_accessible_content:

Authoring accessible content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

https://thib.me/wagtail-wins

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

https://thib.me/wagtail-wins

Content guidelines

https://readabilityguidelines.co.uk/
https://plainlanguage.gov/
