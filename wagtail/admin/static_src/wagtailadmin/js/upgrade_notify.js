$(function() {
    'use strict';

    /*
    *   Expected JSON payload:
    *   {
    *       "version" : "1.2.3",    // Version number. Can only contain numbers and decimal point.
    *       "url" : "https://wagtail.io"  // Absolute URL to page/file containing release notes or actual package. It's up to you.
    *   }
    */

    function cmpVersion(a, b) {
        var i;
        var cmp;
        var len;
        var re = /(\.0)+[^\.]*$/;

        a = (a + '').replace(re, '').split('.');
        b = (b + '').replace(re, '').split('.');
        len = Math.min(a.length, b.length);
        for (i = 0; i < len; i++) {
            cmp = parseInt(a[i], 10) - parseInt(b[i], 10);
            if (cmp !== 0) {
                return cmp;
            }
        }

        return a.length - b.length;
    }

    function gtVersion(a, b) {
        return cmpVersion(a, b) > 0;
    }

    var releasesUrl = 'https://releases.wagtail.io/latest.txt';
    var currentVersion = window.wagtailVersion;

    $.getJSON(releasesUrl, function(data) {
        try {
            if (data.version && gtVersion(data.version, currentVersion)) {
                var $container = $('.panel-upgrade-notification')
                $('.newversion', $container).html(data.version);
                $('.releasenotes-link', $container).attr('href', data.url);
                $container.show();
            }
        } catch (e) {}
    });
});
