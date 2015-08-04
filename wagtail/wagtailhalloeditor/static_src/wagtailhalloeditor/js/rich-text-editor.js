'use strict';

var halloPlugins = {
    halloformat: {},
    halloheadings: {formatBlocks: ['p', 'h2', 'h3', 'h4', 'h5']},
    hallolists: {},
    hallohr: {},
    halloreundo: {},
    hallowagtaillink: {},
    hallorequireparagraphs: {}
};

function registerHalloPlugin(name, opts) {
    halloPlugins[name] = (opts || {});
}

function makeRichTextEditable(id) {
    var input = $('#' + id);
    var richText = $('<div class="richtext"></div>').html(input.val());
    richText.insertBefore(input);
    input.hide();

    var removeStylingPending = false;
    function removeStyling() {
        /* Strip the 'style' attribute from spans that have no other attributes.
        (we don't remove the span entirely as that messes with the cursor position,
        and spans will be removed anyway by our whitelisting)
        */
        $('span[style]', richText).filter(function() {
            return this.attributes.length === 1;
        }).removeAttr('style');
        removeStylingPending = false;
    }

    var closestObj = input.closest('.object');

    richText.hallo({
        toolbar: 'halloToolbarFixed',
        toolbarCssClass: (closestObj.hasClass('full')) ? 'full' : (closestObj.hasClass('stream-field')) ? 'stream-field' : '',
        plugins: halloPlugins
    }).bind('hallomodified', function(event, data) {
        input.val(data.content);
        if (!removeStylingPending) {
            setTimeout(removeStyling, 100);
            removeStylingPending = true;
        }
    }).bind('paste', function(event, data) {
        setTimeout(removeStyling, 1);
    });
}
