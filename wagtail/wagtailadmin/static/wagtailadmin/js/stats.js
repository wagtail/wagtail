$(function(){
    'use strict';

    var uuid = function uuid() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
    };

    var $window = $(window);
    var endpointUrl = "https://ssl.google-analytics.com/collect";
    var payload = {
        // mandatory
        "v": 1, // protocol version
        "tid": "UA-112981-52", // tracking ID
        "t": "pageview", // hit type 
        "dp": "/dashboard", // page url
        "cid": uuid(), // unique client ID (server generated UUID)
        
        // standard
        "an": "Wagtail", // application version (used here to refer to Wagtail, not a mobile "app")
        "av": stats.wagtail_version, // application version (used here to refer to Wagtail, not a mobile "app")
        "sr": $window.width() + "x" + $window.height(), // screen resolution 
        "ua": navigator.userAgent, // user agent
        "dl": document.location.origin + document.location.pathname, // document location
        
        // custom
        "cd2": stats.django_version, // django version
        "cd4": stats.python_version, // python version
        "cd1": stats.db_engine //db engine
    }

    $.post(endpointUrl, payload);
});