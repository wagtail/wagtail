(function ($) {
// Ok, let's do eeet

    ACTIVE_NODE_BG_COLOR = '#B7D7E8';
    RECENTLY_MOVED_COLOR = '#FFFF00';
    RECENTLY_MOVED_FADEOUT = '#FFFFFF';
    ABORT_COLOR = '#EECCCC';
    DRAG_LINE_COLOR = '#AA00AA';

    RECENTLY_FADE_DURATION = 2000;

// This is the basic Node class, which handles UI tree operations for each 'row'
    var Node = function (elem) {
        var $elem = $(elem);
        var node_id = $elem.attr('node');
        var parent_id = $elem.attr('parent');
        var level = parseInt($elem.attr('level'));
        var children_num = parseInt($elem.attr('children-num'));
        return {
            elem: elem,
            $elem: $elem,
            node_id: node_id,
            parent_id: parent_id,
            level: level,
            has_children: function () {
                return children_num > 0;
            },
            node_name: function () {
                // Returns the text of the node
                return $elem.find('th a:not(.collapse)').text();
            },
            is_collapsed: function () {
                return $elem.find('a.collapse').hasClass('collapsed');
            },
            children: function () {
                return $('tr[parent=' + node_id + ']');
            },
            collapse: function () {
                // For each children, hide it's childrens and so on...
                $.each(this.children(),function () {
                    var node = new Node(this);
                    node.collapse();
                }).hide();
                // Swicth class to set the proprt expand/collapse icon
                $elem.find('a.collapse').removeClass('expanded').addClass('collapsed');
            },
            parent_node: function () {
                // Returns a Node object of the parent
                return new Node($('tr[node=' + parent_id + ']', $elem.parent())[0]);
            },
            expand: function () {
                // Display each kid (will display in collapsed state)
                this.children().show();
                // Swicth class to set the proprt expand/collapse icon
                $elem.find('a.collapse').removeClass('collapsed').addClass('expanded');

            },
            toggle: function () {
                if (this.is_collapsed()) {
                    this.expand();
                } else {
                    this.collapse();
                }
            },
            clone: function () {
                return $elem.clone();
            }
        }
    };

    $(document).ready(function () {

        // begin csrf token code
        // Taken from http://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax
        $(document).ajaxSend(function (event, xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        });
        // end csrf token code


        // Don't activate drag or collapse if GET filters are set on the page
        if ($('#has-filters').val() === "1") {
            return;
        }

        $body = $('body');

        // Activate all rows for drag & drop
        // then bind mouse down event
        $('td.drag-handler span').addClass('active').bind('mousedown', function (evt) {
            $ghost = $('<div id="ghost"></div>');
            $drag_line = $('<div id="drag_line"><span></span></div>');
            $ghost.appendTo($body);
            $drag_line.appendTo($body);

            var stop_drag = function () {
                $ghost.remove();
                $drag_line.remove();
                $body.enableSelection().unbind('mousemove').unbind('mouseup');
                node.elem.removeAttribute('style');
            };

            // Create a clone create the illusion that we're moving the node
            var node = new Node($(this).closest('tr')[0]);
            cloned_node = node.clone();
            node.$elem.css({
                'background': ACTIVE_NODE_BG_COLOR
            });

            $targetRow = null;
            as_child = false;

            // Now make the new clone move with the mouse
            $body.disableSelection().bind('mousemove',function (evt2) {
                $ghost.html(cloned_node).css({  // from FeinCMS :P
                    'opacity': .8,
                    'position': 'absolute',
                    'top': evt2.pageY,
                    'left': evt2.pageX - 30,
                    'width': 600
                });
                // Iterate through all rows and see where am I moving so I can place
                // the drag line accordingly
                rowHeight = node.$elem.height();
                $('tr', node.$elem.parent()).each(function (index, element) {
                    $row = $(element);
                    rtop = $row.offset().top;
                    // The tooltop will display whether I'm droping the element as
                    // child or sibling
                    $tooltip = $drag_line.find('span');
                    $tooltip.css({
                        'left': node.$elem.width() - $tooltip.width(),
                        'height': rowHeight,
                    });
                    node_top = node.$elem.offset().top;
                    // Check if you are dragging over the same node
                    if (evt2.pageY >= node_top && evt2.pageY <= node_top + rowHeight) {
                        $targetRow = null;
                        $tooltip.text(gettext('Abort'));
                        $drag_line.css({
                            'top': node_top,
                            'height': rowHeight,
                            'borderWidth': 0,
                            'opacity': 0.8,
                            'backgroundColor': ABORT_COLOR
                        });
                    } else
                    // Check if mouse is over this row
                    if (evt2.pageY >= rtop && evt2.pageY <= rtop + rowHeight / 2) {
                        // The mouse is positioned on the top half of a $row
                        $targetRow = $row;
                        as_child = false;
                        $drag_line.css({
                            'left': node.$elem.offset().left,
                            'width': node.$elem.width(),
                            'top': rtop,
                            'borderWidth': '5px',
                            'height': 0,
                            'opacity': 1
                        });
                        $tooltip.text(gettext('As Sibling'));
                    } else if (evt2.pageY >= rtop + rowHeight / 2 && evt2.pageY <= rtop + rowHeight) {
                        // The mouse is positioned on the bottom half of a row
                        $targetRow = $row;
                        target_node = new Node($targetRow[0]);
                        if (target_node.is_collapsed()) {
                            target_node.expand();
                        }
                        as_child = true;
                        $drag_line.css({
                            'top': rtop,
                            'left': node.$elem.offset().left,
                            'height': rowHeight,
                            'opacity': 0.4,
                            'width': node.$elem.width(),
                            'borderWidth': 0,
                            'backgroundColor': DRAG_LINE_COLOR
                        });
                        $tooltip.text(gettext('As child'));
                    }
                });
            }).bind('mouseup',function () {
                    if ($targetRow !== null) {
                        target_node = new Node($targetRow[0]);
                        if (target_node.node_id !== node.node_id) {
                            /*alert('Insert node ' + node.node_name() + ' as child of: '
                             + target_node.parent_node().node_name() + '\n and sibling of: '
                             + target_node.node_name());*/
                            // Call $.ajax so we can handle the error
                            // On Drop, make an XHR call to perform the node move
                            $.ajax({
                                url: window.MOVE_NODE_ENDPOINT,
                                type: 'POST',
                                data: {
                                    node_id: node.node_id,
                                    parent_id: target_node.parent_id,
                                    sibling_id: target_node.node_id,
                                    as_child: as_child ? 1 : 0
                                },
                                complete: function (req, status) {
                                    // http://stackoverflow.com/questions/1439895/add-a-hash-with-javascript-to-url-without-scrolling-page/1439910#1439910
                                    node.$elem.remove();
                                    window.location.hash = 'node-' + node.node_id;
                                    window.location.reload();
                                },
                                error: function (req, status, error) {
                                    // On error (!200) also reload to display
                                    // the message
                                    node.$elem.remove();
                                    window.location.hash = 'node-' + node.node_id;
                                    window.location.reload();
                                }
                            });
                        }
                    }
                    stop_drag();
                }).bind('keyup', function (kbevt) {
                    // Cancel drag on escape
                    if (kbevt.keyCode === 27) {
                        stop_drag();
                    }
                });
        });

        $('a.collapse').click(function () {
            var node = new Node($(this).closest('tr')[0]); // send the DOM node, not jQ
            node.toggle();
            return false;
        });
        var hash = window.location.hash;
        // This is a hack, the actual element's id ends in '-id' but the url's hash
        // doesn't, I'm doing this to avoid scrolling the page... is that a good thing?
        if (hash) {
            $(hash + '-id').animate({
                backgroundColor: RECENTLY_MOVED_COLOR
            }, RECENTLY_FADE_DURATION, function () {
                $(this).animate({
                    backgroundColor: RECENTLY_MOVED_FADEOUT
                }, RECENTLY_FADE_DURATION, function () {
                    this.removeAttribute('style');
                });
            });
        }
    });
})(django.jQuery);

// http://stackoverflow.com/questions/190560/jquery-animate-backgroundcolor/2302005#2302005
(function (d) {
    d.each(["backgroundColor", "borderBottomColor", "borderLeftColor", "borderRightColor", "borderTopColor", "color", "outlineColor"], function (f, e) {
        d.fx.step[e] = function (g) {
            if (!g.colorInit) {
                g.start = c(g.elem, e);
                g.end = b(g.end);
                g.colorInit = true
            }
            g.elem.style[e] = "rgb(" + [Math.max(Math.min(parseInt((g.pos * (g.end[0] - g.start[0])) + g.start[0]), 255), 0), Math.max(Math.min(parseInt((g.pos * (g.end[1] - g.start[1])) + g.start[1]), 255), 0), Math.max(Math.min(parseInt((g.pos * (g.end[2] - g.start[2])) + g.start[2]), 255), 0)].join(",") + ")"
        }
    });
    function b(f) {
        var e;
        if (f && f.constructor == Array && f.length == 3) {
            return f
        }
        if (e = /rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(f)) {
            return[parseInt(e[1]), parseInt(e[2]), parseInt(e[3])]
        }
        if (e = /rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(f)) {
            return[parseFloat(e[1]) * 2.55, parseFloat(e[2]) * 2.55, parseFloat(e[3]) * 2.55]
        }
        if (e = /#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(f)) {
            return[parseInt(e[1], 16), parseInt(e[2], 16), parseInt(e[3], 16)]
        }
        if (e = /#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(f)) {
            return[parseInt(e[1] + e[1], 16), parseInt(e[2] + e[2], 16), parseInt(e[3] + e[3], 16)]
        }
        if (e = /rgba\(0, 0, 0, 0\)/.exec(f)) {
            return a.transparent
        }
        return a[d.trim(f).toLowerCase()]
    }

    function c(g, e) {
        var f;
        do {
            f = d.css(g, e);
            if (f != "" && f != "transparent" || d.nodeName(g, "body")) {
                break
            }
            e = "backgroundColor"
        } while (g = g.parentNode);
        return b(f)
    }

    var a = {aqua: [0, 255, 255], azure: [240, 255, 255], beige: [245, 245, 220], black: [0, 0, 0], blue: [0, 0, 255], brown: [165, 42, 42], cyan: [0, 255, 255], darkblue: [0, 0, 139], darkcyan: [0, 139, 139], darkgrey: [169, 169, 169], darkgreen: [0, 100, 0], darkkhaki: [189, 183, 107], darkmagenta: [139, 0, 139], darkolivegreen: [85, 107, 47], darkorange: [255, 140, 0], darkorchid: [153, 50, 204], darkred: [139, 0, 0], darksalmon: [233, 150, 122], darkviolet: [148, 0, 211], fuchsia: [255, 0, 255], gold: [255, 215, 0], green: [0, 128, 0], indigo: [75, 0, 130], khaki: [240, 230, 140], lightblue: [173, 216, 230], lightcyan: [224, 255, 255], lightgreen: [144, 238, 144], lightgrey: [211, 211, 211], lightpink: [255, 182, 193], lightyellow: [255, 255, 224], lime: [0, 255, 0], magenta: [255, 0, 255], maroon: [128, 0, 0], navy: [0, 0, 128], olive: [128, 128, 0], orange: [255, 165, 0], pink: [255, 192, 203], purple: [128, 0, 128], violet: [128, 0, 128], red: [255, 0, 0], silver: [192, 192, 192], white: [255, 255, 255], yellow: [255, 255, 0], transparent: [255, 255, 255]}
})(django.jQuery);
