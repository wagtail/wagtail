$(function(){
    $.getJSON(window.versionUrl, function(data){
        var version = data.version;
        // pattern which matches git describe's output if on a dirty checkout
        var gitDescribePat = new RegExp(/([a-z0-9\.]*)\-([0-9]*)\-g([a-z0-9]*)/);
        
        if(gitDescribePat.test(version)){
            // if a dirty git checkout is found, link to it
            version = version.replace(gitDescribePat, '<a href="http://github.com/torchbox/wagtail/commit/$3">' + version + '</a>');
        }

        $('#version').show();
        $('#version-no').html(version);
    })
});
