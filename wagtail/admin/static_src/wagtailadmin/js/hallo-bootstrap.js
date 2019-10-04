'use strict';

function makeHalloRichTextEditable(id, plugins) {
    var input = $('#' + id);
    var editor = $('<div class="halloeditor" data-hallo-editor></div>').html(input.val());
    editor.insertBefore(input);
    input.hide();

    var removeStylingPending = false;
    function removeStyling() {
        /* Strip the 'style' attribute from spans that have no other attributes.
        (we don't remove the span entirely as that messes with the cursor position,
        and spans will be removed anyway by our whitelisting)
        */
        $('span[style]', editor).filter(function() {
            return this.attributes.length === 1;
        }).removeAttr('style');
        removeStylingPending = false;
    }

    /* Workaround for faulty change-detection in hallo */
    function setModified() {
        var hallo = editor.data('IKS-hallo');
        if (hallo) {
            hallo.setModified();
        }
    }

    var closestObj = input.closest('.object');

    editor.hallo({
        toolbar: 'halloToolbarFixed',
        toolbarCssClass: (closestObj.hasClass('full')) ? 'full' : '',
        /* use the passed-in plugins arg */
        plugins: plugins
    }).on('hallomodified', function(event, data) {
        input.val(data.content);
        if (!removeStylingPending) {
            setTimeout(removeStyling, 100);
            removeStylingPending = true;
        }
    }).on('paste drop', function(event, data) {
        setTimeout(function() {
            removeStyling();
            setModified();
        }, 1);
    /* Animate the fields open when you click into them. */
    }).on('halloactivated', function(event, data) {
        $(event.target).addClass('expanded', 200, function(e) {
            /* Hallo's toolbar will reposition itself on the scroll event.
            This is useful since animating the fields can cause it to be
            positioned badly initially. */
            $(window).trigger('scroll');
        });
    }).on('hallodeactivated', function(event, data) {
        $(event.target).removeClass('expanded', 200, function(e) {
            $(window).trigger('scroll');
        });
    });

    setupLinkTooltips(editor);
}

function setupLinkTooltips(elem) {
    elem.tooltip({
        animation: false,
        title: function() {
            return $(this).attr('href');
        },
        trigger: 'hover',
        placement: 'bottom',
        selector: 'a'
    });
}

function insertRichTextDeleteControl(elem) {
    var a = $('<a class="icon icon-cross text-replace halloembed__delete">Delete</a>');
    $(elem).addClass('halloembed').prepend(a);
    a.on('click', function() {
        var widget = $(elem).parent('[data-hallo-editor]').data('IKS-hallo');
        $(elem).fadeOut(function() {
            $(elem).remove();
            if (widget != undefined && widget.options.editable) {
                widget.element.trigger('change');
            }
        });
    });
}

$(function() {
    $('[data-hallo-editor] [contenteditable="false"]').each(function() {
        insertRichTextDeleteControl(this);
    });
})
