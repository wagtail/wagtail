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

function initTagField(id, autocompleteUrl, allowSpaces, tagLimit) {
    $('#' + id).tagit({
        autocomplete: {source: autocompleteUrl},
        preprocessTag: function(val) {
            // Double quote a tag if it contains a space
            // and if it isn't already quoted.
            if (val && val[0] != '"' && val.indexOf(' ') > -1) {
                return '"' + val + '"';
            }

            return val;
        },

        allowSpaces: allowSpaces,
        tagLimit: tagLimit,
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
 *    - confirmationMessage - The message to display in the prompt.
 *    - alwaysDirty - When set to true the form will always be considered dirty,
 *      prompting the user even when nothing has been changed.
*/

function enableDirtyFormCheck(formSelector, options) {
    var $form = $(formSelector);
    var confirmationMessage = options.confirmationMessage || ' ';
    var alwaysDirty = options.alwaysDirty || false;
    var initialData = null;
    var formSubmitted = false;

    $form.on('submit', function() {
        formSubmitted = true;
    });

    // Delay snapshotting the form’s data to avoid race conditions with form widgets that might process the values.
    // User interaction with the form within that delay also won’t trigger the confirmation message.
    setTimeout(function() {
        initialData = $form.serialize();
    }, 1000 * 10);

    window.addEventListener('beforeunload', function(event) {
        var isDirty = initialData && $form.serialize() != initialData;
        var displayConfirmation = (
            !formSubmitted && (alwaysDirty || isDirty)
        );

        if (displayConfirmation) {
            event.returnValue = confirmationMessage;
            return confirmationMessage;
        }
    });
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

    // Enable toggle to open/close user settings
    $(document).on('click', '#account-settings', function() {
        $('.nav-main').toggleClass('nav-main--open-footer');
        $(this).find('em').toggleClass('icon-arrow-down-after icon-arrow-up-after');
    });

    // Resize nav to fit height of window. This is an unimportant bell/whistle to make it look nice
    var fitNav = function() {
        $('.nav-wrapper').css('min-height', $(window).height());
        $('.nav-main').each(function() {
            var thisHeight = $(this).height();
            var footerHeight = $('#footer', $(this)).height();
        });
    };

    fitNav();

    $(window).on('resize', function() {
        fitNav();
    });

    // Logo interactivity
    function initLogo() {
        var sensitivity = 8; // the amount of times the user must stroke the wagtail to trigger the animation

        var $logoContainer = $('.wagtail-logo-container__desktop');
        var mouseX = 0;
        var lastMouseX = 0;
        var dir = '';
        var lastDir = '';
        var dirChangeCount = 0;

        function enableWag() {
            $logoContainer.removeClass('logo-serious').addClass('logo-playful');
        }

        function disableWag() {
            $logoContainer.removeClass('logo-playful').addClass('logo-serious');
        }

        $logoContainer.on('mousemove', function(event) {
            mouseX = event.pageX;

            if (mouseX > lastMouseX) {
                dir = 'r';
            } else if (mouseX < lastMouseX) {
                dir = 'l';
            }

            if (dir != lastDir && lastDir != '') {
                dirChangeCount += 1;
            }

            if (dirChangeCount > sensitivity) {
                enableWag();
            }

            lastMouseX = mouseX;
            lastDir = dir;
        });

        $logoContainer.on('mouseleave', function() {
            dirChangeCount = 0;
            disableWag();
        });

        disableWag();
    }
    initLogo();

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
    if (window.location.hash) {
      $('a[href="' + window.location.hash + '"]').tab('show');
    }

    $(document).on('click', '.tab-nav a', function(e) {
      e.preventDefault();
      $(this).tab('show');
      window.history.replaceState(null, null, $(this).attr('href'));
    });

    $(document).on('click', '.tab-toggle', function(e) {
        e.preventDefault();
        $('.tab-nav a[href="' + $(this).attr('href') + '"]').trigger('click');
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
        var $input = $(window.headerSearch.termInput);
        var $inputContainer = $input.parent();

        $input.on('keyup cut paste change', function() {
            clearTimeout($input.data('timer'));
            $input.data('timer', setTimeout(search, 200));
        });

        // auto focus on search box
        $input.trigger('focus');

        function search() {
            var workingClasses = 'icon-spinner';

            var newQuery = $input.val();
            var currentQuery = getURLParam('q');
            // only do the query if it has changed for trimmed queries
            // eg. " " === "" and "firstword " ==== "firstword"
            if (currentQuery.trim() !== newQuery.trim()) {
                $inputContainer.addClass(workingClasses);
                searchNextIndex++;
                var index = searchNextIndex;
                $.ajax({
                    url: window.headerSearch.url,
                    data: {q: newQuery},
                    success: function(data, status) {
                        if (index > searchCurrentIndex) {
                            searchCurrentIndex = index;
                            $(window.headerSearch.targetOutput).html(data).slideDown(800);
                            window.history.replaceState(null, null, '?q=' + newQuery);
                        }
                    },
                    complete: function() {
                        wagtail.ui.initDropDowns();
                        $inputContainer.removeClass(workingClasses);
                    }
                });
            }
        }

        function getURLParam(name) {
            var results = new RegExp('[\?&]' + name + '=([^]*)').exec(window.location.search);
            if (results) {
                return results[1];
            }
            return '';
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
        var dataName = 'disabledtimeout';

        window.cancelSpinner = function() {
            $self.prop('disabled', '').removeData(dataName).removeClass('button-longrunning-active');

            if ($self.data('clicked-text')) {
                $replacementElem.text($self.data('original-text'));
            }
        };

        // If client-side validation is active on this form, and is going to block submission of the
        // form, don't activate the spinner
        var form = $self.closest('form').get(0);
        if (form && form.checkValidity && !form.noValidate && (!form.checkValidity())) {
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

                    cancelSpinner();

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


// =============================================================================
// Wagtail global module, mainly useful for debugging.
// =============================================================================

var wagtail = window.wagtail = null;

// =============================================================================
// Inline dropdown module
// =============================================================================

wagtail = (function(document, window, wagtail) {

    // Module pattern
    if (!wagtail) {
        wagtail = {
            ui: {}
        };
    }

    // Constants
    var DROPDOWN_SELECTOR = '[data-dropdown]';
    var LISTING_TITLE_SELECTOR = '[data-listing-page-title]';
    var LISTING_ACTIVE_CLASS = 'listing__item--active';
    var ICON_DOWN = 'icon-arrow-down';
    var ICON_UP = 'icon-arrow-up';
    var IS_OPEN = 'is-open';
    var clickEvent = 'click';
    var TOGGLE_SELECTOR = '[data-dropdown-toggle]';
    var ARIA = 'aria-hidden';
    var keys = {
        ESC: 27,
        ENTER: 13,
        SPACE: 32
    };


    /**
     * Singleton controller and registry for DropDown components.
     *
     * Mostly used to maintain open/closed state of components and easily
     * toggle them when the focus changes.
     */
    var DropDownController = {
        _dropDowns: [],

        closeAllExcept: function(dropDown) {
            var index = this._dropDowns.indexOf(dropDown);

            this._dropDowns.forEach(function(item, i) {
                 if (i !== index && item.state.isOpen) {
                    item.closeDropDown();
                }
            });
        },

        add: function(dropDown) {
            this._dropDowns.push(dropDown);
        },

        get: function() {
            return this._dropDowns;
        },

        getByIndex: function(index) {
            return this._dropDowns[index];
        },

        getOpenDropDown: function() {
            var needle = null;

            this._dropDowns.forEach(function(item) {
                if (item.state.isOpen) {
                    needle = item;
                }
            });

            return needle;
        }
    };


    /**
     * DropDown component
     *
     * Template: _button_with_dropdown.html
     *
     * Can contain a list of links
     * Controllable via a toggle class or the keyboard.
     */
    function DropDown(el, registry) {
        if (!el || !registry ) {
            if ('error' in console) {
                console.error('A dropdown was created without an element or the DropDownController.\nMake sure to pass both to your component.');
                return;
            }
        }

        this.el = el;
        this.$parent = $(el).parents(LISTING_TITLE_SELECTOR);

        this.state = {
            isOpen: false
        };

        this.registry = registry;

        this.clickOutsideDropDown = this._clickOutsideDropDown.bind(this);
        this.closeDropDown = this._closeDropDown.bind(this);
        this.openDropDown = this._openDropDown.bind(this);
        this.handleClick = this._handleClick.bind(this);
        this.handleKeyEvent = this._handleKeyEvent.bind(this);

        el.addEventListener(clickEvent, this.handleClick);
        el.addEventListener('keydown', this.handleKeyEvent);
        this.$parent.data('close', this.closeDropDown);
    }

    DropDown.prototype = {

        _handleKeyEvent: function(e) {
            var validTriggers = [keys.SPACE, keys.ENTER];

            if (validTriggers.indexOf(e.which) > -1) {
                e.preventDefault();
                this.handleClick(e);
            }
        },

        _handleClick: function(e) {
            var el = this.el;

            if (!this.state.isOpen) {
                this.openDropDown(e);
            } else {
                this.closeDropDown(e);
            }
        },

        _openDropDown: function(e) {
            e.stopPropagation();
            e.preventDefault();
            var el = this.el;
            var $parent = this.$parent;
            var toggle = el.querySelector(TOGGLE_SELECTOR);

            this.state.isOpen = true;
            this.registry.closeAllExcept(this);

            el.classList.add(IS_OPEN);
            el.setAttribute(ARIA, false);
            toggle.classList.remove(ICON_DOWN);
            toggle.classList.add(ICON_UP);
            document.addEventListener(clickEvent, this.clickOutsideDropDown, false);
            $parent.addClass(LISTING_ACTIVE_CLASS);
        },

        _closeDropDown: function(e) {
            this.state.isOpen = false;

            var el = this.el;
            var $parent = this.$parent;
            var toggle = el.querySelector(TOGGLE_SELECTOR);
            document.removeEventListener(clickEvent, this.clickOutsideDropDown, false);
            el.classList.remove(IS_OPEN);
            toggle.classList.add(ICON_DOWN);
            toggle.classList.remove(ICON_UP);
            el.setAttribute(ARIA, true);
            $parent.removeClass(LISTING_ACTIVE_CLASS);
        },

        _clickOutsideDropDown: function(e) {
            var el = this.el;
            var relTarget = e.relatedTarget || e.toElement;

            if (!$(relTarget).parents().is(el)) {
                this.closeDropDown();
            }
        }
    };

    function initDropDown() {
        var dropDown = new DropDown(this, DropDownController)
        DropDownController.add(dropDown);
    }

    function handleKeyPress(e) {
        if (e.which === keys.ESC) {
            var open = DropDownController.getOpenDropDown();
            if (open) {
                open.closeDropDown();
            }
        }
    }

    function initDropDowns() {
        $(DROPDOWN_SELECTOR).each(initDropDown);
        $(document).on("keydown", handleKeyPress);
    }

    $(document).ready(initDropDowns);
    wagtail.ui.initDropDowns = initDropDowns;
    wagtail.ui.DropDownController = DropDownController;
    return wagtail;

})(document, window, wagtail);
