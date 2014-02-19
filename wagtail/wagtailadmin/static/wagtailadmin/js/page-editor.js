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

    richText.hallo({
        toolbar: 'halloToolbarFixed',
        toolbarcssClass: 'testy',
        plugins: {
            'halloformat': {},
            'halloheadings': {formatBlocks: ["p", "h2", "h3", "h4", "h5"]},
            'hallolists': {}, 
            'hallohr': {},
            'halloreundo': {},
            'hallowagtailimage': {},
            'hallowagtailembeds': {},
            'hallowagtaillink': {},
            'hallowagtaildoclink': {},
        }
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

function insertRichTextDeleteControl(elem) {
    var a = $('<a class="icon icon-cross text-replace delete-control">Delete</a>');
    $(elem).addClass('rich-text-deletable').prepend(a);
    a.click(function() {
        $(elem).fadeOut(function() {
            $(elem).remove();
        });
    });
}

function initDateChoosers(context) {
    $('input.friendly_date', context).datepicker({
        dateFormat: 'd M yy', constrainInput: false, /* showOn: 'button', */ firstDay: 1
    });
    
    if(window.overrideDateInputFormat && window.overrideDateInputFormat !='') {
        $('input.localized_date', context).datepicker({
            dateFormat: window.overrideDateInputFormat, constrainInput: false, /* showOn: 'button', */ firstDay: 1
        });
    } else {
        $('input.localized_date', context).datepicker({
            constrainInput: false, /* showOn: 'button', */ firstDay: 1
        });
    }
    
}
function initFriendlyDateChooser(id) {
    $('#' + id).datepicker({
        dateFormat: 'd M yy', constrainInput: false, /* showOn: 'button', */ firstDay: 1
    });
}
function initLocalizedDateChooser(id) {
    if(window.overrideDateInputFormat && window.overrideDateInputFormat !='') {
        $('#' + id).datepicker({
            dateFormat: window.overrideDateInputFormat, constrainInput: false, /* showOn: 'button', */ firstDay: 1
        });
    } else {
        $('#' + id).datepicker({
            constrainInput: false, /* showOn: 'button', */ firstDay: 1
        });
    }
    
}

function initTimeChoosers(context) {
    $('input.friendly_time', context).timepicker({
        timeFormat: 'g.ia'
    });
    $('input.localized_time', context).timepicker({
        timeFormat: 'H:i', maxTime: '23:59'
    });
}
function initFriendlyTimeChooser(id) {
    $('#' + id).timepicker({
        timeFormat: 'g.ia'
    });
}
function initLocalizedTimeChooser(id) {
    $('#' + id).timepicker({
        timeFormat: 'H:i', maxTime: '23:59'
    });
}

function initTagField(id, autocompleteUrl) {
    $('#' + id).tagit({
        autocomplete: {source: autocompleteUrl}
    });
}

function InlinePanel(opts) {
    var self = {};

    self.setHasContent = function(){
        if($('li:visible', self.formsUl).length){
            self.formsUl.parent().removeClass('empty');
        }else{
            self.formsUl.parent().addClass('empty');
        }
    };

    self.initChildControls = function (prefix) {
        var childId = 'inline_child_' + prefix;
        var deleteInputId = 'id_' + prefix + '-DELETE';

        //mark container as having children to identify fields in use from those not
        self.setHasContent();

        $('#' + deleteInputId + '-button').click(function() {
            /* set 'deleted' form field to true */
            $('#' + deleteInputId).val('1');
            $('#' + childId).slideUp(function() {
                self.updateMoveButtonDisabledStates();
                self.setHasContent();
            });            
        });
        if (opts.canOrder) {
            $('#' + prefix + '-move-up').click(function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the previous visible 'inline_child' li before this one */
                var prevChild = currentChild.prev(':visible');
                if (!prevChild.length) return;
                var prevChildOrderElem = prevChild.find('input[name$="-ORDER"]');
                var prevChildOrder = prevChildOrderElem.val();

                // async swap animation must run before the insertBefore line below, but doesn't need to finish first
                self.animateSwap(currentChild, prevChild);

                currentChild.insertBefore(prevChild);
                currentChildOrderElem.val(prevChildOrder);
                prevChildOrderElem.val(currentChildOrder);

                self.updateMoveButtonDisabledStates();
            });

            $('#' + prefix + '-move-down').click(function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the next visible 'inline_child' li after this one */
                var nextChild = currentChild.next(':visible');
                if (!nextChild.length) return;
                var nextChildOrderElem = nextChild.find('input[name$="-ORDER"]');
                var nextChildOrder = nextChildOrderElem.val();

                // async swap animation must run before the insertAfter line below, but doesn't need to finish first
                self.animateSwap(currentChild, nextChild);

                currentChild.insertAfter(nextChild);
                currentChildOrderElem.val(nextChildOrder);
                nextChildOrderElem.val(currentChildOrder);

                self.updateMoveButtonDisabledStates();
            });
        }
    };

    self.formsUl = $('#' + opts.formsetPrefix + '-FORMS');

    self.updateMoveButtonDisabledStates = function() {
        if (opts.canOrder) {
            forms = self.formsUl.children('li:visible');
            forms.each(function(i) {
                $('ul.controls .inline-child-move-up', this).toggleClass('disabled', i === 0).toggleClass('enabled', i !== 0);
                $('ul.controls .inline-child-move-down', this).toggleClass('disabled', i === forms.length - 1).toggleClass('enabled', i != forms.length - 1);
            });
        }
    };

    self.animateSwap = function(item1, item2){
        var parent = self.formsUl;
        var children = parent.children('li:visible');

        // Apply moving class to container (ul.multiple) so it can assist absolute positioning of it's children
        // Also set it's relatively calculated height to be an absolute one, to prevent the container collapsing while its children go absolute
        parent.addClass('moving').css('height', parent.height());

        children.each(function(){
            // console.log($(this));
            $(this).css('top', $(this).position().top);
        }).addClass('moving');

        // animate swapping around
        item1.animate({
            top:item2.position().top
        }, 200, function(){
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        });
        item2.animate({
            top:item1.position().top
        }, 200, function(){
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        });
    };

    buildExpandingFormset(opts.formsetPrefix, {
        onAdd: function(formCount) {
            function fixPrefix(str) {
                return str.replace(/__prefix__/g, formCount);
            }
            self.initChildControls(fixPrefix(opts.emptyChildFormPrefix));
            if (opts.canOrder) {
                $(fixPrefix('#id_' + opts.emptyChildFormPrefix + '-ORDER')).val(formCount);
            }
            self.updateMoveButtonDisabledStates();
            
            opts.onAdd(fixPrefix);
        }
    });

    return self;
}

function cleanForSlug(val){
    if(URLify != undefined) { // Check to be sure that URLify function exists
        return URLify(val, val.length);
    } else { // If not just do the "replace"
        return val.replace(/\s/g,"-").replace(/[^A-Za-z0-9\-]/g,"").toLowerCase();
    }
}

function initSlugAutoPopulate(){
    $('#id_title').on('focus', function(){
        $('#id_slug').data('previous-val', $('#id_slug').val());
        $(this).data('previous-val', $(this).val());
    });
    $('#id_title').on('keyup keydown keypress blur', function(){
        if($('body').hasClass('create') || (!$('#id_slug').data('previous-val').length || cleanForSlug($('#id_title').data('previous-val')) === $('#id_slug').data('previous-val'))){
            // only update slug if the page is being created from scratch, if slug is completely blank, or if title and slug prior to typing were identical
            $('#id_slug').val(cleanForSlug($('#id_title').val()));
        }
    });
}

function initSlugCleaning(){
    $('#id_slug').on('keyup blur', function(){
        $(this).val(cleanForSlug($(this).val()));
    });
}

function initErrorDetection(){
    var errorSections = {};

    // first count up all the errors
    $('.error-message').each(function(){
        var parentSection = $(this).closest('section');

        if(!errorSections[parentSection.attr('id')]){
            errorSections[parentSection.attr('id')] = 0;
        }

        errorSections[parentSection.attr('id')] = errorSections[parentSection.attr('id')]+1;
    });

    // now identify them on each tab
    for(var index in errorSections) {
        $('.tab-nav a[href=#'+ index +']').addClass('errors').attr('data-count', errorSections[index]);
    }    
}

$(function() {
    initDateChoosers();
    initTimeChoosers();
    initSlugAutoPopulate();
    initSlugCleaning();
    initErrorDetection();

    $('.richtext [contenteditable="false"]').each(function() {
        insertRichTextDeleteControl(this);
    });

    /* Set up behaviour of preview button */
    $('#action-preview').click(function() {
        var previewWindow = window.open($(this).data('placeholder'), $(this).data('windowname'));

        $.ajax({
            type: "POST",
            url: $(this).data('action'),
            data: $('#page-edit-form').serialize(),
            success: function(data, textStatus, request) {
                if (request.getResponseHeader('X-Wagtail-Preview') == 'ok') {
                    previewWindow.document.open();
                    previewWindow.document.write(data);
                    previewWindow.document.close();
                } else {
                    previewWindow.close();
                    document.open();
                    document.write(data);
                    document.close();
                }
            },
            error: function(xhr, textStatus, errorThrown) {
                /* If an error occurs, display it in the preview window so that
                we aren't just showing the spinner forever. We preserve the original
                error output rather than giving a 'friendly' error message so that
                developers can debug template errors. (On a production site, we'd
                typically be serving a friendly custom 500 page anyhow.) */
                previewWindow.document.open();
                previewWindow.document.write(xhr.responseText);
                previewWindow.document.close();
            }
        });
    });
});
