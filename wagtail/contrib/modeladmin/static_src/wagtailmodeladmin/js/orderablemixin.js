$(function() {
    var order_header = $('th.column-index_order');
    var listing_tbody = $('.listing tbody');
    var listing_thead = $('.listing thead');
    var sorted_cols = listing_thead.find('th.sorted');
    order_header.find('a').addClass('text-replace icon-order').removeClass('icon-arrow-down-after icon-arrow-up-after');

    if(sorted_cols.length == 1 && order_header.hasClass('sorted') && order_header.hasClass('ascending')){
        order_header.find('a').attr('title', 'Restore default list ordering').attr('href', '?');
        listing_tbody.sortable({
            cursor: "move",
            tolerance: "pointer",
            containment: "parent",
            handle: ".handle",
            items: "> tr",
            axis: "y",
            placeholder: "dropzone",
            start: function(){
                $(this).parent().addClass('sorting');
            },
            stop: function(event, ui){
                $(this).parent().removeClass('sorting');

                // Work out what page moved and where it moved to
                var movedElement = $(ui.item[0]);
                var movedElementOrderTD = movedElement.find('td.field-index_order');
                var movedObjectId = movedElementOrderTD.data('obj-pk');
                var newPosition = $(movedElement).prevAll().length + 1;

                // Build url
                var url = "reorder/" + movedObjectId + "/?position=" + newPosition;
    
                // Post
                $.get(url, function(){
                    addMessage('success', '"' + movedElementOrderTD.data('obj-title') + '" has been moved successfully.')
                })

                listing_tbody.find('tr:nth-child(odd)').removeClass('even').addClass('odd');
                listing_tbody.find('tr:nth-child(even)').removeClass('odd').addClass('even');

            }
        });
        listing_tbody.disableSelection();
    } else {
        $('.field-index_order .handle').remove();
        order_header.find('a').attr('title', 'Enable ordering of objects').attr('href', '?o=0');
    }
});
