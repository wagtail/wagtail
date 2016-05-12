/* generic function for adding a message to message area through JS alone */
function addMessage(status, text) {
    $('.messages').addClass('new').empty().append('<ul><li class="' + status + '">' + text + '</li></ul>');
    var addMsgTimeout = setTimeout(function() {
        $('.messages').addClass('appear');
        clearTimeout(addMsgTimeout);
    }, 100);
}

function escapeHtml(text) {
    var map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        '\'': '&#039;'
    };

    return text.replace(/[&<>"']/g, function(m) {
        return map[m];
    });
}

function initTagField(id, autocompleteUrl) {
    $('#' + id).tagit({
        autocomplete: {source: autocompleteUrl},
        preprocessTag: function(val) {
            // Double quote a tag if it contains a space
            // and if it isn't already quoted.
            if (val && val[0] != '"' && val.indexOf(' ') > -1) {
                return '"' + val + '"';
            }

            return val;
        }
    });
}

/*
 * Enables a "dirty form check", prompting the user if they are navigating away
 * from a page with unsaved changes.
 *
 * It takes the following parameters:
 *
 *  - formSelector - A CSS selector to select the form to apply this check to.
 *
 *  - options - An object for passing in options. Possible options are:
 *    - ignoredButtonsSelector - A CSS selector to find buttons to ignore within
 *      the form. If the navigation was triggered by one of these buttons, The
 *      check will be ignored. defaults to: input[type="submit"].
 *    - confirmationMessage - The message to display in the prompt.
 *    - alwaysDirty - When set to true the form will always be considered dirty,
 *      prompting the user even when nothing has been changed.
*/

var dirtyFormCheckIsActive = true;

function enableDirtyFormCheck(formSelector, options) {
    var $form = $(formSelector);
    var $ignoredButtons = $form.find(
        options.ignoredButtonsSelector || 'input[type="submit"],button[type="submit"]'
    );
    var confirmationMessage = options.confirmationMessage || ' ';
    var alwaysDirty = options.alwaysDirty || false;
    var initialData = $form.serialize();

    window.addEventListener('beforeunload', function(event) {
        // Ignore if the user clicked on an ignored element
        var triggeredByIgnoredButton = false;
        var $trigger = $(event.explicitOriginalTarget || document.activeElement);

        $ignoredButtons.each(function() {
            if ($(this).is($trigger)) {
                triggeredByIgnoredButton = true;
            }
        });

        if (dirtyFormCheckIsActive && !triggeredByIgnoredButton && (alwaysDirty || $form.serialize() != initialData)) {
            event.returnValue = confirmationMessage;
            return confirmationMessage;
        }
    });
}

function disableDirtyFormCheck() {
    dirtyFormCheckIsActive = false;
}

$(function() {
    // Add class to the body from which transitions may be hung so they don't appear to transition as the page loads
    $('body').addClass('ready');

    // Enable toggle to open/close nav
    $(document).on('click', '#nav-toggle', function() {
        $('body').toggleClass('nav-open');
        if (!$('body').hasClass('nav-open')) {
            $('body').addClass('nav-closed');
        } else {
            $('body').removeClass('nav-closed');
        }
    });

    // Resize nav to fit height of window. This is an unimportant bell/whistle to make it look nice
    var fitNav = function() {
        $('.nav-wrapper').css('min-height', $(window).height());
        $('.nav-main').each(function() {
            var thisHeight = $(this).height();
            var footerHeight = $('.footer', $(this)).height();
        });
    };

    fitNav();

    $(window).resize(function() {
        fitNav();
    });

    // Enable nice focus effects on all fields. This enables help text on hover.
    $(document).on('focus mouseover', 'input,textarea,select', function() {
        $(this).closest('.field').addClass('focused');
        $(this).closest('fieldset').addClass('focused');
        $(this).closest('li').addClass('focused');
    });

    $(document).on('blur mouseout', 'input,textarea,select', function() {
        $(this).closest('.field').removeClass('focused');
        $(this).closest('fieldset').removeClass('focused');
        $(this).closest('li').removeClass('focused');
    });

    /* tabs */
    $(document).on('click', '.tab-nav a', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });

    $(document).on('click', '.tab-toggle', function(e) {
        e.preventDefault();
        $('.tab-nav a[href="' + $(this).attr('href') + '"]').click();
    });

    $('.dropdown').each(function() {
        var $dropdown = $(this);

        $('.dropdown-toggle', $dropdown).on('click', function(e) {
            e.stopPropagation();
            $dropdown.toggleClass('open');

            if ($dropdown.hasClass('open')) {
                // If a dropdown is opened, add an event listener for document clicks to close it
                $(document).on('click.dropdown.cancel', function(e) {
                    var relTarg = e.relatedTarget || e.toElement;

                    // Only close dropdown if the click target wasn't a child of this dropdown
                    if (!$(relTarg).parents().is($dropdown)) {
                        $dropdown.removeClass('open');
                        $(document).off('click.dropdown.cancel');
                    }
                });
            } else {
                $(document).off('click.dropdown.cancel');
            }
        });
    });

    /* Dropzones */
    $('.drop-zone').on('dragover', function() {
        $(this).addClass('hovered');
    }).on('dragleave dragend drop', function() {
        $(this).removeClass('hovered');
    });

    /* Header search behaviour */
    if (window.headerSearch) {
        var searchCurrentIndex = 0;
        var searchNextIndex = 0;

        $(window.headerSearch.termInput).on('input', function() {
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 200);
            $(this).data('timer', wait);
        });

        // auto focus on search box
        $(window.headerSearch.termInput).trigger('focus');

        function search() {
            var workingClasses = 'icon-spinner';

            $(window.headerSearch.termInput).parent().addClass(workingClasses);
            searchNextIndex++;
            var index = searchNextIndex;
            $.ajax({
                url: window.headerSearch.url,
                data: {q: $(window.headerSearch.termInput).val()},
                success: function(data, status) {
                    if (index > searchCurrentIndex) {
                        searchCurrentIndex = index;
                        $(window.headerSearch.targetOutput).html(data).slideDown(800);
                        window.history.pushState(null, 'Search results', '?q=' + $(window.headerSearch.termInput).val());
                    }
                },

                complete: function() {
                    $(window.headerSearch.termInput).parent().removeClass(workingClasses);
                }
            });
        }
    }

    /* Functions that need to run/rerun when active tabs are changed */
    $(document).on('shown.bs.tab', function(e) {
        // Resize autosize textareas
        $('textarea[data-autosize-on]').each(function() {
            autosize.update($(this).get());
        });
    });

    /* Debounce submission of long-running forms and add spinner to give sense of activity */
    $(document).on('click', 'button.button-longrunning', function(e) {
        var $self = $(this);
        var $replacementElem = $('em', $self);
        var reEnableAfter = 30;
        var dataName = 'disabledtimeout'

        // Check the form this submit button belongs to (if any)
        var form = $self.closest('form').get(0);
        if (form && form.checkValidity && (form.checkValidity() == false)) {
                 // ^ Check form.checkValidity returns something as it may not be browser compatible
            return;
        }

        // Disabling a button prevents it submitting the form, so disabling
        // must occur on a brief timeout only after this function returns.

        var timeout = setTimeout(function() {
            if (!$self.data(dataName)) {
                // Button re-enables after a timeout to prevent button becoming
                // permanently un-usable
                $self.data(dataName, setTimeout(function() {
                    clearTimeout($self.data(dataName));

                    $self.prop('disabled', '').removeData(dataName).removeClass('button-longrunning-active')

                    if ($self.data('clicked-text')) {
                        $replacementElem.text($self.data('original-text'));
                    }

                }, reEnableAfter * 1000));

                if ($self.data('clicked-text') && $replacementElem.length) {
                    // Save current button text
                    $self.data('original-text', $replacementElem.text());

                    $replacementElem.text($self.data('clicked-text'));
                }

                // Disabling button must be done last: disabled buttons can't be
                // modified in the normal way, it would seem.
                $self.addClass('button-longrunning-active').prop('disabled', 'true');
            }

            clearTimeout(timeout);
        }, 10);
    });
});
