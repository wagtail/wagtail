General coding guidelines
=========================

Language
~~~~~~~~

British English is preferred for user-facing text; this text should also be marked for translation (using the ``django.utils.translation.gettext`` function and ``{% trans %}`` template tag, for example). However, identifiers within code should use American English if the British or international spelling would conflict with built-in language keywords; for example, CSS code should consistently use the spelling ``color`` to avoid inconsistencies like ``background-color: $colour-red``.
