# plugin for hallo.js to allow inserting links using Wagtail's page chooser

(($) ->
    $.widget "IKS.hallowagtaillink",
        options:
            uuid: ''
            editable: null

        populateToolbar: (toolbar) ->
            widget = this

            getEnclosingLink = () ->
                # if cursor is currently within a link element, return it, otherwise return null
                node = widget.options.editable.getSelection().commonAncestorContainer
                return $(node).parents('a').get(0)

            # Create an element for holding the button
            button = $('<span></span>')
            button.hallobutton
                uuid: @options.uuid
                editable: @options.editable
                label: 'Links'
                icon: 'icon-link'
                command: null
                queryState: (event) ->
                    button.hallobutton('checked', !!getEnclosingLink())

            # Append the button to toolbar
            toolbar.append button

            button.on "click", (event) ->
                enclosingLink = getEnclosingLink()
                if enclosingLink
                    # remove existing link
                    $(enclosingLink).replaceWith(enclosingLink.innerHTML)
                    button.hallobutton('checked', false)
                    widget.options.editable.element.trigger('change')
                else
                    # commence workflow to add a link
                    lastSelection = widget.options.editable.getSelection()

                    if lastSelection.collapsed
                        # TODO: don't hard-code this, as it may be changed in urls.py
                        url = '/admin/choose-page/?allow_external_link=true&allow_email_link=true&prompt_for_link_text=true'
                    else
                        url = '/admin/choose-page/?allow_external_link=true&allow_email_link=true'

                    ModalWorkflow
                        url: url
                        responses:
                            pageChosen: (pageData) ->
                                a = document.createElement('a')
                                a.setAttribute('href', pageData.url)
                                if pageData.id
                                    a.setAttribute('data-id', pageData.id)
                                    a.setAttribute('data-linktype', 'page')

                                if (not lastSelection.collapsed) and lastSelection.canSurroundContents()
                                    # use the selected content as the link text
                                    lastSelection.surroundContents(a)
                                else
                                    # no text is selected, so use the page title as link text
                                    a.appendChild(document.createTextNode pageData.title)
                                    lastSelection.insertNode(a)

                                widget.options.editable.element.trigger('change')

)(jQuery)
