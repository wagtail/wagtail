from __future__ import absolute_import, unicode_literals

from wagtail.wagtailimages.views.serve import ServeView


generate_signature = ServeView().generate_signature
verify_signature = ServeView().verify_signature
