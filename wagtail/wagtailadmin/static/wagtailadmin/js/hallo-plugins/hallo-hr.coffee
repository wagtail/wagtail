#     Hallo - a rich text editing jQuery UI widget
#     (c) 2011 Henri Bergius, IKS Consortium
#     Hallo may be freely distributed under the MIT license
((jQuery) ->
  jQuery.widget "IKS.hallohr",
    options:
      editable: null
      toolbar: null
      uuid: ''
      buttonCssClass: null

    populateToolbar: (toolbar) ->
      buttonset = jQuery "<span class=\"#{@widgetName}\"></span>"

      buttonElement = jQuery '<span></span>'
      buttonElement.hallobutton
        uuid: @options.uuid
        editable: @options.editable
        label: "Horizontal rule"
        command: "insertHorizontalRule"
        icon: "icon-horizontalrule"
        cssClass: @options.buttonCssClass
      buttonset.append buttonElement

      buttonset.hallobuttonset()
      toolbar.append buttonset

)(jQuery)
