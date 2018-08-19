//HT START
function setupJcrop(image, original, focalPointOriginal, fields, container) {
    image.Jcrop({
        trueSize: [original.width, original.height],
        bgColor: 'rgb(192, 192, 192)',
        onSelect: function(box) {
            var x = Math.floor((box.x + box.x2) / 2);
            var y = Math.floor((box.y + box.y2) / 2);
            var w = Math.floor(box.w);
            var h = Math.floor(box.h);

            fields.x.val(x);
            fields.y.val(y);
            fields.width.val(w);
            fields.height.val(h);

        },

        onRelease: function() {
            fields.x.val(focalPointOriginal.x);
            fields.y.val(focalPointOriginal.y);
            fields.width.val(focalPointOriginal.width);
            fields.height.val(focalPointOriginal.height);
        }
    }, function() {
        container.data('jcropapi', this);
    });
}

function resetJcrop(container, image, params){
    let jcropapi = container.data("jcropapi");
    jcropapi.destroy();
    image.removeAttr('style');
    $('.jcrop-holder', container).remove();
    setupJcrop.apply(this, params)
}

function removeJcropSelection(container, image, fields, params){
    let jcropapi = container.data("jcropapi");
    if (jcropapi) {
        jcropapi.destroy();
        image.removeAttr('style');
        $('.jcrop-holder', container).remove();
        $('.current-focal-point-indicator', container).remove();
        fields.x.removeAttr('value');
        fields.y.removeAttr('value');
        fields.width.removeAttr('value');
        fields.height.removeAttr('value');
    }
    setupJcrop.apply(this, params);
}

window.runJcrop = function(focalPointChooser, reset) {
    console.log('running runJcrop');
    var $indicator = $('.current-focal-point-indicator', focalPointChooser);
    console.log('here is focalPointChooser:');
    console.log(focalPointChooser);
    var $image = $('img', focalPointChooser);
    console.log('here is image: ');
    console.log($image);
    let container = focalPointChooser.closest('.select-crop-image-block');//very important to ensure multiple jcrops on the page don't interfere with one another
    console.log('here is container');
    console.log(container);
    let fields = {
        x: $('input.focal_point_x', container),
        y: $('input.focal_point_y', container),
        width: $('input.focal_point_width', container),
        height: $('input.focal_point_height', container)
    }

    let original = {
        width: $image.attr('data-original-width'),//not using .data() here as it reads from a cache 
        height: $image.attr('data-original-height')
    }

    let focalPointOriginal = {
        x: fields.x[0].value,
        y: fields.y[0].value,
        width: fields.width[0].value,
        height: fields.height[0].value
    }

    let left = focalPointOriginal.x - focalPointOriginal.width / 2
    let top = focalPointOriginal.y - focalPointOriginal.height / 2
    let width = focalPointOriginal.width;
    let height = focalPointOriginal.height;

    let params = [$image, original, focalPointOriginal, fields, container];

    if (reset=="reset") {
        resetJcrop(container, $image, params);//more explicit and less brittle to pass $image and container outside params
    } else if (reset=="remove") {
        removeJcropSelection(container, $image, fields, params);
    } else {
        setupJcrop.apply(this, params); 
        //only necessary to apply this css when things haven't been reset
        $indicator.css('left', (left * 100 / original.width) + '%');
        $indicator.css('top', (top * 100 / original.height) + '%');
        $indicator.css('width', (width * 100 / original.width) + '%');
        $indicator.css('height', (height * 100 / original.height) + '%');
    }

    $(window).on('resize', $.debounce(300, function() {
        // jcrop doesn't support responsive images so to cater for resizing the browser
        // we have to destroy() it, which doesn't properly do it,
        // so destroy it some more, then re-apply it
        resetJcrop(container, $image, params)
    }));

    //$('.remove-focal-point', container).off();

    $('.remove-focal-point', container).on('click', function(event) {
        removeJcropSelection(container, $image, fields, params)
    });
};

function setupFocalPointChoosers(){
    let focalPointChoosers = $('.focal-point-chooser');
    focalPointChoosers.each(
        function(index){
            runJcrop($( this ))
        } 
    )
}

$(setupFocalPointChoosers);

//HT END