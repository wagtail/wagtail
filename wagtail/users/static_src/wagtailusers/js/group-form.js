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

    const toggleBoxes = document.querySelectorAll('.js-toggle-permission');

    toggleBoxes.forEach(node => {
        node.addEventListener('change', function() {
            const type = this.dataset.for;
            const boxes = document.querySelectorAll(`.${type}-column input[type="checkbox"]`);
            if(this.checked) {
                boxes.forEach(element => element.checked = true);
            } else {
                boxes.forEach(element => element.checked = false);
            }
        });
    });
});
