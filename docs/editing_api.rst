
Wagtail Editing API
===================

Wagtail provides a highly-customizable editing interface consisting of several components:

	*	**Fields** — built-in content types to augment the basic types provided by Django.
	*	**Field Widgets** — editing widgets which streamline data input
	*	**Panels** — containers which hold related field widgets
	*	**Choosers** — interfaces for finding related objects in a ForeignKey relationship

Configuring your models to use these components will shape the Wagtail editor to your needs. Wagtail also provides an API for injecting custom CSS and Javascript for further customization, including extending the hallo.js rich text editor.

There is also an Edit Handler API for creating your own Wagtail editor components.


Fields
~~~~~~

Django's field types are automatically recognized and provided with an appropriate widget for input.


``RichTextField``

	body = RichTextField()

``Image``

	feed_image = models.ForeignKey(
		'wagtailimages.Image',
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='+'
	)

``Document``

	link_document = models.ForeignKey(
		'wagtaildocs.Document',
		null=True,
		blank=True,
		related_name='+'
	)

``Page``

	page = models.ForeignKey(
		'wagtailcore.Page',
		related_name='adverts',
		null=True,
		blank=True
	)

Can also use more specific models.


Snippets

Snippets are not not subclasses, so you must include the model class directly. A chooser is provided which takes the snippet class.

	advert = models.ForeignKey(
		'demo.Advert',
		related_name='+'
	)


Panels
~~~~~~











FieldPanel
~~~~~~~~~~
Takes field_name, classname=None


MultiFieldPanel
~~~~~~~~~~~~~~~
Condenses several ``FieldPanel``s under a single heading and classname.


InlinePanel
~~~~~~~~~~~
Allows for creating/editing a modelcluster of related objects (carousel example).



RichTextFieldPanel
~~~~~~~~~~~~~~~~~~




PageChooserPanel
~~~~~~~~~~~~~~~~

ImageChooserPanel
~~~~~~~~~~~~~~~~~

DocumentChooserPanel
~~~~~~~~~~~~~~~~~~~~

SnippetChooserPanel
~~~~~~~~~~~~~~~~~~~

Edit Handler API
~~~~~~~~~~~~~~~~



