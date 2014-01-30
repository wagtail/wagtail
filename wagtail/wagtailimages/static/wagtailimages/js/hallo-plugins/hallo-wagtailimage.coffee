# plugin for hallo.js to allow inserting images from the Wagtail image library

(($) ->
    $.widget "IKS.hallowagtailimage",
        options:
            uuid: ''
            editable: null

        populateToolbar: (toolbar) ->
            widget = this

            # Create an element for holding the button
            button = $('<span></span>')
            button.hallobutton
                uuid: @options.uuid
                editable: @options.editable
                label: 'Images'
                icon: 'icon-picture'
                command: null

            # Append the button to toolbar
            toolbar.append button

            button.on "click", (event) ->
                lastSelection = widget.options.editable.getSelection()
                insertionPoint = $(lastSelection.endContainer).parentsUntil('.richtext').last()
                ModalWorkflow
                    url: '/admin/images/chooser/?select_format=true' # TODO: don't hard-code this, as it may be changed in urls.py
                    responses:
                        imageChosen: (imageData) ->
                            elem = $(imageData.html).get(0)

                            lastSelection.insertNode(elem)

                            if elem.getAttribute('contenteditable') == 'false'
                                insertRichTextDeleteControl(elem)
                            widget.options.editable.element.trigger('change')

)(jQuery)
