# plugin for hallo.js to allow inserting links using Wagtail's page chooser

(($) ->
    $.widget "IKS.hallowagtaildoclink",
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
                label: 'Documents'
                icon: 'icon-file-text-alt'
                command: null

            # Append the button to toolbar
            toolbar.append button

            button.on "click", (event) ->
                lastSelection = widget.options.editable.getSelection()
                ModalWorkflow
                    url: window.chooserUrls.documentChooser
                    responses:
                        documentChosen: (docData) ->
                            a = document.createElement('a')
                            a.setAttribute('href', docData.url)
                            a.setAttribute('data-id', docData.id)
                            a.setAttribute('data-linktype', 'document')

                            if (not lastSelection.collapsed) and lastSelection.canSurroundContents()
                                # use the selected content as the link text
                                lastSelection.surroundContents(a)
                            else
                                # no text is selected, so use the doc title as link text
                                a.appendChild(document.createTextNode docData.title)
                                lastSelection.insertNode(a)

                            widget.options.editable.element.trigger('change')

)(jQuery)
