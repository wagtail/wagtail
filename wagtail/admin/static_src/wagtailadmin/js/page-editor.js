'use strict';

var halloPlugins = {};
function registerHalloPlugin(name, opts) {
    /* Obsolete - used on Wagtail <1.12 to register plugins for the hallo.js editor.
    Defined here so that third-party plugins can continue to call it to provide Wagtail <1.12
    compatibility, without throwing an error on later versions. */
}

// Compare two date objects. Ignore minutes and seconds.
function dateEqual(x, y) {
    return x.getDate() === y.getDate() &&
           x.getMonth() === y.getMonth() &&
           x.getYear() === y.getYear()
}

/*
Remove the xdsoft_current css class from markup unless the selected date is currently in view.
Keep the normal behaviour if the home button is clicked.
 */
function hideCurrent(current, input) {
    var selected = new Date(input[0].value);
    if (!dateEqual(selected, current)) {
        $(this).find('.xdsoft_datepicker .xdsoft_current:not(.xdsoft_today)').removeClass('xdsoft_current');
    }
}

function initDateChooser(id, opts) {
    if (window.dateTimePickerTranslations) {
        $('#' + id).datetimepicker($.extend({
            closeOnDateSelect: true,
            timepicker: false,
            scrollInput: false,
            format: 'Y-m-d',
            onGenerate: hideCurrent
        }, opts || {}));
    } else {
        $('#' + id).datetimepicker($.extend({
            timepicker: false,
            scrollInput: false,
            format: 'Y-m-d',
            onGenerate: hideCurrent
        }, opts || {}));
    }
}

function initTimeChooser(id) {
    if (window.dateTimePickerTranslations) {
        $('#' + id).datetimepicker({
            closeOnDateSelect: true,
            datepicker: false,
            scrollInput: false,
            format: 'H:i',
        });
    } else {
        $('#' + id).datetimepicker({
            datepicker: false,
            format: 'H:i'
        });
    }
}

function initDateTimeChooser(id, opts) {
    if (window.dateTimePickerTranslations) {
        $('#' + id).datetimepicker($.extend({
            closeOnDateSelect: true,
            format: 'Y-m-d H:i',
            scrollInput: false,
            onGenerate: hideCurrent
        }, opts || {}));
    } else {
        $('#' + id).datetimepicker($.extend({
            format: 'Y-m-d H:i',
            onGenerate: hideCurrent
        }, opts || {}));
    }
}

function InlinePanel(opts) {
    var self = {};

    self.setHasContent = function() {
        if ($('> li', self.formsUl).not('.deleted').length) {
            self.formsUl.parent().removeClass('empty');
        } else {
            self.formsUl.parent().addClass('empty');
        }
    };

    self.initChildControls = function(prefix) {
        var childId = 'inline_child_' + prefix;
        var deleteInputId = 'id_' + prefix + '-DELETE';

        //mark container as having children to identify fields in use from those not
        self.setHasContent();

        $('#' + deleteInputId + '-button').on('click', function() {
            /* set 'deleted' form field to true */
            $('#' + deleteInputId).val('1');
            $('#' + childId).addClass('deleted').slideUp(function() {
                self.updateMoveButtonDisabledStates();
                self.updateAddButtonState();
                self.setHasContent();
            });
        });

        if (opts.canOrder) {
            $('#' + prefix + '-move-up').on('click', function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the previous visible 'inline_child' li before this one */
                var prevChild = currentChild.prevAll(':not(.deleted)').first();
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

            $('#' + prefix + '-move-down').on('click', function() {
                var currentChild = $('#' + childId);
                var currentChildOrderElem = currentChild.find('input[name$="-ORDER"]');
                var currentChildOrder = currentChildOrderElem.val();

                /* find the next visible 'inline_child' li after this one */
                var nextChild = currentChild.nextAll(':not(.deleted)').first();
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

        /* Hide container on page load if it is marked as deleted. Remove the error
         message so that it doesn't count towards the number of errors on the tab at the
         top of the page. */
        if ($('#' + deleteInputId).val() === '1') {
            $('#' + childId).addClass('deleted').hide(0, function() {
                self.updateMoveButtonDisabledStates();
                self.updateAddButtonState();
                self.setHasContent();
            });

            $('#' + childId).find('.error-message').remove();
        }
    };

    self.formsUl = $('#' + opts.formsetPrefix + '-FORMS');

    self.updateMoveButtonDisabledStates = function() {
        if (opts.canOrder) {
            var forms = self.formsUl.children('li:not(.deleted)');
            forms.each(function(i) {
                $('ul.controls .inline-child-move-up', this).toggleClass('disabled', i === 0).toggleClass('enabled', i !== 0);
                $('ul.controls .inline-child-move-down', this).toggleClass('disabled', i === forms.length - 1).toggleClass('enabled', i != forms.length - 1);
            });
        }
    };

    self.updateAddButtonState = function() {
        if (opts.maxForms) {
            var forms = $('> li', self.formsUl).not('.deleted');
            var addButton = $('#' + opts.formsetPrefix + '-ADD');

            if (forms.length >= opts.maxForms) {
                addButton.addClass('disabled');
            } else {
                addButton.removeClass('disabled');
            }
        }
    };

    self.animateSwap = function(item1, item2) {
        var parent = self.formsUl;
        var children = parent.children('li:not(.deleted)');

        // Apply moving class to container (ul.multiple) so it can assist absolute positioning of it's children
        // Also set it's relatively calculated height to be an absolute one, to prevent the container collapsing while its children go absolute
        parent.addClass('moving').css('height', parent.height());

        children.each(function() {
            // console.log($(this));
            $(this).css('top', $(this).position().top);
        }).addClass('moving');

        // animate swapping around
        item1.animate({
            top:item2.position().top
        }, 200, function() {
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        });

        item2.animate({
            top:item1.position().top
        }, 200, function() {
            parent.removeClass('moving').removeAttr('style');
            children.removeClass('moving').removeAttr('style');
        });
    };

    buildExpandingFormset(opts.formsetPrefix, {
        onAdd: function(formCount) {
            var newChildPrefix = opts.emptyChildFormPrefix.replace(/__prefix__/g, formCount);
            self.initChildControls(newChildPrefix);
            if (opts.canOrder) {
                /* NB form hidden inputs use 0-based index and only increment formCount *after* this function is run.
                Therefore formcount and order are currently equal and order must be incremented
                to ensure it's *greater* than previous item */
                $('#id_' + newChildPrefix + '-ORDER').val(formCount + 1);
            }

            self.updateMoveButtonDisabledStates();
            self.updateAddButtonState();

            if (opts.onAdd) opts.onAdd();
        }
    });

    return self;
}

function cleanForSlug(val, useURLify) {
    if (useURLify) {
        // URLify performs extra processing on the string (e.g. removing stopwords) and is more suitable
        // for creating a slug from the title, rather than sanitising a slug entered manually
        let cleaned = URLify(val, 255, unicodeSlugsEnabled);

        // if the result is blank (e.g. because the title consisted entirely of stopwords),
        // fall through to the non-URLify method
        if (cleaned) {
            return cleaned;
        }
    }

    // just do the "replace"
    if (unicodeSlugsEnabled) {
        return val.replace(/\s/g, '-').replace(/[&\/\\#,+()$~%.'":`@\^!*?<>{}]/g, '').toLowerCase();
    } else {
        return val.replace(/\s/g, '-').replace(/[^A-Za-z0-9\-\_]/g, '').toLowerCase();
    }
}

function initSlugAutoPopulate() {
    var slugFollowsTitle = false;

    $('#id_title').on('focus', function() {
        /* slug should only follow the title field if its value matched the title's value at the time of focus */
        var currentSlug = $('#id_slug').val();
        var slugifiedTitle = cleanForSlug(this.value, true);
        slugFollowsTitle = (currentSlug == slugifiedTitle);
    });

    $('#id_title').on('keyup keydown keypress blur', function() {
        if (slugFollowsTitle) {
            var slugifiedTitle = cleanForSlug(this.value, true);
            $('#id_slug').val(slugifiedTitle);
        }
    });
}

function initSlugCleaning() {
    $('#id_slug').on('blur', function() {
        // if a user has just set the slug themselves, don't remove stop words etc, just illegal characters
        $(this).val(cleanForSlug($(this).val(), false));
    });
}

function initErrorDetection() {
    var errorSections = {};

    // first count up all the errors
    $('.error-message').each(function() {
        var parentSection = $(this).closest('section');

        if (!errorSections[parentSection.attr('id')]) {
            errorSections[parentSection.attr('id')] = 0;
        }

        errorSections[parentSection.attr('id')] = errorSections[parentSection.attr('id')] + 1;
    });

    // now identify them on each tab
    for (var index in errorSections) {
        $('.tab-nav a[href="#' + index + '"]').addClass('errors').attr('data-count', errorSections[index]);
    }
}

function initCollapsibleBlocks() {
    $('.object.multi-field.collapsible').each(function() {
        var $li = $(this);
        var $fieldset = $li.find('fieldset');
        if ($li.hasClass('collapsed') && $li.find('.error-message').length == 0) {
            $fieldset.hide();
        }

        $li.find('> h2').on('click', function() {
            if (!$li.hasClass('collapsed')) {
                $li.addClass('collapsed');
                $fieldset.hide('slow');
            } else {
                $li.removeClass('collapsed');
                $fieldset.show('show');
            }
        });
    });
}

function initKeyboardShortcuts() {
    Mousetrap.bind(['mod+p'], function(e) {
        $('.action-preview').trigger('click');
        return false;
    });

    Mousetrap.bind(['mod+s'], function(e) {
        $('.action-save').trigger('click');
        return false;
    });
}

$(function() {
    /* Only non-live pages should auto-populate the slug from the title */
    if (!$('body').hasClass('page-is-live')) {
        initSlugAutoPopulate();
    }

    initSlugCleaning();
    initErrorDetection();
    initCollapsibleBlocks();
    initKeyboardShortcuts();

    //
    // Preview
    //
    // In order to make the preview truly reliable, the preview page needs
    // to be perfectly independent from the edit page,
    // from the browser perspective. To pass data from the edit page
    // to the preview page, we send the form after each change
    // and save it inside the user session.

    var $previewButton = $('.action-preview'), $form = $('#page-edit-form');
    var previewUrl = $previewButton.data('action');
    var autoUpdatePreviewDataTimeout = -1;

    function setPreviewData() {
        return $.ajax({
            url: previewUrl,
            method: 'POST',
            data: new FormData($form[0]),
            processData: false,
            contentType: false
        });
    }

    $previewButton.one('click', function () {
        if ($previewButton.data('auto-update')) {
            // Form data is changed when field values are changed
            // (change event), when HTML elements are added, modified, moved,
            // and deleted (DOMSubtreeModified event), and we need to delay
            // setPreviewData when typing to avoid useless extra AJAX requests
            // (so we postpone setPreviewData when keyup occurs).
            // TODO: Replace DOMSubtreeModified with a MutationObserver.
            $form.on('change keyup DOMSubtreeModified', function () {
                clearTimeout(autoUpdatePreviewDataTimeout);
                autoUpdatePreviewDataTimeout = setTimeout(setPreviewData, 1000);
            }).trigger('change');
        }
    });

    $previewButton.on('click', function(e) {
        e.preventDefault();
        var $this = $(this);
        var $icon = $this.filter('.icon'),
            thisPreviewUrl = $this.data('action');
        $icon.addClass('icon-spinner').removeClass('icon-view');
        var previewWindow = window.open('', thisPreviewUrl);
        previewWindow.focus();

        setPreviewData().done(function (data) {
            if (data['is_valid']) {
                previewWindow.document.location = thisPreviewUrl;
            } else {
                window.focus();
                previewWindow.close();
                // TODO: Stop sending the form, as it removes file data.
                $form.trigger('submit');
            }
        }).fail(function () {
            alert('Error while sending preview data.');
            window.focus();
            previewWindow.close();
        }).always(function () {
            $icon.addClass('icon-view').removeClass('icon-spinner');
        });
    });
});

if (typeof module !== 'undefined' && module.exports) {
  module.exports.cleanForSlug = cleanForSlug;
}
