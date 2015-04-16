$(function(){
    'use strict';

    /* 
    *   Expected JSON payload:
    *   {
    *       'version' :'1.2.3'    // Version number excluding "v" etc. Must match /^(\d+\.)?(\d+\.)?(|\d+)$/ (xxx.xxx.xxx) mandatory to ensure version number comparison is possible
    *       'download_url' : ''   // Absolute URL to a page/file/archive at which to download the new version e.g PYPI or Github
    *       'release_notes' : ''  // Absolute URL to page/file containing release notes, readable in the browser.
    *   }
    *
    *
    */    

    function cmpVersion(a, b) {
        var i, cmp, len, re = /(\.0)+[^\.]*$/;
        a = (a + '').replace(re, '').split('.');
        b = (b + '').replace(re, '').split('.');
        len = Math.min(a.length, b.length);
        for( i = 0; i < len; i++ ) {
            cmp = parseInt(a[i], 10) - parseInt(b[i], 10);
            if( cmp !== 0 ) {
                return cmp;
            }
        }
        return a.length - b.length;
    }
    function gtVersion(a, b) {
        return cmpVersion(a, b) > 0;
    }

    var trackingUrl = "https://releases.wagtail.io/latest.txt";
    var currentVersion = window.wagtailVersion;

    // $.getJSON(trackingUrl, function(data) {
        var data = {}
        data.version = "1.0.1"
        if(data.version && gtVersion(data.version, currentVersion)){
            $('.panel.summary').after('<div class="panel nice-padding upgrade-available"><div class="help-block help-warning">Wagtail upgrade available. Your version: <strong>' + currentVersion + '</strong>, new version: <strong>' + data.version + '</strong>. <a href="' + data.release_notes + '">Read the release notes.</a></div></div>')
        }
    // });

});