$(function() {
    buildExpandingFormset('id_page_permissions', {
        onInit: function(index) {
            var deleteInputId = 'id_page_permissions-' + index + '-DELETE';
            var childId = 'inline_child_page_permissions-' + index;
            $('#' + deleteInputId + '-button').on('click', function() {
                /* set 'deleted' form field to true */
                $('#' + deleteInputId).val('1');
                $('#' + childId).fadeOut();
            });
        }
    });
});
